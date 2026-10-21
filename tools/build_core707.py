#!/usr/bin/env python3
import os
import re
import json
import shutil
import numpy as np
from PIL import Image
import trimesh
import pygltflib

OUT_DIR = "/tmp/work/branch_core707"
if os.path.exists(OUT_DIR):
    shutil.rmtree(OUT_DIR)

os.makedirs(os.path.join(OUT_DIR, "models"), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "metadata", "scene_dumps"), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "raw"), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "skyboxes_and_textures", "Core_707"), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "skyboxes_and_textures", "Forbidden_Temple_Day_VFX"), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "skyboxes_and_textures", "Forbidden_Temple_Dusk_VFX"), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "tools"), exist_ok=True)

PKGS = [
    "ShatterShot_P",
    "ShatterShot_OOB_Exploration",
    "ShatterShot_VFX",
    "shattershot_p_MapImage_SF",
    "CHN_Stadium_Day_VFX",
    "CHN_Stadium_VFX",
    "Farm_VFX",
]

# Copy raw exports and scene dumps
for pkg in PKGS:
    src_g = f"/tmp/work/exported_grouped/{pkg}"
    if os.path.isdir(src_g):
        shutil.copytree(src_g, os.path.join(OUT_DIR, "raw", pkg))
    dump_f = f"/tmp/{pkg}.upk_scene.json"
    if os.path.isfile(dump_f):
        shutil.copy2(dump_f, os.path.join(OUT_DIR, "metadata", "scene_dumps", f"{pkg}.upk_scene.json"))

# Copy organized skyboxes_and_textures
for root, _, files in os.walk(os.path.join(OUT_DIR, "raw")):
    for f in files:
        if f.endswith((".png", ".gltf", ".bin")):
            full = os.path.join(root, f)
            if any(k in root for k in ["ShatterShot", "shattershot"]):
                shutil.copy2(full, os.path.join(OUT_DIR, "skyboxes_and_textures", "Core_707", f))
            elif "CHN_Stadium_Day_VFX" in root:
                shutil.copy2(full, os.path.join(OUT_DIR, "skyboxes_and_textures", "Forbidden_Temple_Day_VFX", f))
            elif "CHN_Stadium_VFX" in root:
                shutil.copy2(full, os.path.join(OUT_DIR, "skyboxes_and_textures", "Forbidden_Temple_Dusk_VFX", f))

# Index Core 707 meshes and textures
CORE_PKGS = ["ShatterShot_P", "ShatterShot_OOB_Exploration", "ShatterShot_VFX"]
mesh_paths = {}
tex_paths = {}
for pkg in CORE_PKGS:
    for root, _, files in os.walk(f"/tmp/work/exported_grouped/{pkg}"):
        for f in files:
            if f.endswith(".gltf"):
                mesh_paths[f[:-5]] = os.path.join(root, f)
            elif f.endswith(".png"):
                tex_paths[f[:-4].lower()] = os.path.join(root, f)

def get_img(name, mode="RGB"):
    p = tex_paths.get(name.lower())
    if p and os.path.exists(p):
        return Image.open(p).convert(mode)
    return None

# Bake Core 707 PBR textures from RGBA/RGB mask textures
baked_tex = {}
if "bo_cage_rgba" in tex_paths:
    im = Image.open(tex_paths["bo_cage_rgba"]).convert("RGBA")
    arr = np.array(im, dtype=np.float32) / 255.0
    rgb = np.clip(arr[:, :, :3] * 0.85 + 0.12, 0.0, 1.0)
    baked_tex["cage"] = Image.fromarray((rgb * 255).astype(np.uint8), mode="RGB")

if "bo_quarterpipe_rgb" in tex_paths:
    im = Image.open(tex_paths["bo_quarterpipe_rgb"]).convert("RGB")
    arr = np.array(im, dtype=np.float32) / 255.0
    # Dark metallic sci-fi wall with subtle cyan/orange accent
    shade = np.clip(arr[:, :, 1:2] * 0.8 + 0.18, 0.1, 1.0)
    trim = arr[:, :, 0:1]
    base_col = np.array([0.22, 0.25, 0.30], dtype=np.float32)[None, None, :]
    accent_col = np.array([0.35, 0.65, 0.95], dtype=np.float32)[None, None, :]
    rgb = np.clip((base_col * (1.0 - trim * 0.5) + accent_col * (trim * 0.5)) * shade, 0.0, 1.0)
    baked_tex["quarterpipe"] = Image.fromarray((rgb * 255).astype(np.uint8), mode="RGB")

if "bo_centerstrip_rgba" in tex_paths:
    im = Image.open(tex_paths["bo_centerstrip_rgba"]).convert("RGBA")
    arr = np.array(im, dtype=np.float32) / 255.0
    shade = np.clip(arr[:, :, 1:2] * 0.9 + 0.2, 0.15, 1.0)
    rgb = np.clip(np.array([0.28, 0.30, 0.35])[None, None, :] * shade, 0.0, 1.0)
    baked_tex["centerstrip"] = Image.fromarray((rgb * 255).astype(np.uint8), mode="RGB")

if "bo_hextiles_rgb" in tex_paths:
    im = Image.open(tex_paths["bo_hextiles_rgb"]).convert("RGB")
    arr = np.array(im, dtype=np.float32) / 255.0
    shade = np.clip(arr[:, :, 1:2] * 0.85 + 0.20, 0.15, 1.0)
    rim = arr[:, :, 0:1]
    # Blue team hex tile & Orange team hex tile
    blue_rgb = np.clip(np.array([0.16, 0.28, 0.52])[None, None, :] * shade + np.array([0.1, 0.45, 0.95])[None, None, :] * rim * 0.45, 0.0, 1.0)
    orange_rgb = np.clip(np.array([0.52, 0.26, 0.14])[None, None, :] * shade + np.array([0.95, 0.45, 0.1])[None, None, :] * rim * 0.45, 0.0, 1.0)
    baked_tex["tile_blue"] = Image.fromarray((blue_rgb * 255).astype(np.uint8), mode="RGB")
    baked_tex["tile_orange"] = Image.fromarray((orange_rgb * 255).astype(np.uint8), mode="RGB")

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

# Parse all Core 707 instances & 140 Dropshot hex tiles
instances = []
hex_tiles_meta = []

for pkg in CORE_PKGS:
    data = json.load(open(f"/tmp/{pkg}.upk_scene.json"))
    by_idx = {e["index"]: e for e in data["exports"]}
    for e in data["exports"]:
        if e["class"] == "StaticMeshComponent":
            props = e.get("properties", {})
            sm = props.get("StaticMesh")
            if not sm:
                continue
            mname = sm["name"]
            outer = by_idx.get(e["outer_index"] - 1, {}) if e.get("outer_index", 0) > 0 else {}
            outer_cls = outer.get("class", "")
            outer_props = outer.get("properties", {})

            # Skip unplaced template components
            if outer_cls not in ("StaticMeshCollectionActor", "BreakOutActor_Platform_TA", "StaticMeshActor"):
                if not props.get("Translation") and not props.get("Scale3D") and not outer_props.get("Location"):
                    continue

            hidden = bool(props.get("HiddenGame", False) or outer_props.get("bHidden", False))
            mats = [x["name"] for x in props.get("Materials", {}).get("elements", [])]

            entry = {
                "sublevel_package": pkg,
                "component_name": e["name"],
                "mesh": mname,
                "hidden": hidden,
                "actor_class": outer_cls,
                "actor_name": outer.get("name", ""),
                "actor_location": outer_props.get("Location"),
                "actor_rotation": outer_props.get("Rotation"),
                "actor_draw_scale": outer_props.get("DrawScale", 1.0),
                "actor_draw_scale3d": outer_props.get("DrawScale3D"),
                "comp_translation": props.get("Translation"),
                "comp_rotation": props.get("Rotation"),
                "comp_scale": props.get("Scale", 1.0),
                "comp_scale3d": props.get("Scale3D"),
                "materials": mats,
            }
            instances.append(entry)
            if outer_cls == "BreakOutActor_Platform_TA":
                loc = outer_props.get("Location", {"x": 0, "y": 0, "z": 0})
                rot = outer_props.get("Rotation", {"pitch": 0, "yaw": 0, "roll": 0})
                hex_tiles_meta.append({
                    "actor_name": outer.get("name", ""),
                    "mesh": mname,
                    "team": "Orange" if loc.get("y", 0) > 0 else "Blue",
                    "location": loc,
                    "rotation": rot,
                })

hex_tiles_meta.sort(key=lambda x: (x["team"], x["location"]["y"], x["location"]["x"]))

with open(os.path.join(OUT_DIR, "metadata", "core707_scenegraph.json"), "w") as f:
    json.dump({
        "arena": "Core 707 (Dropshot)",
        "internal_code": "ShatterShot_P",
        "total_instances": len(instances),
        "total_hex_tiles": len(hex_tiles_meta),
        "hex_tiles": hex_tiles_meta,
        "instances": instances,
    }, f, indent=2, ensure_ascii=False)

def get_pbr_for_core707(mesh_name, actor_loc, with_textures=True):
    if not with_textures:
        return trimesh.visual.material.PBRMaterial(
            name=f"{mesh_name}_White",
            baseColorFactor=[0.85, 0.85, 0.85, 1.0],
            metallicFactor=0.15,
            roughnessFactor=0.55,
        )
    ml = mesh_name.lower()
    if "tile" in ml:
        y = (actor_loc or {}).get("y", 0.0)
        tex = baked_tex.get("tile_orange" if y > 0 else "tile_blue")
        return trimesh.visual.material.PBRMaterial(
            name="HexTile_Orange" if y > 0 else "HexTile_Blue",
            baseColorTexture=tex,
            metallicFactor=0.45,
            roughnessFactor=0.4,
        )
    if "centerpiece" in ml:
        return trimesh.visual.material.PBRMaterial(
            name="CenterPiece_PBR",
            baseColorTexture=baked_tex.get("centerstrip"),
            metallicFactor=0.6,
            roughnessFactor=0.35,
        )
    if "quarterpipe" in ml or "arena_sm" in ml:
        return trimesh.visual.material.PBRMaterial(
            name="ArenaWall_PBR",
            baseColorTexture=baked_tex.get("quarterpipe"),
            metallicFactor=0.55,
            roughnessFactor=0.4,
        )
    if "cage" in ml:
        return trimesh.visual.material.PBRMaterial(
            name="ArenaCage_PBR",
            baseColorTexture=baked_tex.get("cage"),
            metallicFactor=0.75,
            roughnessFactor=0.3,
        )
    if "edgeglow" in ml:
        return trimesh.visual.material.PBRMaterial(
            name="EdgeGlow_PBR",
            baseColorFactor=[0.2, 0.75, 1.0, 1.0],
            emissiveFactor=[0.2, 0.75, 1.0],
            metallicFactor=0.1,
            roughnessFactor=0.2,
        )
    if "oob_floor" in ml or "building" in ml:
        im = get_img("BO_OOB_Panel_D", mode="RGB")
        return trimesh.visual.material.PBRMaterial(
            name="OOB_Structure_PBR",
            baseColorTexture=im,
            baseColorFactor=[0.35, 0.38, 0.45, 1.0],
            metallicFactor=0.5,
            roughnessFactor=0.5,
        )
    return trimesh.visual.material.PBRMaterial(
        name=f"{mesh_name}_PBR",
        baseColorFactor=[0.5, 0.55, 0.62, 1.0],
        metallicFactor=0.4,
        roughnessFactor=0.5,
    )

def build_core707_glb(out_name, field_only=False, with_textures=True, collision_only=False):
    scene = trimesh.Scene()
    cnt = 0
    for inst in instances:
        mname = inst["mesh"]
        is_coll = mname in ("BO_collision_03", "BO_CenterPiece_02_COLL", "FloorCollision_Plane", "breakout_wall", "breakout_wall2")
        if collision_only:
            if not is_coll:
                continue
        else:
            if is_coll or mname in ("SM_SkySphere", "CloudPlane", "BottomFogLines_SM"):
                continue
            if field_only and mname in ("BO_OOB_Building", "BO_OOB_floorplane"):
                continue

        gpath = mesh_paths.get(mname)
        if not gpath or not os.path.exists(gpath):
            continue

        sub = trimesh.load(gpath)
        geoms = list(sub.geometry.values()) if isinstance(sub, trimesh.Scene) else [sub]
        mat = get_pbr_for_core707(mname, inst.get("actor_location"), with_textures=with_textures)

        Mc = make_transform(inst["comp_translation"], inst["comp_rotation"], inst["comp_scale"], inst["comp_scale3d"])
        Ma = make_transform(inst["actor_location"], inst["actor_rotation"], inst["actor_draw_scale"], inst["actor_draw_scale3d"])
        M_gltf = C @ (Ma @ Mc) @ C_inv

        for g_idx, geom in enumerate(geoms):
            g_copy = geom.copy()
            g_copy.visual.material = mat
            scene.add_geometry(g_copy, node_name=f"{mname}_{cnt}_{g_idx}", transform=M_gltf)
        cnt += 1

    out_path = os.path.join(OUT_DIR, "models", out_name)
    scene.export(out_path, file_type="glb")
    sz = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Built {out_name}: {sz:.2f} MB ({cnt} instances)")

build_core707_glb("Core707.glb", field_only=False, with_textures=True, collision_only=False)
build_core707_glb("Core707_WhiteModel.glb", field_only=False, with_textures=False, collision_only=False)
build_core707_glb("Core707_Field.glb", field_only=True, with_textures=True, collision_only=False)
build_core707_glb("Core707_Field_WhiteModel.glb", field_only=True, with_textures=False, collision_only=False)
build_core707_glb("Core707_Collision.glb", field_only=False, with_textures=False, collision_only=True)
