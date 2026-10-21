# Core 707 (`ShatterShot_P`) & 补充 VFX 天空盒资源分支 (`core-707`)

本分支包含 **Core 707（七零七核心 / 掉落模式 Dropshot）** 的完整场景资产、140 块六边形可击碎地板砖（`BreakOutActor_Platform_TA`）精确世界坐标、1:1 合成的带材质/白模/碰撞体 `.glb` 3D 模型，以及新增补充的 **Forbidden Temple (Day/Dusk)** 与 **Farmstead** `_VFX.upk` 天空盒及环境特效资源。

---

## 1. 合成 3D 模型 (`models/`)

| 文件名 | 说明 | 包含实例数 |
| :--- | :--- | :---: |
| `models/Core707.glb` | **Core 707 完整全场景带材质模型**（含正六边形竞技场、外围铁笼、140 块蓝/橙阵营六边形地板砖、中场分隔带与场外科技建筑群） | 157 |
| `models/Core707_WhiteModel.glb` | **Core 707 完整全场景几何白模** | 157 |
| `models/Core707_Field.glb` | **Core 707 核心赛场带材质模型**（不含场外远景建筑群） | 147 |
| `models/Core707_Field_WhiteModel.glb` | **Core 707 核心赛场几何白模** | 147 |
| `models/Core707_Collision.glb` | **Core 707 物理碰撞体网格**（`BO_collision_03`、`BO_CenterPiece_02_COLL`、`FloorCollision_Plane`） | 8 |

---

## 2. 天空盒、贴图与环境 VFX (`skyboxes_and_textures/`)

- `skyboxes_and_textures/Core_707/`:
  - 天空盒网格：`SM_SkySphere.gltf`、`CloudPlane.gltf`、`BottomFogLines_SM.gltf`
  - 赛场与地板贴图：`BO_HexTiles_RGB.png`、`BO_HexTiles_N.png`、`BO_HexTiles_E.png`、`BO_Cage_RGBA.png`、`BO_Quarterpipe_RGB.png`、`BO_CenterStrip_RGBA.png`、`BO_OOB_Panel_D.png`、`ForceField.png`、`MapImage.png`
- `skyboxes_and_textures/Forbidden_Temple_Day_VFX/` (`CHN_Stadium_Day_VFX.upk`):
  - 天空太阳与云层：`SunPlane00.gltf`、`Cloud_T.png`
  - 6 面环境立方体贴图：`CubemapFace0.png` ~ `CubemapFace5.png`
  - 瀑布与水面网格/贴图：`CHN_Waterfall01..03.gltf`、`CHN_OOB_Water_01.gltf`、`Waterfall_T.png`、`WaterFall_Small_01.png`、`FlowerPedal.png`
- `skyboxes_and_textures/Forbidden_Temple_Dusk_VFX/` (`CHN_Stadium_VFX.upk`):
  - 标准/黄昏版禁忌神庙的太阳平面、云层贴图、6 面环境 Cubemap 与瀑布/水面特效资源。

---

## 3. 场景图与完整元数据 (`metadata/`)

- `metadata/core707_scenegraph.json`：包含 Core 707 跨 `ShatterShot_P`、`ShatterShot_OOB_Exploration`、`ShatterShot_VFX` 三个子关卡包的全部 157 个静态网格组件世界变换，以及 **140 块六边形地板砖 (`hex_tiles`) 的精确坐标、旋转与阵营归属**。
- `metadata/scene_dumps/*.upk_scene.json`：7 个 UPK 包的完整 Actor / Component / Material 属性树转储。
