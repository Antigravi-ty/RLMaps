import os
import json
import numpy as np
from PIL import Image
import trimesh

# Build material -> texture map
mat_to_tex = {}
for mdir in ["/tmp/woods_p_export/Woods_P/MaterialInstanceConstant", "/tmp/woods_p_export/Woods_P/Material3"]:
    if os.path.exists(mdir):
        for fname in os.listdir(mdir):
            if fname.endswith(".mat"):
                mat_name = fname[:-4]
                with open(os.path.join(mdir, fname), "r") as f:
                    for line in f:
                        if line.startswith("Diffuse="):
                            tex = line.strip().split("=")[1]
                            mat_to_tex[mat_name] = tex

# Also check mesh name to texture map heuristic
mesh_to_tex = {}
tex_dir = "/tmp/woods_p_export/Woods_P/Texture2D"
all_textures = set(f[:-4] for f in os.listdir(tex_dir) if f.endswith(".png"))

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

# Load meshes and assign textures
gltf_dir = "/tmp/woods_p_export/Woods_P/StaticMesh3"
loaded_geoms = {}

def get_mesh_geometry(mesh_name, mat_list=None):
    if mesh_name in loaded_geoms:
        return loaded_geoms[mesh_name]
    
    gltf_path = os.path.join(gltf_dir, f"{mesh_name}.gltf")
    if not os.path.exists(gltf_path):
        return None
    
    try:
        sub_scene = trimesh.load(gltf_path)
    except Exception as e:
        print(f"Error loading {mesh_name}: {e}")
        return None
        
    # Attempt to find texture
    tex_candidate = None
    if mat_list:
        for m in mat_list:
            if m in mat_to_tex and mat_to_tex[m] in all_textures:
                tex_candidate = mat_to_tex[m]
                break
    if not tex_candidate:
        if f"{mesh_name}_D" in all_textures:
            tex_candidate = f"{mesh_name}_D"
        elif mesh_name in all_textures:
            tex_candidate = mesh_name
            
    if tex_candidate:
        img_path = os.path.join(tex_dir, f"{tex_candidate}.png")
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                for geom in sub_scene.geometry.values():
                    if hasattr(geom, "visual") and hasattr(geom.visual, "material"):
                        geom.visual.material.image = img
            except Exception as e:
                pass
                
    geoms = list(sub_scene.geometry.values())
    loaded_geoms[mesh_name] = geoms
    return geoms

print("Synthesizing Driftwoods_Day arena...")
master_scene = trimesh.Scene()
inst_count = 0

for e in scene_data["exports"]:
    props = e.get("properties", {})
    if "StaticMesh" not in props:
        continue
    if props.get("HiddenGame") is True:
        continue
        
    mesh_name = props["StaticMesh"]["name"]
    # Check materials
    mat_list = []
    if isinstance(props.get("Materials"), dict) and "elements" in props["Materials"]:
        mat_list = [m["name"] for m in props["Materials"]["elements"]]
        
    geoms = get_mesh_geometry(mesh_name, mat_list)
    if not geoms:
        continue
        
    # Transform
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
        master_scene.add_geometry(geom, node_name=node_name, transform=M_gltf)
        
    inst_count += 1

print(f"Total instances placed in scene: {inst_count}")
out_glb = "/tmp/Driftwoods_Day.glb"
master_scene.export(out_glb, file_type="glb")
print(f"Successfully generated {out_glb} ({os.path.getsize(out_glb)} bytes)")
