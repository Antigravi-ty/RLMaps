#!/usr/bin/env python3
"""
三蹦子模式 (Confidential_ThirdWheel_Test / AprilFool LTM / Tritip / Body_Topple)
与 Mutator 特殊球体/道具完整解析及 GLB 合成脚本
"""
import os
import re
import io
import json
import shutil
import numpy as np
from PIL import Image
import trimesh
import pygltflib

OUT_DIR = "/tmp/work/branch_tricycle"
if os.path.exists(OUT_DIR):
    shutil.rmtree(OUT_DIR)

for sub in [
    "models/tricycle_cars",
    "models/mutator_balls",
    "models/mutator_items",
    "textures_and_icons/topple_tricycle",
    "textures_and_icons/mutator_balls",
    "textures_and_icons/mutator_items_and_icons",
    "metadata/scene_dumps",
    "raw",
    "tools",
]:
    os.makedirs(os.path.join(OUT_DIR, sub), exist_ok=True)

# 1. 复制原始导出资产与 Scene Dumps
SKYBOX_PKGS = ["GameInfo_LTM_AprilFool_SF", "Mutators_SF", "Mutators_Balls_SF", "Mutators_Items_SF"]
BODY_PKGS = ["body_topple_SF", "Body_Topple_T_SF"]

for pkg in SKYBOX_PKGS:
    src = f"/tmp/work/exports_skybox33/{pkg}/{pkg}"
    if os.path.isdir(src):
        shutil.copytree(src, os.path.join(OUT_DIR, "raw", pkg))
    dump_f = f"/tmp/work/dumps_skybox33/{pkg}.upk_scene.json"
    if os.path.isfile(dump_f):
        shutil.copy2(dump_f, os.path.join(OUT_DIR, "metadata/scene_dumps", f"{pkg}.upk_scene.json"))

for pkg in BODY_PKGS:
    src = f"/tmp/work/exports_bodiesV2/{pkg}/{pkg}"
    if os.path.isdir(src):
        shutil.copytree(src, os.path.join(OUT_DIR, "raw", pkg))
    dump_f = f"/tmp/work/dumps_bodiesV2/{pkg}.upk_scene.json"
    if os.path.isfile(dump_f):
        shutil.copy2(dump_f, os.path.join(OUT_DIR, "metadata/scene_dumps", f"{pkg}.upk_scene.json"))

# 复制整理贴图与图标
for pkg in BODY_PKGS:
    tdir = f"/tmp/work/exports_bodiesV2/{pkg}/{pkg}/Texture2D"
    if os.path.isdir(tdir):
        for f in os.listdir(tdir):
            if f.endswith(".png"):
                shutil.copy2(os.path.join(tdir, f), os.path.join(OUT_DIR, "textures_and_icons/topple_tricycle", f))

for f in os.listdir("/tmp/work/exports_skybox33/Mutators_Balls_SF/Mutators_Balls_SF/Texture2D"):
    if f.endswith(".png"):
        shutil.copy2(
            os.path.join("/tmp/work/exports_skybox33/Mutators_Balls_SF/Mutators_Balls_SF/Texture2D", f),
            os.path.join(OUT_DIR, "textures_and_icons/mutator_balls", f),
        )

for pkg in ["Mutators_Items_SF", "GameInfo_LTM_AprilFool_SF"]:
    tdir = f"/tmp/work/exports_skybox33/{pkg}/{pkg}/Texture2D"
    if os.path.isdir(tdir):
        for f in os.listdir(tdir):
            if f.endswith(".png"):
                shutil.copy2(os.path.join(tdir, f), os.path.join(OUT_DIR, "textures_and_icons/mutator_items_and_icons", f))

# 2. 生成三蹦子 (Topple & Octane) 高细节分材质 PBR 贴图与 GLB 模型
topple_tex_dir = "/tmp/work/exports_bodiesV2/body_topple_SF/body_topple_SF/Texture2D"

def bake_topple_body_tex():
    d_im = Image.open(os.path.join(topple_tex_dir, "Body_Topple_D.png")).convert("RGBA").resize((512, 512), Image.Resampling.BICUBIC)
    fx_im = Image.open(os.path.join(topple_tex_dir, "Body_Topple_Fxmasks.png")).convert("RGBA").resize((512, 512), Image.Resampling.BICUBIC)
    curv_im = Image.open(os.path.join(topple_tex_dir, "Body_Topple_Curvature.png")).convert("RGB").resize((512, 512), Image.Resampling.BICUBIC)
    d_arr = np.array(d_im, dtype=np.float32) / 255.0
    fx_arr = np.array(fx_im, dtype=np.float32) / 255.0
    curv_arr = np.array(curv_im, dtype=np.float32) / 255.0

    # Paint mask (A 通道) 为蓝/橙主车漆，其余为深灰金属/碳纤边框与高光曲率
    paint_w = np.clip(d_arr[:, :, 3], 0.0, 1.0)[..., None]
    ao = np.clip(fx_arr[:, :, 0] * 0.85 + 0.25, 0.2, 1.15)[..., None]
    bevel = np.clip((curv_arr[:, :, 0] - 0.5) * 0.35, -0.15, 0.20)[..., None]

    paint_col = np.array([0.12, 0.46, 0.92], dtype=np.float32)[None, None, :]  # 经典蓝队金属漆
    trim_col = np.array([0.18, 0.20, 0.23], dtype=np.float32)[None, None, :]
    rgb = np.clip((paint_col * paint_w + trim_col * (1.0 - paint_w)) * ao + bevel, 0.0, 1.0)
    return Image.fromarray((rgb * 255.0).astype(np.uint8), mode="RGB")

def bake_topple_chassis_tex():
    d_im = Image.open(os.path.join(topple_tex_dir, "Chassis_Topple_D.png")).convert("RGB").resize((512, 512), Image.Resampling.BICUBIC)
    rgb_im = Image.open(os.path.join(topple_tex_dir, "Chassis_Topple_RGB.png")).convert("RGBA").resize((512, 512), Image.Resampling.BICUBIC)
    d_arr = np.array(d_im, dtype=np.float32) / 255.0
    rgb_arr = np.array(rgb_im, dtype=np.float32) / 255.0
    ao = np.clip(rgb_arr[:, :, 3] * 0.9 + 0.35, 0.3, 1.15)[..., None]
    chrome_w = np.clip(rgb_arr[:, :, 1] * 2.5, 0.0, 1.0)[..., None]
    base = np.clip(d_arr * 1.45 + 0.08, 0.08, 0.85)
    chrome_col = np.array([0.78, 0.82, 0.86], dtype=np.float32)[None, None, :]
    out = np.clip((base * (1.0 - chrome_w) + chrome_col * chrome_w) * ao, 0.0, 1.0)
    return Image.fromarray((out * 255.0).astype(np.uint8), mode="RGB")

topple_body_tex = bake_topple_body_tex()
topple_chassis_tex = bake_topple_chassis_tex()

def shift_vertices_to_three_wheels(verts):
    """
    将前桥悬挂、转向节、前刹车盘与前控制臂顶点 (X > 0.30m, Y < 0.08m, |Z| > 0.04m)
    向车头中心线 (Z -> ±0.05m / 居中) 收拢，匹配 CAR_CONFIG_PSYCLOPS (FRONT_WHEELS_OFFSET.y = 5.0 uu)
    """
    v = verts.copy()
    front_susp_mask = (v[:, 0] > 0.34) & (v[:, 1] < 0.04) & (np.abs(v[:, 2]) > 0.03)
    # 按 X 与 Y 平滑过渡收窄横向 Z 坐标 (从 ±0.24m 收窄至 ±0.05m)
    v[front_susp_mask, 2] *= 0.21
    return v

def build_topple_glbs():
    sk_path = "/tmp/work/exports_bodiesV2/body_topple_SF/body_topple_SF/SkeletalMesh3/Body_Topple_SK.gltf"
    cone_path = "/tmp/work/exports_bodiesV2/body_topple_SF/body_topple_SF/StaticMesh3/Body_Topple_BoostconeMesh.gltf"
    s = trimesh.load(sk_path)
    geoms = list(s.geometry.values())

    # 7 个原生材质槽分类配置 (完整保留每个平面的细节材质分类)
    slot_configs = [
        ("01_MIC_Topple_Chassis", topple_chassis_tex, [1.0, 1.0, 1.0, 1.0], 0.78, 0.38, None, "OPAQUE"),
        ("02_MIC_Topple_CarbonFiber", None, [0.14, 0.15, 0.17, 1.0], 0.35, 0.42, None, "OPAQUE"),
        ("03_MIC_Topple_Windshield", None, [0.08, 0.11, 0.16, 1.0], 0.90, 0.12, None, "OPAQUE"),
        ("04_MIC_Topple_Lenses_Headlights", None, [0.95, 0.96, 1.0, 1.0], 0.20, 0.15, [0.85, 0.90, 1.0], "OPAQUE"),
        ("05_MIC_Topple_Plastic_Trim", None, [0.16, 0.17, 0.19, 1.0], 0.08, 0.68, None, "OPAQUE"),
        ("06_MAT_Vehicle_Glass_Translucent", None, [0.20, 0.32, 0.48, 0.42], 0.85, 0.10, None, "BLEND"),
        ("07_MIC_Topple_Body_Paint", topple_body_tex, [1.0, 1.0, 1.0, 1.0], 0.55, 0.28, None, "OPAQUE"),
    ]

    for mode_name, is_three_wheel, with_tex in [
        ("Topple_Tricycle_ThreeWheel.glb", True, True),
        ("Topple_Standard_FourWheel.glb", False, True),
        ("Topple_WhiteModel.glb", True, False),
    ]:
        scene = trimesh.Scene()
        for idx, g in enumerate(geoms):
            gm = g.copy()
            if is_three_wheel:
                gm.vertices = shift_vertices_to_three_wheels(gm.vertices)
            sname, btex, bcol, met, rough, emis, amode = slot_configs[idx]
            if not with_tex:
                gm.visual.material = trimesh.visual.material.PBRMaterial(
                    name=f"{sname}_White",
                    baseColorFactor=[0.85, 0.85, 0.85, 0.45 if amode == "BLEND" else 1.0],
                    metallicFactor=0.1,
                    roughnessFactor=0.55,
                    alphaMode=amode,
                    doubleSided=True,
                )
            else:
                gm.visual.material = trimesh.visual.material.PBRMaterial(
                    name=sname,
                    baseColorTexture=btex,
                    baseColorFactor=bcol,
                    metallicFactor=met,
                    roughnessFactor=rough,
                    emissiveFactor=emis,
                    alphaMode=amode,
                    doubleSided=True,
                )
            scene.add_geometry(gm, node_name=sname)

        # 挂载氮气喷口锥体网格 (BoostEmitter Socket: Location=(-53.17, 0, 7.01) UU -> (-0.5317, 0.0701, 0) m)
        if os.path.exists(cone_path):
            cm = trimesh.load(cone_path, force="mesh")
            cm.visual.material = trimesh.visual.material.PBRMaterial(
                name="08_BoostCone_FX",
                baseColorFactor=[1.0, 0.55, 0.12, 0.65] if with_tex else [0.85, 0.85, 0.85, 0.5],
                emissiveFactor=[1.0, 0.45, 0.08] if with_tex else None,
                alphaMode="BLEND",
                doubleSided=True,
            )
            T_cone = np.eye(4)
            T_cone[:3, 3] = [-0.5317, 0.0701, 0.0]
            scene.add_geometry(cm, node_name="08_BoostCone_FX", transform=T_cone)

        out_p = os.path.join(OUT_DIR, "models/tricycle_cars", mode_name)
        scene.export(out_p, file_type="glb")
        print(f"-> 生成 {mode_name}: {os.path.getsize(out_p)/1024:.1f} KB")

    # 生成保留完整 55 骨骼绑定的 SkeletalRigged GLB (并将前轮骨骼横向偏移改为 ±0.05m 三蹦子布局)
    g_rig = pygltflib.GLTF2().load(sk_path)
    for n in g_rig.nodes:
        if n.name in ("FL_WheelTranslation_jnt", "FL_axleShaft_jnt", "FL_ctrlArm_jnt", "FL_Shock_A_jnt"):
            if n.translation and len(n.translation) == 3:
                n.translation[2] = -0.050
        elif n.name in ("FR_WheelTranslation_jnt", "FR_axleShaft_jnt", "FR_ctrlArm_jnt", "FR_Shock_A_jnt"):
            if n.translation and len(n.translation) == 3:
                n.translation[2] = +0.050
    for idx, m in enumerate(g_rig.materials):
        if idx < len(slot_configs):
            sname, _, bcol, met, rough, emis, amode = slot_configs[idx]
            m.name = sname
            m.pbrMetallicRoughness = pygltflib.PbrMetallicRoughness(
                baseColorFactor=[0.14, 0.48, 0.92, 1.0] if idx == 6 else bcol,
                metallicFactor=met,
                roughnessFactor=rough,
            )
            if emis:
                m.emissiveFactor = emis
            m.alphaMode = amode
            m.doubleSided = True
    rig_out = os.path.join(OUT_DIR, "models/tricycle_cars/Topple_Tricycle_ThreeWheel_SkeletalRigged.glb")
    g_rig.convert_buffers(pygltflib.BufferFormat.BINARYBLOB)
    g_rig.save_binary(rig_out)
    print(f"-> 生成 Topple_Tricycle_ThreeWheel_SkeletalRigged.glb: {os.path.getsize(rig_out)/1024:.1f} KB")

build_topple_glbs()

# 3. 合成 Octane 三蹦子分材质版 GLB (将 Body 与 Chassis 按 UV 遮罩拆分为 6 个独立材质分类)
def build_octane_tricycle_glb():
    sk_path = "/tmp/work/exports_bodiesV2/Body_Octane_SF/Body_Octane_SF/SkeletalMesh3/Body_Octane_PremiumSkin_SK.gltf"
    rgb_path = "/tmp/work/exports_bodiesV2/Body_Octane_SF/Body_Octane_SF/Texture2D/Body_Octane_Bevel_RGB.png"
    s = trimesh.load(sk_path)
    geoms = list(s.geometry.values())
    chassis_g, body_g = geoms[0].copy(), geoms[1].copy()
    chassis_g.vertices = shift_vertices_to_three_wheels(chassis_g.vertices)
    body_g.vertices = shift_vertices_to_three_wheels(body_g.vertices)

    rgb_im = np.array(Image.open(rgb_path).convert("RGBA"))
    H, W = rgb_im.shape[:2]
    uv = body_g.visual.uv
    tri_uv = uv[body_g.faces].mean(axis=1) % 1.0
    px = np.clip((tri_uv[:, 0] * W).astype(int), 0, W - 1)
    py = np.clip((tri_uv[:, 1] * H).astype(int), 0, H - 1)
    samp = rgb_im[py, px]

    paint_mask = samp[:, 3] > 128
    glass_mask = (~paint_mask) & (samp[:, 2] > 140)
    trim_mask = (~paint_mask) & (~glass_mask)

    scene = trimesh.Scene()
    chassis_g.visual.material = trimesh.visual.material.PBRMaterial(
        name="01_Octane_Chassis_Metal",
        baseColorTexture=topple_chassis_tex,
        metallicFactor=0.78,
        roughnessFactor=0.38,
    )
    scene.add_geometry(chassis_g, node_name="01_Octane_Chassis_Metal")

    for sub_name, mask, btex, bcol, met, rough in [
        ("02_Octane_Body_Paint", paint_mask, topple_body_tex, [1.0, 1.0, 1.0, 1.0], 0.55, 0.28),
        ("03_Octane_Windshield_Glass", glass_mask, None, [0.08, 0.12, 0.18, 1.0], 0.92, 0.10),
        ("04_Octane_Trim_Plastic", trim_mask, None, [0.16, 0.17, 0.19, 1.0], 0.15, 0.62),
    ]:
        if mask.sum() == 0:
            continue
        sub_m = body_g.submesh([np.where(mask)[0]], append=True)
        sub_m.visual.material = trimesh.visual.material.PBRMaterial(
            name=sub_name,
            baseColorTexture=btex,
            baseColorFactor=bcol,
            metallicFactor=met,
            roughnessFactor=rough,
            doubleSided=True,
        )
        scene.add_geometry(sub_m, node_name=sub_name)

    out_p = os.path.join(OUT_DIR, "models/tricycle_cars/Octane_Tricycle_ThreeWheel.glb")
    scene.export(out_p, file_type="glb")
    print(f"-> 生成 Octane_Tricycle_ThreeWheel.glb: {os.path.getsize(out_p)/1024:.1f} KB")

build_octane_tricycle_glb()

# 4. 导出 Mutators_Balls_SF 全部特殊球体为带贴图的 GLB
ball_tex_map = {
    "Ball_DefaultBall00": ("Ball_Default00_D.png", [0.82, 0.84, 0.88, 1.0], 0.45, 0.38),
    "Ball_Soccer_SM": ("SoccerBall_D.png", [0.95, 0.95, 0.95, 1.0], 0.1, 0.55),
    "ball_adidas_sm": ("ball_adidas_d.png", [0.95, 0.95, 0.95, 1.0], 0.15, 0.45),
    "Ball_Nike_SM": ("NikeBall_D.png", [0.95, 0.95, 0.95, 1.0], 0.2, 0.45),
    "Ball_LuminousAirplane_SM": ("ball_luminousairplane_d.png", [0.95, 0.95, 0.95, 1.0], 0.3, 0.4),
    "Ball_SphereGulp_SM": ("Ball_SphereGulp_D_2k.png", [1.0, 1.0, 1.0, 1.0], 0.15, 0.45),
    "GodBall_RL_SM": ("Ball_Default00_D.png", [0.65, 0.35, 1.0, 1.0], 0.6, 0.25),
    "Ball_CubeBall_SM": ("Ball_CubeBall00_D.png", [0.85, 0.85, 0.88, 1.0], 0.4, 0.4),
    "PumpkinCube2_SM": ("Ball_PumpkinCube_D.png", [1.0, 0.52, 0.12, 1.0], 0.05, 0.75),
    "Ball_Basketball_SM": ("Ball_Basketball_D.png", [0.92, 0.42, 0.14, 1.0], 0.05, 0.78),
    "Ball_Beachball_SM": ("Ball_Beachball_D.png", [1.0, 1.0, 1.0, 1.0], 0.05, 0.25),
    "Football_06_SM": ("Weave_D.png", [0.48, 0.26, 0.14, 1.0], 0.1, 0.7),
    "HockeyPuck_SM": ("HockeyPuck_D.png", [0.15, 0.16, 0.18, 1.0], 0.1, 0.65),
    "PizzaCheezyPuck_SM": ("ball_pizza_cheese_d.png", [1.0, 0.78, 0.28, 1.0], 0.05, 0.65),
    "Ball_Breakout_SM": ("Ball_Breakout_D.png", [0.35, 0.75, 1.0, 1.0], 0.55, 0.3),
    "eggball_sm": ("eggball_RGBA.png", [0.95, 0.92, 0.85, 1.0], 0.1, 0.5),
}

ball_sdir = "/tmp/work/exports_skybox33/Mutators_Balls_SF/Mutators_Balls_SF/StaticMesh3"
ball_tdir = "/tmp/work/exports_skybox33/Mutators_Balls_SF/Mutators_Balls_SF/Texture2D"
for bname, (tfile, bcol, met, rough) in ball_tex_map.items():
    gp = os.path.join(ball_sdir, f"{bname}.gltf")
    if not os.path.exists(gp):
        continue
    m = trimesh.load(gp)
    tp = os.path.join(ball_tdir, tfile)
    im = Image.open(tp).convert("RGB").resize((512, 512), Image.Resampling.BICUBIC) if os.path.exists(tp) else None
    geoms = list(m.geometry.values()) if isinstance(m, trimesh.Scene) else [m]
    sc = trimesh.Scene()
    for idx, g in enumerate(geoms):
        g.visual.material = trimesh.visual.material.PBRMaterial(
            name=f"{bname}_Mat_{idx}",
            baseColorTexture=im,
            baseColorFactor=bcol,
            metallicFactor=met,
            roughnessFactor=rough,
        )
        sc.add_geometry(g, node_name=f"{bname}_{idx}")
    out_p = os.path.join(OUT_DIR, "models/mutator_balls", f"{bname}.glb")
    sc.export(out_p, file_type="glb")

# 5. 导出 Mutators_Items_SF 道具模型为带贴图的 GLB
item_tex_map = {
    "Items_BoxingGlove2_SM": ("Items_BoxingGlove_D2.png", [0.92, 0.18, 0.15, 1.0]),
    "Items_BoxingGloveB_SM": ("Items_BoxingGloveB_D2.png", [0.22, 0.25, 0.30, 1.0]),
    "Items_Boot_SM": ("HAT_boot_D.png", [0.55, 0.35, 0.18, 1.0]),
    "Items_Plunger_SM": ("HAT_plunger_D.png", [0.85, 0.22, 0.20, 1.0]),
    "Items_Hammer_SM": ("Hammer_D.png", [0.55, 0.58, 0.62, 1.0]),
    "Batarang_SM": ("Batarang_D.png", [0.20, 0.22, 0.25, 1.0]),
    "Items_Spikes_01": (None, [0.75, 0.78, 0.82, 1.0]),
    "clayspikes_sm": ("clayspikes_d.png", [0.68, 0.55, 0.42, 1.0]),
    "Spring02": (None, [0.78, 0.80, 0.85, 1.0]),
}
item_sdir = "/tmp/work/exports_skybox33/Mutators_Items_SF/Mutators_Items_SF/StaticMesh3"
item_tdir = "/tmp/work/exports_skybox33/Mutators_Items_SF/Mutators_Items_SF/Texture2D"
for iname, (tfile, bcol) in item_tex_map.items():
    gp = os.path.join(item_sdir, f"{iname}.gltf")
    if not os.path.exists(gp):
        continue
    m = trimesh.load(gp)
    im = Image.open(os.path.join(item_tdir, tfile)).convert("RGB").resize((512, 512), Image.Resampling.BICUBIC) if tfile and os.path.exists(os.path.join(item_tdir, tfile)) else None
    geoms = list(m.geometry.values()) if isinstance(m, trimesh.Scene) else [m]
    sc = trimesh.Scene()
    for idx, g in enumerate(geoms):
        g.visual.material = trimesh.visual.material.PBRMaterial(
            name=f"{iname}_Mat_{idx}",
            baseColorTexture=im,
            baseColorFactor=bcol,
            metallicFactor=0.35,
            roughnessFactor=0.45,
        )
        sc.add_geometry(g, node_name=f"{iname}_{idx}")
    sc.export(os.path.join(OUT_DIR, "models/mutator_items", f"{iname}.glb"), file_type="glb")

# 6. 生成完整三蹦子与愚人节 LTM 元数据 JSON
tricycle_meta = {
    "mode_name": "Three-Wheeler Mode (三蹦子模式 / Confidential_ThirdWheel_Test / April Fools LTM)",
    "packages": {
        "car_body_package": "body_topple_SF.upk",
        "car_thumbnail_package": "Body_Topple_T_SF.upk",
        "ltm_gameinfo_package": "GameInfo_LTM_AprilFool_SF.upk",
        "mutators_package": "Mutators_SF.upk",
        "mutator_balls_package": "Mutators_Balls_SF.upk",
        "mutator_items_package": "Mutators_Items_SF.upk",
    },
    "mutator_loadout_tritip": {
        "export_name": "Tritip",
        "class": "Mutator_Loadout_TA",
        "forced_products": ["body_tritip (ProductAsset_Body_TA'body_topple_SF.Body_Topple', ProductID=12314)"],
    },
    "body_topple_parameters": {
        "product_id": 12314,
        "skeletal_mesh": "Body_Topple_SK",
        "handling_preset": 100,
        "hitbox_rb_bodysetup_uu": {
            "length_x": 118.495,
            "width_y": 83.2725,
            "height_z": 36.3,
            "offset": {"x": 13.97567, "y": 0.0, "z": 20.75499},
        },
        "front_axle": {
            "wheel_radius": 14.5,
            "wheel_width": 14.0,
            "wheel_mesh_offset_side": 2.0,
        },
        "back_axle": {
            "wheel_radius": 16.5,
            "wheel_width": 15.5,
            "wheel_mesh_offset_side": 3.0,
            "wheel_PivotOffset": 1.0,
        },
        "chassis_spring": {
            "max_displacement": {"x": 2.5, "y": 2.5, "z": 5.0},
            "spring_constant": {"x": 300.0, "y": 300.0, "z": 250.0},
            "max_rotation_deg": {"pitch": 6.0, "yaw": 1.5, "roll": 8.0},
        },
    },
    "rocketsim_psyclops_physics_config": {
        "preset_name": "CAR_CONFIG_PSYCLOPS",
        "hitbox_index_in_wasm": 6,
        "three_wheels": True,
        "hitbox_size_uu": [118.01, 84.2, 36.16],
        "hitbox_pos_offset_uu": [13.88, 0.0, 20.75],
        "front_wheels": {
            "wheel_radius": 12.50,
            "suspension_rest_length": 33.0,
            "connection_point_offset_uu": [51.25, 5.0, -0.65],
            "note": "横向偏移 Y 从标准 Octane 的 25.90f 大幅收窄至 5.00f（车头正中央单轮/并拢双轮支撑），极易侧倾翻车",
        },
        "back_wheels": {
            "wheel_radius": 13.50,
            "suspension_rest_length": 31.3,
            "connection_point_offset_uu": [-33.75, 29.5, -1.7],
        },
        "curves_and_forces": {
            "sticky_force_scale": 0.0,
            "steer_angle_from_speed_curve_threewheel": [
                [0.0, 0.40906],
                [500.0, 0.25461],
                [1000.0, 0.141965],
                [1500.0, 0.07519],
                [1750.0, 0.06097],
                [3000.0, 0.02685],
            ],
            "lat_friction_curve_threewheel": [
                [0.0, 1.0],
                [0.05, 0.3],
                [1.0, 0.1],
            ],
            "mutators_sf_wheel_test_override": {
                "lat_friction_curve": [[0.0, 2.0], [1.0, 0.4]],
                "handbrake_lat_friction_curve": [[0.0, 0.05]],
            },
        },
    },
}

with open(os.path.join(OUT_DIR, "metadata/tricycle_aprilfool_ltm_config.json"), "w") as fp:
    json.dump(tricycle_meta, fp, indent=2, ensure_ascii=False)
print("已生成 metadata/tricycle_aprilfool_ltm_config.json")
