#!/usr/bin/env python3
"""
Driftwoods 场景与核心球场自动化合成管线脚本
支持生成日间全场景、日间全场景白模、Woods_Field* 核心球场模型及核心球场白模。
"""

import os
import sys
import json
import time
import numpy as np
from PIL import Image
import trimesh
import pygltflib

# 基础路径配置（基于仓库相对路径）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
RAW_DIR = os.path.join(REPO_DIR, "raw", "Woods_P")
TEX_DIR = os.path.join(RAW_DIR, "Texture2D")
MESH_DIR = os.path.join(RAW_DIR, "StaticMesh3")
SCENEGRAPH_PATH = os.path.join(REPO_DIR, "metadata", "driftwoods_day_scenegraph.json")
MODELS_DIR = os.path.join(REPO_DIR, "models")

os.makedirs(MODELS_DIR, exist_ok=True)

# 索引全部可用贴图
all_textures = {}
if os.path.exists(TEX_DIR):
    for f in os.listdir(TEX_DIR):
        if f.endswith(".png"):
            all_textures[os.path.splitext(f)[0].lower()] = os.path.join(TEX_DIR, f)

# 构建通用材质到漫反射贴图的映射表
mat_to_tex = {}
for mdir in [os.path.join(RAW_DIR, "MaterialInstanceConstant"), os.path.join(RAW_DIR, "Material3")]:
    if os.path.exists(mdir):
        for fname in os.listdir(mdir):
            if fname.endswith(".mat"):
                m_name = fname[:-4].lower()
                with open(os.path.join(mdir, fname), "r") as f:
                    for line in f:
                        if line.startswith("Diffuse="):
                            tex = line.strip().split("=")[1].strip()
                            mat_to_tex[m_name] = tex
                            break

# 读取场景元数据
with open(SCENEGRAPH_PATH, "r") as f:
    sg = json.load(f)

# 虚幻空间到 glTF 坐标系转换矩阵
C = np.array([
    [0.01, 0.0,  0.0,  0.0],
    [0.0,  0.0,  0.01, 0.0],
    [0.0,  0.01, 0.0,  0.0],
    [0.0,  0.0,  0.0,  1.0]
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
def get_img(name, convert_rgb=False):
    if not name:
        return None
    k = (name.lower(), convert_rgb)
    if k in img_cache:
        return img_cache[k]
    path = all_textures.get(name.lower())
    if path and os.path.exists(path):
        im = Image.open(path)
        if convert_rgb:
            im = im.convert("RGB")
        img_cache[k] = im
        return im
    return None

def create_pbr(mat_name, mesh_name, with_textures=True):
    if not with_textures:
        return trimesh.visual.material.PBRMaterial(
            baseColorFactor=[0.85, 0.85, 0.85, 1.0],
            metallicFactor=0.1,
            roughnessFactor=0.5
        )
        
    mn = mat_name.lower() if mat_name else ""
    mesh_lower = mesh_name.lower()
    
    # 1. 球场地面：使用 2048x2048 未压缩全高清地面与标线贴图
    if "grass_base_team1_mic" in mn or "groomedgrass_fakelight_team1_mic" in mn or "fieldlines" in mn or (mesh_name == "Woods_Field_Ground" and not mn):
        img = get_img("Woods_FieldLines_D_Unfiltered", convert_rgb=True)
        return trimesh.visual.material.PBRMaterial(
            baseColorTexture=img,
            baseColorFactor=[1.0, 1.0, 1.0, 1.0],
            metallicFactor=0.0,
            roughnessFactor=0.85
        )
        
    # 2. 黑色/深色金属结构件（看台支架、围栏金属立柱、电线等）
    if "bch_g_metal_matte_black_mic" in mn:
        return trimesh.visual.material.PBRMaterial(
            baseColorFactor=[0.08, 0.08, 0.08, 1.0],
            metallicFactor=0.85,
            roughnessFactor=0.35
        )
    if "woods_metal_dark" in mn or "powerlinewire" in mn:
        return trimesh.visual.material.PBRMaterial(
            baseColorFactor=[0.12, 0.12, 0.12, 1.0],
            metallicFactor=0.8,
            roughnessFactor=0.4
        )
        
    # 3. 发光带与霓虹指示条（坡道边沿发光带、球门金属亮条）
    if "netglow_mat" in mn or "metaltrim_glow" in mn or "glow" in mn:
        return trimesh.visual.material.PBRMaterial(
            baseColorFactor=[1.0, 0.85, 0.35, 1.0],
            emissiveFactor=[1.0, 0.85, 0.35],
            metallicFactor=0.1,
            roughnessFactor=0.4
        )
        
    # 4. 六边形能量防护网与网眼围栏（半透明与发光蜂窝网格）
    if "hex" in mn or "wl_g_netfence_mic" in mn or "csnetfence" in mn or "net" in mn:
        img = get_img("ForcefieldHex")
        return trimesh.visual.material.PBRMaterial(
            baseColorTexture=img if img else None,
            baseColorFactor=[0.5, 0.75, 1.0, 0.5],
            emissiveFactor=[0.1, 0.2, 0.4],
            metallicFactor=0.1,
            roughnessFactor=0.3,
            alphaMode="BLEND"
        )
        
    # 5. 看台木质长凳/坐板
    if "woods_wood_moss_vert_mat" in mn or "bleachers" in mesh_lower:
        img = get_img("Bleachers_Boards_D") or get_img("Woods_WoodPlanks_D") or get_img("Woods_Wood_Basic_D")
        return trimesh.visual.material.PBRMaterial(
            baseColorTexture=img,
            metallicFactor=0.05,
            roughnessFactor=0.7
        )
        
    # 6. 木板/木质构件
    if "plank" in mn:
        img = get_img("Woods_WoodPlanks_D") or get_img("Woods_Wood_Basic_D")
        return trimesh.visual.material.PBRMaterial(
            baseColorTexture=img,
            metallicFactor=0.05,
            roughnessFactor=0.7
        )
        
    # 7. 平铺木纹
    if "woodtiled" in mn:
        img = get_img("Woods_Wood_Basic_D") or get_img("Woods_WoodPlanks_D")
        return trimesh.visual.material.PBRMaterial(
            baseColorTexture=img,
            metallicFactor=0.05,
            roughnessFactor=0.7
        )

    # 8. 通用材质查找：优先通过材质名映射
    tex_candidate = None
    if mn in mat_to_tex and mat_to_tex[mn].lower() in all_textures:
        tex_candidate = mat_to_tex[mn]
    elif f"{mesh_name}_D".lower() in all_textures:
        tex_candidate = f"{mesh_name}_D"
    elif mesh_lower in all_textures:
        tex_candidate = mesh_name

    img = get_img(tex_candidate) if tex_candidate else None
    if img:
        return trimesh.visual.material.PBRMaterial(
            baseColorTexture=img,
            metallicFactor=0.05,
            roughnessFactor=0.7
        )

    return trimesh.visual.material.PBRMaterial(
        baseColorFactor=[0.75, 0.75, 0.75, 1.0],
        metallicFactor=0.1,
        roughnessFactor=0.6
    )

def build_scene(filter_prefix=None, with_textures=True):
    scene = trimesh.Scene()
    inst_count = 0
    loaded_cache = {}

    for inst in sg["instances"]:
        mesh_name = inst.get("mesh")
        if not mesh_name:
            continue
        if filter_prefix and not mesh_name.startswith(filter_prefix):
            continue
        if inst.get("hidden") is True:
            continue
        # 核心球场模型排除远景草地 LOD 重叠层，消除 Z-fighting 闪烁
        if filter_prefix == "Woods_Field" and mesh_name == "Woods_Field_Ground_LOD":
            continue

        gltf_path = os.path.join(MESH_DIR, f"{mesh_name}.gltf")
        if not os.path.exists(gltf_path):
            continue

        mat_list = inst.get("materials", [])
        cache_key = (mesh_name, tuple(mat_list), with_textures)
        if cache_key in loaded_cache:
            geoms = loaded_cache[cache_key]
        else:
            sub = trimesh.load(gltf_path)
            geoms = list(sub.geometry.values())
            for idx, geom in enumerate(geoms):
                mname = mat_list[idx] if idx < len(mat_list) else None
                geom.visual.material = create_pbr(mname, mesh_name, with_textures=with_textures)
            loaded_cache[cache_key] = geoms

        c_tr = inst.get("component_transform", {})
        c_loc = c_tr.get("translation")
        c_rot = c_tr.get("rotation")
        c_scale = c_tr.get("scale", 1.0)
        c_scale3d = c_tr.get("scale3d")

        act = inst.get("actor", {})
        a_loc = act.get("location")
        a_rot = act.get("rotation")
        a_scale = act.get("draw_scale", 1.0)
        a_scale3d = act.get("draw_scale3d")

        Mc = make_transform(c_loc, c_rot, c_scale, c_scale3d)
        Ma = make_transform(a_loc, a_rot, a_scale, a_scale3d)
        M_ue = Ma @ Mc
        M_gltf = C @ M_ue @ C_inv

        for g_idx, geom in enumerate(geoms):
            node_name = f"{mesh_name}_{inst_count}_{g_idx}"
            scene.add_geometry(geom, node_name=node_name, transform=M_gltf)

        inst_count += 1

    return scene, inst_count

def main():
    models_to_build = [
        ("Driftwoods_Field.glb", "Woods_Field", True, "Woods_Field* 核心球场（带高清贴图与半透力场网）"),
        ("Driftwoods_Field_WhiteModel.glb", "Woods_Field", False, "Woods_Field* 核心球场白模（纯几何体）"),
        ("Driftwoods_Day.glb", None, True, "全场景日间版（带高清地面及完整贴图）"),
        ("Driftwoods_Day_WhiteModel.glb", None, False, "全场景日间版白模（纯几何体）"),
    ]

    for out_name, prefix, with_tex, desc in models_to_build:
        print(f"\n合成任务: {out_name} - {desc}")
        t0 = time.time()
        scene, count = build_scene(filter_prefix=prefix, with_textures=with_tex)
        out_path = os.path.join(MODELS_DIR, out_name)
        scene.export(out_path, file_type="glb")
        size_mb = os.path.getsize(out_path) / (1024 * 1024)
        g = pygltflib.GLTF2().load(out_path)
        print(f"-> 完成: {out_name} ({size_mb:.2f} MB, {count} 个实例, {len(g.images)} 张嵌入贴图, 耗时 {time.time()-t0:.2f}s)")

if __name__ == "__main__":
    main()
