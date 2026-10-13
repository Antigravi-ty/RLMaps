import os
import json
import numpy as np
from PIL import Image
import trimesh
import pygltflib

# Build material -> texture map
tex_dir = "/tmp/woods_p_export/Woods_P/Texture2D"
all_textures = {os.path.splitext(f)[0].lower(): os.path.join(tex_dir, f) for f in os.listdir(tex_dir) if f.endswith(".png")}

mat_to_tex = {}
for mdir in ["/tmp/woods_p_export/Woods_P/MaterialInstanceConstant", "/tmp/woods_p_export/Woods_P/Material3"]:
    if os.path.exists(mdir):
        for fname in os.listdir(mdir):
            if fname.endswith(".mat"):
                mat_name = fname[:-4]
                with open(os.path.join(mdir, fname), "r") as f:
                    for line in f:
                        if line.startswith("Diffuse="):
                            tex = line.strip().split("=")[1].strip()
                            mat_to_tex[mat_name.lower()] = tex
                            break

with open("/tmp/Woods_P.upk_scene.json", "r") as f:
    scene_data = json.load(f)

by_idx = {e["index"]: e for e in scene_data["exports"]}

def rotator_to_matrix(pitch, yaw, roll):
    p = pitch * (2.0 * np.pi / 65536.0)
    y = yaw   * (2.0 * np.pi / 65536.0)
    r = roll  * (2.0 * np.pi / 65536.0)
    
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(r), -np.sin(r)],
        [0, np.sin(r), np.cos(r)]
    ])
    Ry = np.array([
        [np.cos(p), 0, np.sin(p)],
        [0, 1, 0],
        [-np.sin(p), 0, np.cos(p)]
    ])
    Rz = np.array([
        [np.cos(y), -np.sin(y), 0],
        [np.sin(y), np.cos(y), 0],
        [0, 0, 1]
    ])
    return Rz @ Ry @ Rx

def make_transform(loc=None, rot=None, scale=1.0, scale3d=None):
    M = np.eye(4)
    if rot:
        pitch = rot.get("pitch", 0)
        yaw = rot.get("yaw", 0)
        roll = rot.get("roll", 0)
        M[:3, :3] = rotator_to_matrix(pitch, yaw, roll)
    
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

C = np.array([
    [0.01, 0.0,  0.0,  0.0],
    [0.0,  0.0,  0.01, 0.0],
    [0.0,  0.01, 0.0,  0.0],
    [0.0,  0.0,  0.0,  1.0]
])
C_inv = np.linalg.inv(C)

gltf_dir = "/tmp/woods_p_export/Woods_P/StaticMesh3"
image_cache = {}

def get_texture_image(tex_name):
    if not tex_name:
        return None
    key = tex_name.lower()
    if key in image_cache:
        return image_cache[key]
    if key in all_textures:
        img = Image.open(all_textures[key])
        image_cache[key] = img
        return img
    return None

def build_scene(filter_prefix=None, with_textures=True):
    scene = trimesh.Scene()
    inst_count = 0
    loaded_cache = {}

    for e in scene_data["exports"]:
        props = e.get("properties", {})
        if "StaticMesh" not in props:
            continue
        if props.get("HiddenGame") is True:
            continue
            
        mesh_name = props["StaticMesh"]["name"]
        if filter_prefix and not mesh_name.startswith(filter_prefix):
            continue
            
        mat_list = []
        if isinstance(props.get("Materials"), dict) and "elements" in props["Materials"]:
            mat_list = [m["name"] for m in props["Materials"]["elements"]]
            
        # Load mesh
        gltf_path = os.path.join(gltf_dir, f"{mesh_name}.gltf")
        if not os.path.exists(gltf_path):
            continue
            
        cache_key = (mesh_name, tuple(mat_list), with_textures)
        if cache_key in loaded_cache:
            geoms = loaded_cache[cache_key]
        else:
            sub = trimesh.load(gltf_path)
            geoms = list(sub.geometry.values())
            
            if with_textures:
                for idx, geom in enumerate(geoms):
                    mat_name = mat_list[idx] if idx < len(mat_list) else None
                    tex_file = None
                    if mat_name and mat_name.lower() in mat_to_tex:
                        tex_file = mat_to_tex[mat_name.lower()]
                    elif f"{mesh_name}_D".lower() in all_textures:
                        tex_file = f"{mesh_name}_D"
                    elif mesh_name.lower() in all_textures:
                        tex_file = mesh_name
                    elif "wood" in mesh_name.lower() and "woods_wood_basic_d" in all_textures:
                        tex_file = "Woods_Wood_Basic_D"
                            
                    img = get_texture_image(tex_file)
                    if img:
                        geom.visual.material = trimesh.visual.material.PBRMaterial(
                            baseColorTexture=img,
                            metallicFactor=0.05,
                            roughnessFactor=0.7
                        )
            else:
                white_mat = trimesh.visual.material.PBRMaterial(
                    baseColorFactor=[0.85, 0.85, 0.85, 1.0],
                    metallicFactor=0.1,
                    roughnessFactor=0.5
                )
                for geom in geoms:
                    geom.visual.material = white_mat

            loaded_cache[cache_key] = geoms
            
        # Transforms
        c_loc = props.get("Translation")
        c_rot = props.get("Rotation")
        c_scale = props.get("Scale", 1.0)
        c_scale3d = props.get("Scale3D")
        
        outer_idx = e.get("outer_index", 0)
        outer = by_idx.get(outer_idx - 1) if outer_idx > 0 else None
        
        a_loc = outer.get("properties", {}).get("Location") if outer else None
        a_rot = outer.get("properties", {}).get("Rotation") if outer else None
        a_scale = outer.get("properties", {}).get("DrawScale", 1.0) if outer else 1.0
        a_scale3d = outer.get("properties", {}).get("DrawScale3D") if outer else None
        
        Mc = make_transform(c_loc, c_rot, c_scale, c_scale3d)
        Ma = make_transform(a_loc, a_rot, a_scale, a_scale3d)
        M_ue = Ma @ Mc
        M_gltf = C @ M_ue @ C_inv
        
        for g_idx, geom in enumerate(geoms):
            node_name = f"{mesh_name}_{inst_count}_{g_idx}"
            scene.add_geometry(geom, node_name=node_name, transform=M_gltf)
            
        inst_count += 1

    return scene, inst_count

models_to_build = [
    ("Driftwoods_Day.glb", None, True, "Full scene with embedded textures"),
    ("Driftwoods_Day_WhiteModel.glb", None, False, "Full scene white clay model"),
    ("Driftwoods_Field.glb", "Woods_Field", True, "Woods_Field core arena with embedded textures"),
    ("Driftwoods_Field_WhiteModel.glb", "Woods_Field", False, "Woods_Field core arena white clay model"),
]

for out_name, prefix, with_tex, desc in models_to_build:
    print(f"\nBuilding {out_name} ({desc})...")
    scene, count = build_scene(filter_prefix=prefix, with_textures=with_tex)
    out_path = os.path.join("/tmp", out_name)
    scene.export(out_path, file_type="glb")
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    g = pygltflib.GLTF2().load(out_path)
    print(f"-> Generated {out_name}: {size_mb:.2f} MB, {count} instances, {len(g.images)} textures embedded.")
