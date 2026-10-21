#!/usr/bin/env python3
"""
Throwback Stadium (SARPBC 怀旧球场) & Throwback Hockey 全场景合成与 RocketSim 碰撞网格 (.cmf) 生成管线
"""
import os
import re
import json
import time
import struct
import shutil
import numpy as np
from PIL import Image
import trimesh
import pygltflib

OUT_DIR = "/tmp/work/branch_throwback"
if os.path.exists(OUT_DIR):
    shutil.rmtree(OUT_DIR)

for sub in [
    "models",
    "collision_meshes/throwback_stadium",
    "collision_meshes/throwback_hockey",
    "skyboxes_and_textures/01_Skyboxes_and_Cubemaps",
    "skyboxes_and_textures/02_Ground_and_Ice_Textures",
    "skyboxes_and_textures/03_MapImages_UI_Previews",
    "skyboxes_and_textures/04_Banners_Flags_and_Props",
    "raw/Throwback_Stadium",
    "raw/Throwback_Hockey",
    "metadata/scene_dumps",
    "tools",
]:
    os.makedirs(os.path.join(OUT_DIR, sub), exist_ok=True)

STADIUM_PKGS = ["ThrowbackStadium_P", "ThrowbackStadium_Field", "ThrowbackStadium_OOB", "throwbackstadium_p_MapImage_SF"]
HOCKEY_PKGS = ["ThrowbackHockey_P", "ThrowbackHockey_Field", "ThrowbackHockey_OOB", "throwbackhockey_p_MapImage_SF"]
ALL_PKGS = STADIUM_PKGS + HOCKEY_PKGS

# 1. 复制原始导出资产与 Scene Dumps
for pkg in STADIUM_PKGS:
    src = f"/tmp/work/exports_skybox33/{pkg}/{pkg}"
    if os.path.isdir(src):
        shutil.copytree(src, os.path.join(OUT_DIR, "raw", "Throwback_Stadium", pkg))
    dump_src = f"/tmp/work/dumps_skybox33/{pkg}.upk_scene.json"
    if os.path.isfile(dump_src):
        shutil.copy2(dump_src, os.path.join(OUT_DIR, "metadata", "scene_dumps", f"{pkg}.upk_scene.json"))

for pkg in HOCKEY_PKGS:
    src = f"/tmp/work/exports_skybox33/{pkg}/{pkg}"
    if os.path.isdir(src):
        shutil.copytree(src, os.path.join(OUT_DIR, "raw", "Throwback_Hockey", pkg))
    dump_src = f"/tmp/work/dumps_skybox33/{pkg}.upk_scene.json"
    if os.path.isfile(dump_src):
        shutil.copy2(dump_src, os.path.join(OUT_DIR, "metadata", "scene_dumps", f"{pkg}.upk_scene.json"))

# 2. 索引全部 Mesh、Texture、Material
mesh_paths = {}
all_textures = {}
mat_props_raw = {}
mat_files_raw = {}

for pkg in ALL_PKGS:
    pdir = f"/tmp/work/exports_skybox33/{pkg}/{pkg}"
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

# 用 ShatterShot_VFX 的 SM_SkySphere 作为 SkySphere01 的几何体
if "SkySphere01" not in mesh_paths and os.path.exists("/tmp/work/exports_skybox33/ShatterShot_VFX/ShatterShot_VFX/StaticMesh3/SM_SkySphere.gltf"):
    mesh_paths["SkySphere01"] = "/tmp/work/exports_skybox33/ShatterShot_VFX/ShatterShot_VFX/StaticMesh3/SM_SkySphere.gltf"

# 3. 重建 2048x2048 怀旧球场高清草坪与标线贴图 + 2048x1024 天空盒全景图
print("正在生成 2048x2048 怀旧球场草坪标线贴图与 2048x1024 天空盒贴图...")
uf_path = all_textures["fieldpattern_longfield_unfiltered"]
lm_path = all_textures["floorlightmap"]
uf_im = Image.open(uf_path).convert("RGBA")
lm_im = Image.open(lm_path).convert("RGB").resize(uf_im.size, Image.Resampling.BICUBIC)

uf_arr = np.array(uf_im, dtype=np.float32) / 255.0
lm_arr = np.array(lm_im, dtype=np.float32) / 255.0

grass_rgb = uf_arr[:, :, :3]
# 提亮草坪绿意并叠加柔和的球场光照
grass_boost = np.array([1.25, 1.48, 1.10], dtype=np.float32)[None, None, :]
light_tint = (lm_arr * 0.45 + 0.78)
grass_lit = np.clip(grass_rgb * grass_boost * light_tint, 0.0, 1.0)

# Alpha 通道为高清球场白线与中圈标线遮罩 (A 范围 0..98)
line_mask = np.clip(uf_arr[:, :, 3] / 90.0, 0.0, 1.0)[..., None]
line_col = np.array([0.95, 0.97, 0.95], dtype=np.float32)[None, None, :]
pitch_final = np.clip(grass_lit * (1.0 - 0.88 * line_mask) + line_col * (0.88 * line_mask), 0.0, 1.0)
pitch_im = Image.fromarray((pitch_final * 255.0).astype(np.uint8), mode="RGB")

reconstructed_pitch_path = os.path.join(OUT_DIR, "skyboxes_and_textures/02_Ground_and_Ice_Textures/FieldPattern_LongField_Reconstructed_2048.png")
pitch_im.save(reconstructed_pitch_path)
all_textures["fieldpattern_longfield_reconstructed_2048"] = reconstructed_pitch_path

# 生成 2048x1024 晴空万里云层全景贴图 (结合 ENV_PartlyCloudy 与 Curve_StadiumFog)
W, H = 2048, 1024
y_lin = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
# 天顶蔚蓝 -> 地平线浅暖青蓝渐变
zenith = np.array([0.16, 0.42, 0.78], dtype=np.float32)[None, None, :]
horizon = np.array([0.68, 0.82, 0.95], dtype=np.float32)[None, None, :]
ground_haze = np.array([0.55, 0.65, 0.72], dtype=np.float32)[None, None, :]
t_sky = np.clip(y_lin * 1.8, 0.0, 1.0)[..., None]
sky_bg = zenith * (1.0 - t_sky ** 0.7) + horizon * (t_sky ** 0.7)
t_low = np.clip((y_lin - 0.55) * 2.2, 0.0, 1.0)[..., None]
sky_bg = sky_bg * (1.0 - t_low) + ground_haze * t_low
sky_canvas = np.repeat(sky_bg, W, axis=1)

cloud_path = all_textures.get("env_partlycloudy")
if cloud_path:
    cl_im = Image.open(cloud_path).convert("RGBA").resize((512, 512), Image.Resampling.BICUBIC)
    cl_tile = np.tile(np.array(cl_im, dtype=np.float32) / 255.0, (2, 4, 1))
    cloud_weight = np.clip(cl_tile[:, :, 0] * (1.0 - np.abs(y_lin - 0.35) * 2.4), 0.0, 1.0)[..., None]
    sky_canvas = np.clip(sky_canvas * (1.0 - 0.45 * cloud_weight) + 0.98 * (0.45 * cloud_weight), 0.0, 1.0)

sky_im = Image.fromarray((sky_canvas * 255.0).astype(np.uint8), mode="RGB")
reconstructed_sky_path = os.path.join(OUT_DIR, "skyboxes_and_textures/01_Skyboxes_and_Cubemaps/Throwback_SkyDome_Reconstructed_2048x1024.png")
sky_im.save(reconstructed_sky_path)
all_textures["throwback_skydome_reconstructed"] = reconstructed_sky_path

# 4. 整理分类贴图至 skyboxes_and_textures/
for tname in ["ENV_PartlyCloudy", "Curve_StadiumFog", "Corona_Sun01_D", "CubemapFace0", "CubemapFace1", "CubemapFace2", "CubemapFace3", "CubemapFace4", "CubemapFace5"]:
    p = all_textures.get(tname.lower())
    if p:
        shutil.copy2(p, os.path.join(OUT_DIR, "skyboxes_and_textures/01_Skyboxes_and_Cubemaps", os.path.basename(p)))

for tname in ["FieldPattern_LongField_Unfiltered", "FieldPattern_LongField", "FloorLightMap", "CS_FieldGrassPattern_D", "Grass_Strip", "Ice_01_D", "Ice_01_N", "RockyDirt_D", "RockyDirt_N", "GrassAndBush_D", "RiverStrip_D"]:
    p = all_textures.get(tname.lower())
    if p:
        shutil.copy2(p, os.path.join(OUT_DIR, "skyboxes_and_textures/02_Ground_and_Ice_Textures", os.path.basename(p)))

for mpkg, out_n in [("throwbackstadium_p_MapImage_SF", "throwbackstadium_p__MapImage.png"), ("throwbackhockey_p_MapImage_SF", "throwbackhockey_p__MapImage.png")]:
    mp = f"/tmp/work/exports_skybox33/{mpkg}/{mpkg}/Texture2D/MapImage.png"
    if os.path.exists(mp):
        shutil.copy2(mp, os.path.join(OUT_DIR, "skyboxes_and_textures/03_MapImages_UI_Previews", out_n))

for tname in ["CountryFlagsCombined", "Logo_RocketLeague", "RocketLeagueAd_2x1_Dark", "RocketLeagueAd_Dark", "Flag_10yr", "Advert_Strip", "Park_BannerFlag00_RGB", "Park_BannerScaffold_D", "TILE_Labs_Trim00_RGB", "LightArray_Arrow_D", "BoostPad_Large_D", "BoostPad_Small_D", "ForcefieldHex", "Hills_A_Color", "Mountain_B_Color"]:
    p = all_textures.get(tname.lower())
    if p:
        shutil.copy2(p, os.path.join(OUT_DIR, "skyboxes_and_textures/04_Banners_Flags_and_Props", os.path.basename(p)))

# 5. 解析材质元数据
materials_meta = {}
for mname, txt in sorted(mat_props_raw.items()):
    parent_m = re.search(r"Parent\s*=\s*\w+\x27([^\x27]+)\x27", txt)
    parent_name = parent_m.group(1).split(".")[-1] if parent_m else None
    two_sided = "TwoSided = true" in txt
    is_masked = "bIsMasked = true" in txt or "BLEND_Masked" in txt
    is_translucent = "BLEND_Translucent" in txt or "BLEND_Additive" in txt

    vec_params = {}
    for r, g, b, a, vname in re.findall(
        r"ParameterValue\s*=\s*\{\s*R=([0-9.eE+-]+),\s*G=([0-9.eE+-]+),\s*B=([0-9.eE+-]+),\s*A=([0-9.eE+-]+)\s*\}\s*\n\s*ParameterName\s*=\s*(\w+)",
        txt,
    ):
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

with open(os.path.join(OUT_DIR, "metadata/throwback_stadium_materials_metadata.json"), "w") as fp:
    json.dump({"total_materials": len(materials_meta), "materials": materials_meta}, fp, indent=2, ensure_ascii=False)

# 6. 提取 ThrowbackStadium 精确物理配置 (GoalVolume 3D AABB, 44 BoostPads, 9 PlayerStarts)
with open("/tmp/work/dumps_skybox33/ThrowbackStadium_P.upk_scene.json") as fp:
    tb_p_exports = json.load(fp)["exports"]
tb_by_idx = {e["index"] + 1: e for e in tb_p_exports}

goal_volumes = []
boost_pads = []
player_starts = []

for e in tb_p_exports:
    cls = e["class"]
    props = e.get("properties", {})
    if cls == "GoalVolume_TA":
        b_idx = props.get("Brush", {}).get("index", 0)
        b_obj = tb_by_idx.get(b_idx, {})
        goal_volumes.append({
            "name": e["name"],
            "team_num": props.get("TeamNum", 0),
            "location": props.get("Location"),
            "world_aabb_uu": b_obj.get("properties", {}).get("_ModelBounds"),
        })
    elif cls.startswith("VehiclePickup_Boost"):
        is_big = "Pill" in cls or "Pill" in str(e.get("archetype", ""))
        boost_pads.append({
            "name": e["name"],
            "class": cls,
            "archetype": e.get("archetype"),
            "is_big": is_big,
            "location_uu": props.get("Location"),
            "rotation": props.get("Rotation"),
        })
    elif "PlayerStart" in cls:
        player_starts.append({
            "name": e["name"],
            "class": cls,
            "team_index": props.get("TeamIndex", 0),
            "location_uu": props.get("Location"),
            "rotation": props.get("Rotation"),
        })

physics_cfg = {
    "arena": "Throwback Stadium (SARPBC Retro LongField)",
    "package": "ThrowbackStadium_P.upk",
    "arena_bounds_uu": {
        "x_min": -4096.0, "x_max": 4096.0,
        "y_min": -6912.0, "y_max": 6912.0,
        "z_min": 0.0,     "z_max": 2048.0,
    },
    "goal_volumes": goal_volumes,
    "boost_pads_summary": {
        "total": len(boost_pads),
        "big_pills": sum(1 for b in boost_pads if b["is_big"]),
        "small_pads": sum(1 for b in boost_pads if not b["is_big"]),
    },
    "boost_pads": boost_pads,
    "player_starts": player_starts,
}
with open(os.path.join(OUT_DIR, "metadata/throwback_stadium_physics_config.json"), "w") as fp:
    json.dump(physics_cfg, fp, indent=2, ensure_ascii=False)

# 7. 构建 SceneGraph JSON 函数
def build_scenegraph(pkgs, arena_title, internal_code, out_json):
    instances = []
    level_counts = {}
    for pkg in pkgs:
        dump_path = f"/tmp/work/dumps_skybox33/{pkg}.upk_scene.json"
        if not os.path.exists(dump_path):
            continue
        with open(dump_path, "r") as fp:
            exports = json.load(fp)["exports"]
        by_idx = {e["index"] + 1: e for e in exports}
        pkg_cnt = 0
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
            if outer_outer == "Pickup_Boost" or outer_class == "InstancedStaticMeshComponent":
                continue
            hidden = bool(props.get("HiddenGame", False) or outer_props.get("bHidden", False))
            mats = [x["name"] for x in props.get("Materials", {}).get("elements", [])]
            instances.append({
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
            })
            pkg_cnt += 1
        level_counts[pkg] = pkg_cnt
    sg = {
        "arena": arena_title,
        "internal_code": internal_code,
        "sublevels": level_counts,
        "total_instances": len(instances),
        "instances": instances,
    }
    with open(out_json, "w") as fp:
        json.dump(sg, fp, indent=2, ensure_ascii=False)
    return sg

sg_stadium = build_scenegraph(
    ["ThrowbackStadium_P", "ThrowbackStadium_Field", "ThrowbackStadium_OOB"],
    "Throwback Stadium (SARPBC)",
    "ThrowbackStadium",
    os.path.join(OUT_DIR, "metadata/throwback_stadium_scenegraph.json"),
)
sg_hockey = build_scenegraph(
    ["ThrowbackHockey_P", "ThrowbackHockey_Field", "ThrowbackHockey_OOB"],
    "Throwback Stadium (Snow Day / Hockey)",
    "ThrowbackHockey",
    os.path.join(OUT_DIR, "metadata/throwback_hockey_scenegraph.json"),
)

# 8. 矩阵工具与 RocketSim .cmf 碰撞网格生成
C = np.array([
    [0.01, 0.0,  0.0,  0.0],
    [0.0,  0.0,  0.01, 0.0],
    [0.0,  0.01, 0.0,  0.0],
    [0.0,  0.0,  0.0,  1.0],
])
C_inv = np.linalg.inv(C)

# Bullet 物理坐标变换: 1 BT = 50 UU (即 UU * 0.02)
C_bt = np.array([
    [0.02, 0.0,  0.0,  0.0],
    [0.0,  0.02, 0.0,  0.0],
    [0.0,  0.0,  0.02, 0.0],
    [0.0,  0.0,  0.0,  1.0],
])

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

def write_cmf(filepath, tris_int32, verts_float32):
    num_tris = len(tris_int32)
    num_verts = len(verts_float32)
    with open(filepath, "wb") as fp:
        fp.write(struct.pack("<ii", num_tris, num_verts))
        fp.write(tris_int32.astype("<i4").tobytes())
        fp.write(verts_float32.astype("<f4").tobytes())

def export_arena_cmf_set(sg, out_cmf_dir, export_coll_glb_path=None):
    manifest = []
    coll_scene = trimesh.Scene()
    idx = 0
    for inst in sg["instances"]:
        mesh_name = inst["mesh"]
        mats = inst.get("materials", [])
        # 只导出场地与球门物理碰撞网格 (Collision_Mat: Field_TB_Collision_*, LF_GoalCollision*, LongField_Collision, Plane32768)
        if not ("Collision" in mesh_name or "Plane32768" in mesh_name):
            continue
        gltf_path = mesh_paths.get(mesh_name)
        if not gltf_path or not os.path.exists(gltf_path):
            continue

        c_tr = inst.get("component_transform", {})
        Mc = make_transform(c_tr.get("translation"), c_tr.get("rotation"), c_tr.get("scale", 1.0), c_tr.get("scale3d"))
        act = inst.get("actor", {})
        Ma = make_transform(act.get("location"), act.get("rotation"), act.get("draw_scale", 1.0), act.get("draw_scale3d"))
        M_ue = Ma @ Mc

        raw_m = trimesh.load(gltf_path, force="mesh")
        # 转换到 Bullet 世界坐标系 (1 BT = 50 UU)
        M_total_bt = C_bt @ M_ue @ C_inv
        verts_h = np.hstack([raw_m.vertices, np.ones((len(raw_m.vertices), 1))])
        verts_bt = (verts_h @ M_total_bt.T)[:, :3].astype(np.float32)

        faces = raw_m.faces.copy()
        if np.linalg.det(M_total_bt[:3, :3]) < 0:
            faces = faces[:, [0, 2, 1]]

        # 合并重复顶点 (与 RLArenaCollisionDumper 保持一致)
        rounded = np.round(verts_bt, 5)
        _, unique_indices, inv = np.unique(rounded, axis=0, return_index=True, return_inverse=True)
        dedup_verts = verts_bt[unique_indices]
        dedup_faces = inv[faces].astype(np.int32)

        cmf_name = f"mesh_{idx}.cmf"
        write_cmf(os.path.join(out_cmf_dir, cmf_name), dedup_faces, dedup_verts)
        manifest.append(cmf_name)

        if export_coll_glb_path:
            M_gltf = C @ M_ue @ C_inv
            vis_m = raw_m.copy()
            if "Goal" in mesh_name:
                col = [1.0, 0.45, 0.15, 0.65]
            elif "Plane32768" in mesh_name:
                col = [0.25, 0.65, 1.0, 0.22]
            else:
                col = [0.2, 0.85, 0.45, 0.55]
            vis_m.visual.material = trimesh.visual.material.PBRMaterial(
                name=f"Coll_{mesh_name}",
                baseColorFactor=col,
                metallicFactor=0.1,
                roughnessFactor=0.5,
                alphaMode="BLEND",
                doubleSided=True,
            )
            coll_scene.add_geometry(vis_m, node_name=f"{mesh_name}_{idx}", transform=M_gltf)

        idx += 1

    with open(os.path.join(out_cmf_dir, "manifest.json"), "w") as fp:
        json.dump(manifest, fp, indent=2)
    if export_coll_glb_path:
        coll_scene.export(export_coll_glb_path, file_type="glb")
    return len(manifest)

n_tb_cmf = export_arena_cmf_set(
    sg_stadium,
    os.path.join(OUT_DIR, "collision_meshes/throwback_stadium"),
    os.path.join(OUT_DIR, "models/ThrowbackStadium_Collision.glb"),
)
n_hk_cmf = export_arena_cmf_set(
    sg_hockey,
    os.path.join(OUT_DIR, "collision_meshes/throwback_hockey"),
)
print(f"已生成 RocketSim .cmf 碰撞网格: ThrowbackStadium={n_tb_cmf} 个, ThrowbackHockey={n_hk_cmf} 个")

# 9. PBR 材质构建与 GLB 场景合成
img_cache = {}
def get_img(name, mode=None):
    if not name:
        return None
    k = (name.lower(), mode)
    if k in img_cache:
        return img_cache[k]
    p = all_textures.get(name.lower())
    if p and os.path.exists(p):
        im = Image.open(p)
        if mode:
            im = im.convert(mode)
        img_cache[k] = im
        return im
    return None

baked_cache = {}

def create_pbr(mat_name, mesh_name, with_textures=True, is_hockey=False):
    mn = mat_name if mat_name else ""
    mn_lower = mn.lower()
    meta = materials_meta.get(mn, {})

    # 透明力场墙与球门玻璃在白模和贴图模型中均保持半透明
    if any(k in mn_lower for k in ["forcefield_mat", "hexglass", "glasswithtrim", "buildingglass"]):
        if not with_textures:
            return trimesh.visual.material.PBRMaterial(
                name=mn or "Glass_White",
                baseColorFactor=[0.8, 0.88, 0.96, 0.18],
                metallicFactor=0.1,
                roughnessFactor=0.25,
                alphaMode="BLEND",
                doubleSided=True,
            )
        if "team1" in mn_lower:
            col = [0.22, 0.58, 1.0, 0.28]
        elif "team2" in mn_lower:
            col = [1.0, 0.52, 0.16, 0.28]
        else:
            col = [0.75, 0.88, 1.0, 0.20]
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorFactor=col,
            metallicFactor=0.15,
            roughnessFactor=0.2,
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

    # 1. 天空盒天穹 (SkySphere01 -> Throwback_SkyDome_Reconstructed)
    if "skydome" in mn_lower or mesh_name == "SkySphere01":
        sky = get_img("throwback_skydome_reconstructed", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn or "SkyDome_MAT",
            baseColorTexture=sky,
            emissiveTexture=sky,
            emissiveFactor=[0.35, 0.35, 0.35],
            metallicFactor=0.0,
            roughnessFactor=1.0,
            doubleSided=True,
        )

    # 2. 球场草坪或冰面 (Grass_Plane)
    if mesh_name == "Grass_Plane" or "longfield_grass" in mn_lower or "ice_mat" in mn_lower:
        if is_hockey or "ice_mat" in mn_lower:
            ice_im = get_img("Ice_01_D", mode="RGB")
            return trimesh.visual.material.PBRMaterial(
                name=mn or "Ice_Mat",
                baseColorTexture=ice_im,
                baseColorFactor=[0.85, 0.94, 1.0, 1.0],
                metallicFactor=0.08,
                roughnessFactor=0.22,
            )
        pitch = get_img("fieldpattern_longfield_reconstructed_2048", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn or "LongField_Grass_Base_MIC",
            baseColorTexture=pitch,
            metallicFactor=0.0,
            roughnessFactor=0.82,
        )

    # 3. 球门与边墙发光灯带 (TrimLight_Glow_Team1/Team2)
    if "trimlight_glow_team1" in mn_lower:
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorFactor=[0.18, 0.55, 1.0, 1.0],
            emissiveFactor=[0.25, 0.65, 1.0],
            metallicFactor=0.1,
            roughnessFactor=0.3,
        )
    if "trimlight_glow_team2" in mn_lower:
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorFactor=[1.0, 0.52, 0.12, 1.0],
            emissiveFactor=[1.0, 0.55, 0.12],
            metallicFactor=0.1,
            roughnessFactor=0.3,
        )

    # 4. 场边广告牌与横幅 (4x1_A..D_MIC, 2x1_A..B_MIC, Advert_Strip*, Tifo_All_MIC)
    if any(k in mn_lower for k in ["4x1_", "2x1_", "tifo"]):
        ad_im = get_img("RocketLeagueAd_2x1_Dark", mode="RGB") or get_img("Logo_RocketLeague", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=ad_im,
            metallicFactor=0.1,
            roughnessFactor=0.45,
            doubleSided=True,
        )
    if "advert_strip" in mn_lower:
        ad_im = get_img("RocketLeagueAd_Dark", mode="RGB") or get_img("Advert_Strip", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=ad_im,
            metallicFactor=0.1,
            roughnessFactor=0.45,
        )

    # 5. 国旗与十周年旗帜
    if "countryflags" in mn_lower:
        fl_im = get_img("CountryFlagsCombined", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=fl_im,
            metallicFactor=0.0,
            roughnessFactor=0.7,
            doubleSided=True,
        )
    if "10yr_flag" in mn_lower or "park_bannerflag" in mn_lower:
        fl_im = get_img("Flag_10yr", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=fl_im,
            baseColorFactor=[1.0, 0.65, 0.15, 1.0],
            metallicFactor=0.05,
            roughnessFactor=0.65,
            doubleSided=True,
        )

    # 6. 加速垫 (BoostPad_Large / Small)
    if "boostpad_large" in mn_lower:
        im = get_img("BoostPad_Large_D", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=im,
            baseColorFactor=[1.0, 0.78, 0.22, 1.0],
            emissiveFactor=[0.45, 0.32, 0.05],
            metallicFactor=0.35,
            roughnessFactor=0.4,
        )
    if "boostpad_small" in mn_lower or "boostpad_02" in mn_lower or "boostpad_mat" in mn_lower:
        im = get_img("BoostPad_Small_D", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=im,
            baseColorFactor=[0.95, 0.72, 0.25, 1.0],
            emissiveFactor=[0.3, 0.2, 0.05],
            metallicFactor=0.35,
            roughnessFactor=0.45,
        )

    # 7. 铁笼框架与深色金属结构 (Frame_01_V2_Mat, ForceField_HexGage_MIC, DarkMetal_*)
    if any(k in mn_lower for k in ["frame_01", "forcefield_hexgage", "darkmetal", "handrail", "metaltexture"]):
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorFactor=[0.22, 0.24, 0.27, 1.0],
            metallicFactor=0.78,
            roughnessFactor=0.36,
        )
    if "retro_stadium_goaltrim" in mn_lower:
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorFactor=[0.78, 0.80, 0.84, 1.0],
            metallicFactor=0.65,
            roughnessFactor=0.32,
        )

    # 8. 看台水泥、红砖与台阶 (Concrete*, RedBricks_Mat, Stairs_Mat, SeatBase_Mat)
    if "redbricks" in mn_lower:
        im = get_img("Station_BrickRed00_D2", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=im,
            baseColorFactor=[0.72, 0.32, 0.26, 1.0],
            metallicFactor=0.05,
            roughnessFactor=0.82,
        )
    if "concrete" in mn_lower or "stairs_mat" in mn_lower or "seatbase" in mn_lower:
        im = get_img("ConcreteWall_D", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=im,
            baseColorFactor=[0.62, 0.63, 0.65, 1.0],
            metallicFactor=0.05,
            roughnessFactor=0.78,
        )

    # 9. 远山、丘陵与地形草地 (Mountain_Mat, Hills_A_MIC, GrassAndBush_Mat, RiverStrip_Mat)
    if "mountain_mat" in mn_lower:
        im = get_img("Mountain_B_Color", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=im,
            baseColorFactor=[0.52, 0.58, 0.66, 1.0],
            metallicFactor=0.05,
            roughnessFactor=0.88,
        )
    if "hills_a" in mn_lower:
        im = get_img("Hills_A_Color", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=im,
            baseColorFactor=[0.36, 0.55, 0.30, 1.0],
            metallicFactor=0.0,
            roughnessFactor=0.88,
        )
    if "grassandbush" in mn_lower:
        im = get_img("GrassAndBush_D", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=im,
            baseColorFactor=[0.32, 0.52, 0.26, 1.0],
            metallicFactor=0.0,
            roughnessFactor=0.88,
        )
    if "riverstrip" in mn_lower:
        im = get_img("RiverStrip_D", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=im,
            baseColorFactor=[0.24, 0.46, 0.68, 1.0],
            metallicFactor=0.2,
            roughnessFactor=0.25,
        )

    # 10. 观众人群点阵 (Crowd_ST_Team1/Team2_Mic, CrowdFlag_Mat)
    if "crowd" in mn_lower:
        col = [0.25, 0.52, 0.90, 1.0] if "team1" in mn_lower else [0.92, 0.48, 0.18, 1.0]
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorFactor=col,
            metallicFactor=0.05,
            roughnessFactor=0.7,
            doubleSided=True,
        )

    # 11. 通用纹理回退
    tex_cand = None
    mat_kv = meta.get("umodel_mat_bindings", {})
    if "Diffuse" in mat_kv:
        tex_cand = mat_kv["Diffuse"]
    elif "Diffuse" in meta.get("texture_parameters", {}):
        tex_cand = meta["texture_parameters"]["Diffuse"]
    elif meta.get("referenced_textures"):
        for rt in meta["referenced_textures"]:
            if not rt.endswith("_N") and not rt.endswith("_NORM"):
                tex_cand = rt
                break
    im = get_img(tex_cand, mode="RGB") if tex_cand else None
    if im is not None:
        return trimesh.visual.material.PBRMaterial(
            name=mn,
            baseColorTexture=im,
            metallicFactor=0.1,
            roughnessFactor=0.65,
        )

    return trimesh.visual.material.PBRMaterial(
        name=mn or "DefaultMaterial",
        baseColorFactor=[0.62, 0.64, 0.66, 1.0],
        metallicFactor=0.15,
        roughnessFactor=0.6,
    )

EXCLUDED_VFX_MESHES = {
    "Circle_Sprite",
    "Sphere01",
    "3DSprite",
    "LongField_LightCones",
    "LightCone_01",
    "GlowSheets_Team1_Combined",
    "GlowSheets_Team2_Combined",
    "FogCylinder",
}

def synthesize_glb(sg, out_glb_path, core_field_only=False, with_textures=True, is_hockey=False):
    scene = trimesh.Scene()
    inst_count = 0
    loaded_cache = {}
    grass_plane_added = False

    for inst in sg["instances"]:
        if inst.get("hidden") is True:
            continue
        pkg = inst["sublevel_package"]
        mesh_name = inst["mesh"]
        mat_list = inst.get("materials", [])

        # 排除 316 个近景 3D 碎草块 (Grass_1x1, Grass_Side, Grass_Goal_*, Grass_Corner) 以保持草坪标线清晰且体积紧凑
        if mesh_name.startswith("Grass_") and mesh_name != "Grass_Plane":
            continue
        # 避免 Grass_Plane (Base 与 LOD) 重叠造成 Z-fighting
        if mesh_name == "Grass_Plane":
            if grass_plane_added:
                continue
            grass_plane_added = True
        if mesh_name in EXCLUDED_VFX_MESHES:
            continue
        if any("lightcone" in m.lower() or "fog" in m.lower() or "hotspot" in m.lower() for m in mat_list):
            continue

        if core_field_only:
            if "OOB" in pkg:
                continue
            if mesh_name in ("LongField_OOB_Floor", "SkySphere01", "Park_BannerScaffold00", "Park_BannerFlag_CMB"):
                continue
        else:
            if not with_textures and mesh_name == "SkySphere01":
                continue

        gltf_path = mesh_paths.get(mesh_name)
        if not gltf_path or not os.path.exists(gltf_path):
            continue

        cache_key = (mesh_name, tuple(mat_list), with_textures, is_hockey)
        if cache_key in loaded_cache:
            geoms = loaded_cache[cache_key]
        else:
            sub = trimesh.load(gltf_path)
            geoms = list(sub.geometry.values()) if isinstance(sub, trimesh.Scene) else [sub]
            for idx, geom in enumerate(geoms):
                mname = mat_list[idx] if idx < len(mat_list) else (mat_list[0] if mat_list else None)
                geom.visual.material = create_pbr(mname, mesh_name, with_textures=with_textures, is_hockey=is_hockey)
            loaded_cache[cache_key] = geoms

        c_tr = inst.get("component_transform", {})
        Mc = make_transform(c_tr.get("translation"), c_tr.get("rotation"), c_tr.get("scale", 1.0), c_tr.get("scale3d"))
        act = inst.get("actor", {})
        Ma = make_transform(act.get("location"), act.get("rotation"), act.get("draw_scale", 1.0), act.get("draw_scale3d"))
        M_ue = Ma @ Mc
        M_gltf = C @ M_ue @ C_inv

        for g_idx, geom in enumerate(geoms):
            scene.add_geometry(geom, node_name=f"{mesh_name}_{inst_count}_{g_idx}", transform=M_gltf)
        inst_count += 1

    scene.export(out_glb_path, file_type="glb")
    sz_mb = os.path.getsize(out_glb_path) / (1024 * 1024)
    g = pygltflib.GLTF2().load(out_glb_path)
    print(f"-> 生成 {os.path.basename(out_glb_path)}: {sz_mb:.2f} MB ({inst_count} 个实例, {len(g.nodes)} 节点, {len(g.images)} 张贴图)")

synthesize_glb(sg_stadium, os.path.join(OUT_DIR, "models/ThrowbackStadium_Field.glb"), core_field_only=True, with_textures=True, is_hockey=False)
synthesize_glb(sg_stadium, os.path.join(OUT_DIR, "models/ThrowbackStadium_Field_WhiteModel.glb"), core_field_only=True, with_textures=False, is_hockey=False)
synthesize_glb(sg_stadium, os.path.join(OUT_DIR, "models/ThrowbackStadium.glb"), core_field_only=False, with_textures=True, is_hockey=False)
synthesize_glb(sg_stadium, os.path.join(OUT_DIR, "models/ThrowbackStadium_WhiteModel.glb"), core_field_only=False, with_textures=False, is_hockey=False)
synthesize_glb(sg_hockey, os.path.join(OUT_DIR, "models/ThrowbackHockey_Field.glb"), core_field_only=True, with_textures=True, is_hockey=True)
synthesize_glb(sg_hockey, os.path.join(OUT_DIR, "models/ThrowbackHockey.glb"), core_field_only=False, with_textures=True, is_hockey=True)
