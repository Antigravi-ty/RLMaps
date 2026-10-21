# Throwback Stadium（SARPBC 怀旧球场）& Throwback Hockey 完整全量资产与物理碰撞库 (`throwback-stadium`)

本分支专门用于存放从 `ThrowbackStadium_P.upk`、`ThrowbackStadium_Field.upk`、`ThrowbackStadium_OOB.upk`、`throwbackstadium_p_MapImage_SF.upk` 以及冰球版 `ThrowbackHockey_*`（共 8 个 `.upk` 包）中完整解密、解包与 1:1 合成的 **Throwback Stadium（SARPBC 怀旧球场）全场景 GLB 模型**、**RocketSim 专用 `.cmf` 物理碰撞网格文件**、**2048×2048 重建高清草坪标线贴图**、**精确物理配置参数（独立球门 3D GoalVolume、44 个加速垫、出生点）** 与 **100% 原始导出资产**。

---

## 一、 仓库目录结构

```text
├── models/                                            # 1:1 合成 3D 模型 (.glb)
│   ├── ThrowbackStadium.glb                           # 怀旧球场 1:1 完整全场景带材质模型（含天空穹顶、2048 草坪、独立球门、看台、旗帜、城市与远山，18.41 MB）
│   ├── ThrowbackStadium_WhiteModel.glb                # 怀旧球场 1:1 完整全场景几何白模（15.83 MB）
│   ├── ThrowbackStadium_Field.glb                     # 怀旧球场核心赛场带材质模型（含草坪、独立球门、力场笼架、加速垫与场边广告牌，3.13 MB）
│   ├── ThrowbackStadium_Field_WhiteModel.glb          # 怀旧球场核心赛场几何白模（1.92 MB）
│   ├── ThrowbackStadium_Collision.glb                 # 怀旧球场 36 个物理碰撞网格可视化组装模型（球门橙色、斜坡圆角绿色、边界墙蓝色）
│   ├── ThrowbackHockey.glb                            # 怀旧冰球场（Snow Day）1:1 完整全场景带材质模型（16.78 MB）
│   └── ThrowbackHockey_Field.glb                      # 怀旧冰球场核心冰面赛场带材质模型（1.77 MB）
├── collision_meshes/                                  # 直接供 RLCleanWASM / RocketSim 加载的二进制碰撞网格 (.cmf)
│   ├── throwback_stadium/                             # ThrowbackStadium_P 的 36 个精确碰撞网格 (mesh_0.cmf ~ mesh_35.cmf + manifest.json)
│   └── throwback_hockey/                              # ThrowbackHockey_P 的 4 个合并碰撞网格 (mesh_0.cmf ~ mesh_3.cmf + manifest.json)
├── skyboxes_and_textures/                             # 按类别整理的贴图与重建高清资产 (.png)
│   ├── 01_Skyboxes_and_Cubemaps/                      # Throwback_SkyDome_Reconstructed_2048x1024.png、ENV_PartlyCloudy.png、CubemapFace0..5.png 等
│   ├── 02_Ground_and_Ice_Textures/                    # FieldPattern_LongField_Reconstructed_2048.png (2048x2048 重建草坪标线)、Unfiltered 原始图与冰面贴图
│   ├── 03_MapImages_UI_Previews/                      # throwbackstadium_p__MapImage.png & throwbackhockey_p__MapImage.png (2048x1024)
│   └── 04_Banners_Flags_and_Props/                    # CountryFlagsCombined.png (2048x1024)、Logo_RocketLeague.png、Flag_10yr.png 等
├── metadata/                                          # 场景图、材质与物理核心参数 JSON
│   ├── throwback_stadium_physics_config.json          # 独立球门 3D GoalVolume 包围盒、全部 44 个加速垫 (8大36小) 与 9 个出生点的精确坐标
│   ├── throwback_stadium_scenegraph.json              # Throwback Stadium 跨 3 个子关卡共 583 个组件实例完整世界变换与材质映射
│   ├── throwback_hockey_scenegraph.json               # Throwback Hockey 跨 3 个子关卡共 262 个组件实例完整世界变换与材质映射
│   ├── throwback_stadium_materials_metadata.json      # 全部材质着色器参数定义
│   └── scene_dumps/                                   # 8 个 UPK 包的完整 Actor / Component 属性转储 JSON
├── raw/                                               # 8 个 UPK 包的 100% 原始导出文件 (StaticMesh3, Texture2D, Material3, MaterialInstanceConstant)
│   ├── Throwback_Stadium/
│   └── Throwback_Hockey/
└── tools/
    └── synthesize_throwback_stadium.py                # 自动化场景合成、草坪标线重建与 .cmf 碰撞网格导出脚本
```

---

## 二、 怀旧球场（Throwback Stadium）核心物理参数（提取自 `ThrowbackStadium_P.upk`）

与标准球场（底线在 `Y = ±5120`，球门嵌在底墙内，共 34 个氮气垫）不同，Throwback Stadium 复刻了前作《SARPBC》的经典长球场设计：**球门作为独立实体立在场地内部，球门后方有宽敞的开放通道，底墙延伸至 `Y = ±6912`**。

### 1. 场地与独立球门 3D 进球判定体积 (`GoalVolume_TA`)
- **场地物理边界（Unreal Units 厘米）**：
  - `X ∈ [-4096.0, +4096.0]`
  - `Y ∈ [-6912.0, +6912.0]`（比标准场长 `1792 UU`）
  - `Z ∈ [0.0, +2048.0]`
- **独立球门进球触发盒 (`GoalVolume_TA_0` 橙方 / `GoalVolume_TA_1` 蓝方)**：
  - 横向宽度：`X ∈ [-960.0, +960.0]`
  - 纵向深度：`|Y| ∈ [4909.31, 5757.31]`（球门前线位于 `|Y| = 4909.31`，球门后背位于 `|Y| = 5757.31`，球在 `|Y| > 5757.31` 的球门后方通道滚动时**不会**触发进球！）
  - 垂直高度：`Z ∈ [-64.0, +648.0]`

### 2. 氮气加速垫 (`VehiclePickup_Boost_TA`，共 44 个：8 大 + 36 小)
- **8 个大氮气垫 (`VehiclePickup_BoostPill`, `Z = 72.0`)**：
  - 中场两侧：`(-3584, 0, 72)`、`(+3584, 0, 72)`
  - 半场四角：`(-3072, -4096, 72)`、`(+3072, -4096, 72)`、`(-3072, +4096, 72)`、`(+3072, +4096, 72)`
  - **球门正后方大氮气**：`(0, -6512, 72)`、`(0, +6512, 72)`
- **36 个小氮气垫 (`VehiclePickup_BoostPad`, `Z = 70.0`)**：
  - 除场内常规列阵外，在两侧球门后方额外布置了 8 个小氮气垫：`(±1792, ±5776, 70)`、`(±920, ±6272, 70)`。
  - 完整坐标数组已保存在 `metadata/throwback_stadium_physics_config.json` 并已内置到 `TricycleCoreWASM` 的 `RLConst::ThrowbackStadium` 中。

---

## 三、 如何在 `RLCleanWASM` 中启用 Throwback Stadium？

1. **替换或新增碰撞网格 (`.cmf`)**：
   - 将本分支 `collision_meshes/throwback_stadium/` 下的 `manifest.json` 和 `mesh_0.cmf ~ mesh_35.cmf` 放入 `RLCleanWASM/public/custom/arenamesh_throwback/`（或直接替换 `custom/arenamesh/`）。
   - 注意：RocketSim 的 `.cmf` 顶点单位为 **Bullet Units (`1 BT = 50 UU`)**，且顶点已去重、三角面法线统一朝向场内，本分支生成的 `.cmf` 已 100% 遵循该规范。
2. **加载视觉模型 (`ThrowbackStadium.glb` 或 `ThrowbackStadium_Field.glb`)**：
   - 在前端 Three.js 场景中加载 `models/ThrowbackStadium.glb`（完整场景）或 `models/ThrowbackStadium_Field.glb`（轻量核心赛场）。
3. **调用 `TricycleCoreWASM` 预设接口**：
   - 在调用 `module._physics_init(...)` 之前，先调用 `module._physics_setArenaPreset(1)`（`1 = Throwback Stadium`），WASM 物理核心会自动切换为 3D `GoalVolume` 进球检测、44 个怀旧球场氮气垫坐标与怀旧球场开球出生点。
