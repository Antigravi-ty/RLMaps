#!/usr/bin/env python3
"""
Forbidden Temple (Day) [禁忌神庙-日间] 全场景与核心球场自动化合成管线脚本
支持跨 4 个流式子关卡包 (CHN_Stadium_Day_P, CHN_Stadium_Day_Field, CHN_Stadium_Day_OOB, CHN_Stadium_Day_Mountains)
提取完整 Scenegraph 元数据、解析 UE3 通道遮罩材质参数 (DiffuseColor / Goldlief / EmissiveBrightness)，
并生成：
  1. ForbiddenTemple_Field.glb            - 核心球场带材质贴图模型
  2. ForbiddenTemple_Field_WhiteModel.glb - 核心球场白模
  3. ForbiddenTemple_Day.glb              - 完整日间全场景模型（含天空球、球场、长城、神庙建筑群、樱花树与远景群山）
  4. ForbiddenTemple_Day_WhiteModel.glb   - 完整日间全场景白模
"""

import os
import re
import json
import time
import numpy as np
from PIL import Image
import trimesh
import pygltflib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
RAW_FT_DIR = os.path.join(REPO_DIR, "raw", "Forbidden_Temple")
SCENE_DUMPS_DIR = os.path.join(REPO_DIR, "metadata", "scene_dumps")
SCENEGRAPH_PATH = os.path.join(REPO_DIR, "metadata", "forbidden_temple_day_scenegraph.json")
MAT_META_PATH = os.path.join(REPO_DIR, "metadata", "forbidden_temple_materials_metadata.json")
MODELS_DIR = os.path.join(REPO_DIR, "models")

os.makedirs(MODELS_DIR, exist_ok=True)

SUBLEVEL_PKGS = [
    "CHN_Stadium_Day_P",
    "CHN_Stadium_Day_Field",
    "CHN_Stadium_Day_OOB",
    "CHN_Stadium_Day_Mountains",
]

# 1. 索引全部可用 Mesh、Texture 与 Material 属性文件
mesh_paths = {}
all_textures = {}
mat_props_raw = {}
mat_files_raw = {}

for pkg in SUBLEVEL_PKGS:
    pdir = os.path.join(RAW_FT_DIR, pkg)
    sdir = os.path.join(pdir, "StaticMesh3")
    if os.path.isdir(sdir):
        for f in os.listdir(sdir):
            if f.endswith(".gltf"):
                mname = f[:-5]
                if mname not in mesh_paths:
                    mesh_paths[mname] = os.path.join(sdir, f)
    tdir = os.path.join(pdir, "Texture2D")
    if os.path.isdir(tdir):
        for f in os.listdir(tdir):
            if f.endswith(".png"):
                tname = f[:-4]
                if tname.lower() not in all_textures:
                    all_textures[tname.lower()] = os.path.join(tdir, f)
    for msub in ["Material3", "MaterialInstanceConstant"]:
        mdir = os.path.join(pdir, msub)
        if os.path.isdir(mdir):
            for f in os.listdir(mdir):
                if f.endswith(".props.txt"):
                    mname = f[:-10]
                    with open(os.path.join(mdir, f), "r") as fp:
                        mat_props_raw[mname] = fp.read()
                elif f.endswith(".mat"):
                    mname = f[:-4]
                    with open(os.path.join(mdir, f), "r") as fp:
                        mat_files_raw[mname] = fp.read()

# 2. 解析全部材质参数并输出 metadata/forbidden_temple_materials_metadata.json
materials_meta = {}
for mname, txt in sorted(mat_props_raw.items()):
    parent_m = re.search(r"Parent\s*=\s*\w+\x27([^\x27]+)\x27", txt)
    parent_name = parent_m.group(1).split(".")[-1] if parent_m else None
    two_sided = "TwoSided = true" in txt
    is_masked = "bIsMasked = true" in txt or "BLEND_Masked" in txt or (parent_name and "Masked" in parent_name)
    is_translucent = "BLEND_Translucent" in txt or "BLEND_Additive" in txt

    vec_params = {}
    for r, g, b, a, vname in re.findall(
        r"ParameterValue\s*=\s*\{\s*R=([0-9.eE+-]+),\s*G=([0-9.eE+-]+),\s*B=([0-9.eE+-]+),\s*A=([0-9.eE+-]+)\s*\}\s*\n\s*ParameterName\s*=\s*(\w+)",
        txt,
    ):
        vec_params[vname] = [float(r), float(g), float(b), float(a)]
    for r, g, b, a, vname in re.findall(
        r"Value\s*=\s*\{\s*R=([0-9.eE+-]+),\s*G=([0-9.eE+-]+),\s*B=([0-9.eE+-]+),\s*A=([0-9.eE+-]+)\s*\}\s*\n\s*Name\s*=\s*(\w+)",
        txt,
    ):
        if vname not in vec_params:
            vec_params[vname] = [float(r), float(g), float(b), float(a)]

    scalar_params = {}
    for val, sname in re.findall(
        r"ParameterValue\s*=\s*([0-9.eE+-]+)\s*\n\s*ParameterName\s*=\s*(\w+)",
        txt,
    ):
        scalar_params[sname] = float(val)

    tex_params = {}
    for tpath, tparam in re.findall(
        r"ParameterValue\s*=\s*Texture2D\x27([^\x27]+)\x27\s*\n\s*ParameterName\s*=\s*(\w+)",
        txt,
    ):
        tex_params[tparam] = tpath.split(".")[-1]

    ref_textures = [t.split(".")[-1] for t in re.findall(r"Texture2D\x27([^\x27]+)\x27", txt)]

    mat_kv = {}
    if mname in mat_files_raw:
        for line in mat_files_raw[mname].splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                mat_kv[k.strip()] = v.strip()

    materials_meta[mname] = {
        "parent": parent_name,
        "two_sided": two_sided,
        "is_masked": is_masked,
        "is_translucent": is_translucent,
        "texture_parameters": tex_params,
        "referenced_textures": ref_textures,
        "vector_parameters": vec_params,
        "scalar_parameters": scalar_params,
        "umodel_mat_bindings": mat_kv,
    }

with open(MAT_META_PATH, "w") as fp:
    json.dump(
        {"total_materials": len(materials_meta), "materials": materials_meta},
        fp,
        indent=2,
        ensure_ascii=False,
    )
print(f"已生成材质元数据: {MAT_META_PATH} ({len(materials_meta)} 个材质)")

# 3. 解析 4 个子关卡包并生成统一 Scenegraph JSON
instances = []
level_counts = {}

for pkg in SUBLEVEL_PKGS:
    dump_path = os.path.join(SCENE_DUMPS_DIR, f"{pkg}.upk_scene.json")
    with open(dump_path, "r") as fp:
        exports = json.load(fp)["exports"]
    by_idx = {e["index"] + 1: e for e in exports}
    pkg_inst_count = 0

    for e in exports:
        if "MeshComponent" not in e["class"]:
            continue
        props = e.get("properties", {})
        sm = props.get("StaticMesh") or props.get("SkeletalMesh")
        if not sm:
            continue
        mesh_name = sm["name"]
        outer = by_idx.get(e["outer_index"], {})
        outer_class = outer.get("class", "")
        outer_name = outer.get("name", "")
        outer_outer = str(outer.get("outer", ""))
        outer_props = outer.get("properties", {})

        # 过滤未放置的 FX 模板对象 (Pickup_Boost 下的默认模板，没有世界坐标)
        if outer_outer == "Pickup_Boost":
            continue
        # 过滤 InstancedStaticMeshComponent 自身嵌套的模板组件
        if outer_class == "InstancedStaticMeshComponent":
            continue

        hidden = bool(props.get("HiddenGame", False) or outer_props.get("bHidden", False))
        mats = [x["name"] for x in props.get("Materials", {}).get("elements", [])]

        inst_entry = {
            "sublevel_package": pkg,
            "component_name": e["name"],
            "class": e["class"],
            "mesh": mesh_name,
            "hidden": hidden,
            "max_draw_distance": props.get("MaxDrawDistance"),
            "actor": {
                "name": outer_name,
                "class": outer_class,
                "outer": outer_outer,
                "layer": outer_props.get("Layer"),
                "location": outer_props.get("Location"),
                "rotation": outer_props.get("Rotation"),
                "draw_scale": outer_props.get("DrawScale", 1.0),
                "draw_scale3d": outer_props.get("DrawScale3D"),
            },
            "component_transform": {
                "translation": props.get("Translation"),
                "rotation": props.get("Rotation"),
                "scale": props.get("Scale", 1.0),
                "scale3d": props.get("Scale3D"),
            },
            "materials": mats,
        }
        instances.append(inst_entry)
        pkg_inst_count += 1
    level_counts[pkg] = pkg_inst_count

sg_data = {
    "arena": "Forbidden Temple (Day)",
    "internal_code": "CHN_Stadium_Day",
    "sublevels": level_counts,
    "total_instances": len(instances),
    "instances": instances,
}
with open(SCENEGRAPH_PATH, "w") as fp:
    json.dump(sg_data, fp, indent=2, ensure_ascii=False)
print(f"已生成场景图元数据: {SCENEGRAPH_PATH} (共 {len(instances)} 个组件实例)")

# 4. 坐标系转换与变换矩阵工具
C = np.array([
    [0.01, 0.0,  0.0,  0.0],
    [0.0,  0.0,  0.01, 0.0],
    [0.0,  0.01, 0.0,  0.0],
    [0.0,  0.0,  0.0,  1.0],
])
C_inv = np.linalg.inv(C)

def rotator_to_matrix(pitch, yaw, roll):
    p = pitch * (2.0 * np.pi / 65536.0)
    y = yaw   * (2.0 * np.pi / 65536.0)
    r = roll  * (2.0 * np.pi / 65536.0)
    Rx = np.array([[1, 0, 0], [0, np.cos(r), -np.sin(r)], [0, np.sin(r), np.cos(r)]])
    Ry = np.array([[np.cos(p), 0, np.sin(p)], [0, 1, 0], [-np.sin(p), 0, np.cos(p)]])
    Rz = np.array([[np.cos(y), -np.sin(y), 0], [np.sin(y), np.cos(y), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def make_transform(loc=None, rot=None, scale=1.0, scale3d=None):
    M = np.eye(4)
    if rot:
        M[:3, :3] = rotator_to_matrix(rot.get("pitch", 0), rot.get("yaw", 0), rot.get("roll", 0))
    s = [scale if scale is not None else 1.0] * 3
    if scale3d:
        s[0] *= scale3d.get("x", 1.0)
        s[1] *= scale3d.get("y", 1.0)
        s[2] *= scale3d.get("z", 1.0)
    M[:3, :3] = M[:3, :3] @ np.diag(s)
    if loc:
        M[0, 3] = loc.get("x", 0.0)
        M[1, 3] = loc.get("y", 0.0)
        M[2, 3] = loc.get("z", 0.0)
    return M

img_cache = {}
def get_img(name, mode=None):
    if not name:
        return None
    k = (name.lower(), mode)
    if k in img_cache:
        return img_cache[k]
    path = all_textures.get(name.lower())
    if path and os.path.exists(path):
        im = Image.open(path)
        if mode:
            im = im.convert(mode)
        img_cache[k] = im
        return im
    return None

baked_tex_cache = {}

def bake_chn_master_texture(mat_name, meta):
    """
    针对 MAT_CHN_Stadium_Master / Blend / Masked 系列材质：
    将其通道遮罩贴图 (*_RGB / *_M) 与 DiffuseColor、Goldlief 向量参数烘焙为真实色彩贴图。
    """
    if mat_name in baked_tex_cache:
        return baked_tex_cache[mat_name]

    tparams = meta.get("texture_parameters", {})
    vparams = meta.get("vector_parameters", {})
    mask_tex_name = tparams.get("Mask")
    if not mask_tex_name and meta.get("referenced_textures"):
        for rt in meta["referenced_textures"]:
            if rt.endswith("_RGB") or rt.endswith("_M"):
                mask_tex_name = rt
                break

    im = get_img(mask_tex_name)
    if im is None:
        return None

    arr = np.array(im.convert("RGBA"), dtype=np.float32) / 255.0
    R = arr[:, :, 0]
    G = arr[:, :, 1]
    B = arr[:, :, 2]
    A = arr[:, :, 3]

    diff_col = np.array(vparams.get("DiffuseColor", [0.5, 0.5, 0.5, 1.0])[:3], dtype=np.float32)
    gold_col = np.array(vparams.get("Goldlief", diff_col.tolist())[:3], dtype=np.float32)

    # 线性空间转近似 sRGB 提亮，使 UE3 线性颜色在标准 glTF 查看器中明亮自然
    diff_srgb = np.clip(diff_col, 0.0, 1.0) ** 0.65
    gold_srgb = np.clip(gold_col, 0.0, 1.0) ** 0.65

    # 判断遮罩通道：若 R 通道几乎全为 0 且 B 通道有值，则使用 B 通道作为次色权重，否则使用 R 通道
    if R.mean() < 0.03 and B.mean() > 0.05:
        w = B
    else:
        w = R

    # G 通道为 AO / 漫反射明暗底图
    shade = np.clip(G * 1.25 + 0.1, 0.0, 1.35)[..., None]
    rgb = ((1.0 - w[..., None]) * diff_srgb[None, None, :] + w[..., None] * gold_srgb[None, None, :]) * shade
    rgb = np.clip(rgb, 0.0, 1.0)

    is_masked = meta.get("is_masked", False)
    if is_masked:
        # 对 CHN_GateSign_M / CHN_RL_Logo_M 这类无独立 Alpha 通道的贴图，使用 B 通道作为镂空遮罩
        raw_im = get_img(mask_tex_name)
        if raw_im.mode != "RGBA":
            alpha_ch = np.clip(B * 1.2, 0.0, 1.0)
        else:
            alpha_ch = A
        out_arr = np.dstack([rgb, alpha_ch])
        out_im = Image.fromarray((out_arr * 255.0).astype(np.uint8), mode="RGBA")
    else:
        out_im = Image.fromarray((rgb * 255.0).astype(np.uint8), mode="RGB")

    baked_tex_cache[mat_name] = out_im
    return out_im

def create_pbr(mat_name, mesh_name, with_textures=True):
    mn = mat_name if mat_name else ""
    mn_lower = mn.lower()
    meta = materials_meta.get(mn, {})
    parent = (meta.get("parent") or "").lower()

    # 透明防护能量网在白模和贴图模型中均保持半透明，以免遮挡球场内部结构
    if "beach_netfence" in mn_lower:
        if not with_textures:
            return trimesh.visual.material.PBRMaterial(
                name=mn or "NetFence_White",
                baseColorFactor=[0.8, 0.88, 0.95, 0.18],
                metallicFactor=0.1,
                roughnessFactor=0.3,
                alphaMode="BLEND",
                doubleSided=True,
            )
        hex_im = get_img("ForcefieldHex", mode="RGB")
        if hex_im is not None and "netfence_rgba" not in baked_tex_cache:
            h_arr = np.array(hex_im, dtype=np.float32) / 255.0
            lum = h_arr.mean(axis=2)
            rgba = np.zeros((h_arr.shape[0], h_arr.shape[1], 4), dtype=np.uint8)
            rgba[:, :, 0] = np.clip(lum * 180 + 50, 0, 255).astype(np.uint8)
            rgba[:, :, 1] = np.clip(lum * 220 + 35, 0, 255).astype(np.uint8)
            rgba[:, :, 2] = 255
            rgba[:, :, 3] = np.clip(lum * 160 + 28, 28, 190).astype(np.uint8)
            baked_tex_cache["netfence_rgba"] = Image.fromarray(rgba, mode="RGBA")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=baked_tex_cache.get("netfence_rgba"),
            baseColorFactor=[0.75, 0.9, 1.0, 0.32],
            metallicFactor=0.1,
            roughnessFactor=0.25,
            alphaMode="BLEND",
            doubleSided=True,
        )

    if not with_textures:
        return trimesh.visual.material.PBRMaterial(
            name=f"{mn}_White" if mn else "WhiteModel",
            baseColorFactor=[0.85, 0.85, 0.85, 1.0],
            metallicFactor=0.1,
            roughnessFactor=0.55,
        )

    # 1. 天空盒球体 (SM_SkySphere -> Beach_Clouds_01 4096x1024 全景贴图)
    if "beach_sky" in mn_lower or mesh_name == "SM_SkySphere":
        sky_im = get_img("Beach_Clouds_01", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn or "Beach_Sky_MAT_INST",
            baseColorTexture=sky_im,
            baseColorFactor=[1.0, 1.0, 1.0, 1.0],
            emissiveTexture=sky_im,
            emissiveFactor=[0.35, 0.35, 0.35],
            metallicFactor=0.0,
            roughnessFactor=1.0,
            doubleSided=True,
        )

    # 2. 球场草坪地面 (2048x2048 重建高清草坪与标线贴图)
    if "grass_day" in mn_lower or mesh_name in ("Grass_Base", "Grass_LOD"):
        pitch_im = get_img("CHN_FieldGrassPattern_Day_Reconstructed_2048", mode="RGB") or get_img("CHN_FieldGrassPattern_Day_D", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn or "Grass_Day_Base_MIC",
            baseColorTexture=pitch_im,
            baseColorFactor=[1.0, 1.0, 1.0, 1.0],
            metallicFactor=0.0,
            roughnessFactor=0.85,
        )

    # 3. 球场外围铁笼骨架 (CHN_FFCage_Full -> ForceField_HexGage_MIC)
    if "forcefield_hexgage" in mn_lower or mesh_name == "CHN_FFCage_Full":
        return trimesh.visual.material.PBRMaterial(
            name=mn or "ForceField_HexGage_MIC",
            baseColorFactor=[0.24, 0.19, 0.12, 1.0],
            metallicFactor=0.8,
            roughnessFactor=0.35,
        )

    # 4. 远景山体与山体植被 (OOB_Mountains_MAT_INST / MountainFoliage_MAT_INST)
    if "oob_mountains" in mn_lower or "mountainfoliage" in mn_lower:
        key = f"mountain_{mn_lower}"
        if key not in baked_tex_cache:
            rock_im = get_img("GodRock_00_D", mode="RGB")
            norm_im = get_img("MountainRock_01_", mode="RGBA")
            if rock_im is not None and norm_im is not None:
                r_arr = np.array(rock_im, dtype=np.float32) / 255.0
                n_arr = np.array(norm_im, dtype=np.float32) / 255.0
                moss_mask = np.clip((n_arr[:, :, 1] - 0.35) * 2.2, 0.0, 1.0)[..., None]
                if "foliage" in mn_lower:
                    moss_col = np.array([0.18, 0.38, 0.10], dtype=np.float32)[None, None, :]
                    comp = r_arr * 0.35 + moss_col * 0.65
                else:
                    moss_col = np.array([0.22, 0.36, 0.12], dtype=np.float32)[None, None, :]
                    comp = r_arr * (1.0 - 0.55 * moss_mask) + moss_col * (0.55 * moss_mask)
                baked_tex_cache[key] = Image.fromarray((np.clip(comp, 0.0, 1.0) * 255.0).astype(np.uint8), mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=baked_tex_cache.get(key),
            metallicFactor=0.05,
            roughnessFactor=0.85,
        )

    # 5. 樱花树叶与绿色灌木树叶 (CHN_Tree_MAT_INST / CHN_Tree02_MAT_INST)
    if "chn_tree" in mn_lower:
        key = f"tree_{mn_lower}"
        if key not in baked_tex_cache:
            leaf_im = get_img("Tree_Leaves", mode="RGBA")
            if leaf_im is not None:
                l_arr = np.array(leaf_im, dtype=np.float32) / 255.0
                shade = np.clip(l_arr[:, :, 0] * 3.5 + 0.35, 0.35, 1.2)[..., None]
                if "tree02" in mn_lower:
                    col = np.array([0.22, 0.48, 0.14], dtype=np.float32)[None, None, :]
                else:
                    col = np.array([0.98, 0.42, 0.55], dtype=np.float32)[None, None, :]
                rgb = np.clip(col * shade, 0.0, 1.0)
                alpha = np.where(l_arr[:, :, 3] > 0.08, 1.0, 0.0)[..., None]
                baked_tex_cache[key] = Image.fromarray((np.dstack([rgb, alpha]) * 255.0).astype(np.uint8), mode="RGBA")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=baked_tex_cache.get(key),
            metallicFactor=0.0,
            roughnessFactor=0.8,
            alphaMode="MASK",
            alphaCutoff=0.35,
            doubleSided=True,
        )

    # 6. 樱花花枝 (CHN_CherryBlossomBranch_Mat)
    if "cherryblossombranch" in mn_lower:
        im = get_img("CHN_CherryBlossom_FlowersBranch_D", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=im,
            metallicFactor=0.0,
            roughnessFactor=0.75,
            doubleSided=True,
        )

    # 7. MAT_CHN_Stadium_Master / Blend / Masked 派生材质
    if "mat_chn_stadium" in parent or "mic_field_centerpiece_stone" in parent:
        baked_im = bake_chn_master_texture(mn, meta)
        if baked_im is not None:
            is_gold = "gold" in mn_lower
            is_masked = meta.get("is_masked", False)
            return trimesh.visual.material.PBRMaterial(
                name=mn,
                baseColorTexture=baked_im,
                metallicFactor=0.65 if is_gold else 0.1,
                roughnessFactor=0.32 if is_gold else 0.68,
                alphaMode="MASK" if is_masked else "OPAQUE",
                alphaCutoff=0.33 if is_masked else None,
                doubleSided=is_masked or meta.get("two_sided", False),
            )

    # 8. 场地红木母材质 (CHN_Field_WoodParent_MAT / MIC_Field_Wood)
    if "woodparent" in mn_lower or "mic_field_wood" in mn_lower or "woodparent" in parent:
        im = get_img("Field_Redwood_D", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=im,
            metallicFactor=0.08,
            roughnessFactor=0.6,
        )

    # 9. 石阶材质 (Stairs_Mat -> Stairs_Pack 通道图烘焙为青石台阶色)
    if "stairs_mat" in mn_lower:
        if "stairs_baked" not in baked_tex_cache:
            st_im = get_img("Stairs_Pack", mode="RGB")
            if st_im is not None:
                s_arr = np.array(st_im, dtype=np.float32) / 255.0
                shade = s_arr[:, :, 1:2] * 1.15
                stone_col = np.array([0.58, 0.56, 0.50], dtype=np.float32)[None, None, :]
                baked_tex_cache["stairs_baked"] = Image.fromarray(
                    (np.clip(stone_col * shade, 0.0, 1.0) * 255.0).astype(np.uint8), mode="RGB"
                )
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=baked_tex_cache.get("stairs_baked"),
            metallicFactor=0.05,
            roughnessFactor=0.75,
        )

    # 10. 球场发光边带与灯笼高光 (TrimLight_Glow / Glow / BoostPad_Glow)
    if "trimlight_glow_team1" in mn_lower:
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorFactor=[0.2, 0.55, 1.0, 1.0],
            emissiveFactor=[0.2, 0.55, 1.0],
            metallicFactor=0.1,
            roughnessFactor=0.3,
        )
    if "trimlight_glow_team2" in mn_lower or mn_lower == "glow" or "boostpad_glow" in mn_lower:
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorFactor=[1.0, 0.72, 0.25, 1.0],
            emissiveFactor=[0.9, 0.6, 0.15],
            metallicFactor=0.1,
            roughnessFactor=0.3,
        )

    # 11. 深色金属与水泥材质
    if "darkmetal" in mn_lower:
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorFactor=[0.18, 0.18, 0.20, 1.0],
            metallicFactor=0.8,
            roughnessFactor=0.35,
        )
    if "concrete_mat" in mn_lower:
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorFactor=[0.55, 0.54, 0.52, 1.0],
            metallicFactor=0.05,
            roughnessFactor=0.8,
        )

    # 12. 通用材质纹理绑定查找
    tex_candidate = None
    mat_kv = meta.get("umodel_mat_bindings", {})
    if "Diffuse" in mat_kv:
        tex_candidate = mat_kv["Diffuse"]
    elif "Diffuse" in meta.get("texture_parameters", {}):
        tex_candidate = meta["texture_parameters"]["Diffuse"]
    elif meta.get("referenced_textures"):
        for rt in meta["referenced_textures"]:
            if not rt.endswith("_N") and not rt.endswith("_NORM"):
                tex_candidate = rt
                break

    im = get_img(tex_candidate, mode="RGBA" if meta.get("is_masked") else "RGB") if tex_candidate else None
    if im is not None:
        is_masked = meta.get("is_masked", False)
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=im,
            metallicFactor=0.1,
            roughnessFactor=0.65,
            alphaMode="MASK" if is_masked else "OPAQUE",
            alphaCutoff=0.33 if is_masked else None,
            doubleSided=is_masked or meta.get("two_sided", False),
        )

    return trimesh.visual.material.PBRMaterial(
        name=mn or "DefaultMaterial",
        baseColorFactor=[0.65, 0.63, 0.60, 1.0],
        metallicFactor=0.1,
        roughnessFactor=0.65,
    )

# 排除纯 2D 雾气卡片、光束体积锥体及距离 576cm 内才显示的 321 个碎草片（保持模型干净无遮挡）
EXCLUDED_VFX_MATERIALS = {
    "BeachFog_MAT",
    "CHN_TunnelFog_MAT",
    "CHN_OOB_Fire_Mat",
    "LightCone_Team1_MIC",
    "LightCone_Team2_MIC",
}
EXCLUDED_VFX_MESHES = {
    "Circle_Sprite",
    "LightCones_Team1_Combined",
    "LightCones_Team2_Combined",
    "Grass_LOD",
}

def build_scene(core_field_only=False, with_textures=True):
    scene = trimesh.Scene()
    inst_count = 0
    loaded_cache = {}

    for inst in sg_data["instances"]:
        if inst.get("hidden") is True:
            continue
        pkg = inst["sublevel_package"]
        mesh_name = inst["mesh"]
        mat_list = inst.get("materials", [])

        # 排除近景 3D 草叶碎块 (Grass_01..43, Grass_1x1) 及 VFX 辅助面片
        if mesh_name.startswith("Grass_") and mesh_name != "Grass_Base":
            continue
        if mesh_name in EXCLUDED_VFX_MESHES:
            continue
        if any(m in EXCLUDED_VFX_MATERIALS for m in mat_list):
            continue

        # 核心球场模式仅保留 CHN_Stadium_Day_Field 与 CHN_Stadium_Day_P 中的核心赛场组件（不含远景山体、OOB 建筑群和巨大天空球）
        if core_field_only:
            if pkg not in ("CHN_Stadium_Day_Field", "CHN_Stadium_Day_P"):
                continue
            if mesh_name in ("SM_SkySphere", "CHN_CastleBase_Room", "CHN_CastleBase_Room_Door", "CHN_OOB_Building01_CMB"):
                continue
        else:
            # 全场景白模中排除闭合的 SM_SkySphere 球壳，以便从外部直接观察群山与球场全貌
            if not with_textures and mesh_name == "SM_SkySphere":
                continue

        gltf_path = mesh_paths.get(mesh_name)
        if not gltf_path or not os.path.exists(gltf_path):
            continue

        cache_key = (mesh_name, tuple(mat_list), with_textures)
        if cache_key in loaded_cache:
            geoms = loaded_cache[cache_key]
        else:
            sub = trimesh.load(gltf_path)
            geoms = list(sub.geometry.values()) if isinstance(sub, trimesh.Scene) else [sub]
            for idx, geom in enumerate(geoms):
                mname = mat_list[idx] if idx < len(mat_list) else (mat_list[0] if mat_list else None)
                geom.visual.material = create_pbr(mname, mesh_name, with_textures=with_textures)
            loaded_cache[cache_key] = geoms

        c_tr = inst.get("component_transform", {})
        Mc = make_transform(
            c_tr.get("translation"),
            c_tr.get("rotation"),
            c_tr.get("scale", 1.0),
            c_tr.get("scale3d"),
        )
        act = inst.get("actor", {})
        Ma = make_transform(
            act.get("location"),
            act.get("rotation"),
            act.get("draw_scale", 1.0),
            act.get("draw_scale3d"),
        )
        M_ue = Ma @ Mc
        M_gltf = C @ M_ue @ C_inv

        for g_idx, geom in enumerate(geoms):
            node_name = f"{mesh_name}_{inst_count}_{g_idx}"
            scene.add_geometry(geom, node_name=node_name, transform=M_gltf)

        inst_count += 1

    return scene, inst_count

def main():
    tasks = [
        ("ForbiddenTemple_Field.glb", True, True, "核心球场完整带材质模型（含高清草坪、球门、石桥、龙凤浮雕、加速垫与半透能量罩）"),
        ("ForbiddenTemple_Field_WhiteModel.glb", True, False, "核心球场几何白模"),
        ("ForbiddenTemple_Day.glb", False, True, "禁忌神庙（日间）1:1 全场景带材质模型（含天空球、核心球场、长城、神庙建筑群、樱花树与远景群山）"),
        ("ForbiddenTemple_Day_WhiteModel.glb", False, False, "禁忌神庙（日间）1:1 全场景几何白模"),
    ]

    for out_name, core_only, with_tex, desc in tasks:
        print(f"\n[合成任务] {out_name} - {desc}")
        t0 = time.time()
        scene, count = build_scene(core_field_only=core_only, with_textures=with_tex)
        out_path = os.path.join(MODELS_DIR, out_name)
        scene.export(out_path, file_type="glb")
        size_mb = os.path.getsize(out_path) / (1024 * 1024)
        g = pygltflib.GLTF2().load(out_path)
        print(f"-> 完成: {out_name} ({size_mb:.2f} MB, {count} 个有效实例, {len(g.nodes)} 个节点, {len(g.images)} 张嵌入贴图, 耗时 {time.time()-t0:.2f}s)")

if __name__ == "__main__":
    main()
