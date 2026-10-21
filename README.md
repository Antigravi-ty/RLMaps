# Rocket League 天空盒、球场材质贴图与 Forbidden Temple（禁忌神庙）全量资产库

本分支（`skybox-and-forbidden-temple`）专门用于存放从 `Skybox.zip`（共 36 个 `.upk` 包）中完整解密、解包与重建的 **全地图天空盒（Skybox）**、**球场地面/草坪材质贴图**、**地图 UI 预览图（MapImage）** 以及 **Forbidden Temple (Day)（禁忌神庙-日间版）1:1 全场景 GLB 模型与原始资产/Metadata**。

> **一键下载提示**：点击 GitHub 页面右上角的 `Code -> Download ZIP`（或直接访问分支归档下载链接）即可一次性下载本分支的全部 GLB 模型、贴图与元数据，不包含主分支的历史其他地图文件。

---

## 一、 仓库目录结构

```text
├── models/                                            # Forbidden Temple (Day) 合成 3D 模型 (GLB)
│   ├── ForbiddenTemple_Day.glb                        # 1:1 完整全场景模型（含 4096x1024 天空球、球场、长城、神庙建筑群、樱花树与群山，26.69 MB）
│   ├── ForbiddenTemple_Day_WhiteModel.glb             # 1:1 完整全场景几何白模（22.57 MB）
│   ├── ForbiddenTemple_Field.glb                      # 核心球场模型（含高清重建草坪标线、球门、石桥、龙凤浮雕、加速垫与半透力场罩，6.68 MB）
│   └── ForbiddenTemple_Field_WhiteModel.glb           # 核心球场几何白模（5.21 MB）
├── skyboxes_and_textures/                             # 按用途与球场分类整理的图片资产 (.png)
│   ├── 01_Skyboxes/                                   # 全部球场的天空盒全景图、云层贴图、渐变曲线图 (Curve)、太阳光晕与 6 面环境立方体贴图 (Cubemap)
│   ├── 02_Ground_and_Field_Textures/                  # 全部球场的地面草皮、2048x2048 未压缩标线贴图 (Unfiltered)、泥土/石板与地面光照图 (FloorLightMap)
│   ├── 03_MapImages_UI_Previews/                      # 从 12 个 *_MapImage_SF.upk 提取的 2048x1024 官方地图高清预览横幅
│   └── 04_All_Other_Map_Textures/                     # 其他球场包中提取的全部环境贴图与材质属性定义 (.mat / .props.txt)
├── raw/
│   └── Forbidden_Temple/                              # Forbidden Temple 5 个 UPK 包的 100% 原始导出资产
│       ├── CHN_Stadium_Day_P/                         # 主持久关卡原始资产 (StaticMesh3, Texture2D, Material3, MaterialInstanceConstant, LightMapTexture2D)
│       ├── CHN_Stadium_Day_Field/                     # 赛场核心几何与材质原始资产
│       ├── CHN_Stadium_Day_OOB/                       # 赛场外围建筑群/长城/樱花树原始资产
│       ├── CHN_Stadium_Day_Mountains/                 # 远景群山与云雾原始资产
│       └── chn_stadium_day_p_MapImage_SF/             # 地图 UI 缩略图原始资产
├── metadata/                                          # 场景图与材质/包结构元数据
│   ├── forbidden_temple_day_scenegraph.json           # 跨 4 个子关卡合并的 836 个组件实例完整坐标、旋转、缩放与材质槽映射
│   ├── forbidden_temple_materials_metadata.json       # 111 个 Forbidden Temple 材质的完整着色器参数 (DiffuseColor, Goldlief, 纹理槽与混合模式)
│   ├── upk_package_inventory.json                     # 36 个 UPK 包的版本、AES 密钥索引与导出资产统计清单
│   └── scene_dumps/                                   # 各 UPK 关卡的原始 Actor/Component 属性导出 JSON
└── tools/                                             # 自动化合成脚本与定制 UModel 补丁
    ├── synthesize_forbidden_temple.py                 # 禁忌神庙场景图生成、通道遮罩色彩烘焙与 GLB 合成脚本
    └── rl_umodel_patch.diff                           # 支持多密钥 AES 解密、v32/v34 压缩块跨距自适应及字节对齐属性扫描的 UEViewer (UModel) 补丁
```

---

## 二、 核心交付物说明

### 1. Forbidden Temple（禁忌神庙-日间版）GLB 模型与 Metadata
Forbidden Temple 采用虚幻引擎 3 的多关卡流式加载（Level Streaming）架构，完整场景由 4 个 `.upk` 共同组成：
- `CHN_Stadium_Day_P.upk`（主持久关卡：天空盒 `SM_SkySphere`、6 个大加速垫 + 3 组小加速垫、16 个力场笼架与半透明力场墙/顶棚、石狮 `CHN_Fudog_SM`、外围步道与城门底座）
- `CHN_Stadium_Day_Field.upk`（球场核心结构：草坪基底 `Grass_Base`、球门 `CHN_Field_Goal`、坡道 `CHN_Field_QuarterPipeSides`、石桥 `CHN_GoalBridge01`、龙凤浮雕 `dragon_relief_SM` / `Phoenix_relief_SM`、莲花/龙珠金饰牌匾）
- `CHN_Stadium_Day_OOB.upk`（场外古建筑群：7 座大型宫殿/阁楼 `CHN_OOB_Building02..07_CMB`、长城城墙与烽火台 `CHN_StadiumWalls01..04` / `CHN_StadiumGuardTower02`、牌坊大门 `CHN_GateLarge01`、樱花树 `CHN_PeachBlossom_Final_LOD`、睡莲、战鼓与旗帜）
- `CHN_Stadium_Day_Mountains.upk`（远景群山：桂林喀斯特风格山峰 `DigletMountain_02_SM` / `CHN_Mountain_LOD`、远景地形 `DBO_Terrain_Mountains_NoGround`、远景阁楼 `CHN_OOB_Building08..11_CMB` 以及复活节石像彩蛋 `AT_Moai_SM`）

> **材质色彩烘焙说明**：禁忌神庙中的绝大多数建筑与场地材质派生自 `MAT_CHN_Stadium_Master`，其原始 `*_RGB.png` 贴图实际上是**通道打包遮罩图**（G 通道为明暗 AO，R/B 通道为双色混合权重），真实颜色由材质实例中的 `DiffuseColor` 与 `Goldlief` 向量参数在着色器中动态混合。`tools/synthesize_forbidden_temple.py` 完整解析了 `metadata/forbidden_temple_materials_metadata.json` 中的全部向量参数，将朱红木漆、鎏金雕花、青砖长城、碧玉栏杆与粉色樱花树冠准确烘焙进了 GLB 模型的 PBR 贴图中。

### 2. 全地图天空盒（Skybox）与球场地面贴图清单
- **全景天空盒大图（4096×1024 / 4096×2048，自带完整高清分辨率）**：
  - **Forbidden Temple Day**：`Beach_Clouds_01.png` (`4096×1024`)
  - **Farmstead (Standard/Dusk)**：`Sky_T7.png` (`4096×2048`)
  - **Mannfield Dusk (`EuroStadium_Dusk_P`)**：`CHN_Sky3.png` (`4096×1024`) 及叠加黄昏色调参数后的 `CHN_Sky3_EuroStadium_Dusk_Tinted.png` (`4096×1024`)
- **程序化天穹（SkyDome）+ 云层 + 渐变曲线 + 6 面环境 Cubemap**：
  - **Champions Field (`CS_P`, `CS_Day_P`)**：`SkyClouds02_T.png`、`Curve_CSNight.png`、`Corona_Sun01_D.png`、`CubemapFace0..5.png`
  - **Beckwith Park (`Park_P`, `Park_Night_P`, `Park_Rainy_P`)**：`Clouds_01.png`、`ENV_PartlyCloudy.png`、`Curve_ParkNight.png`、`Park_Day_LensFlare_D.png`、`CubemapFace0..5.png`
  - **Mannfield (`EuroStadium_P`, `EuroStadium_Night_P`, `EuroStadium_Rainy_P`)**：`Clouds_01.png`、`ENV_PartlyCloudy.png`、`Curve_Dusk_01.png`、`Curve_ParkNight.png`、`Sun_Glow_001_D.png`、`CubemapFace0..5.png`
  - **Farmstead Night (`Farm_Night_P`)**：`Cloud_Card_00_D.png`、`Smoke_ Wispy_01_D.png`、`CubemapFace0..5.png`
- **球场地面/草皮高清贴图（2048×2048 Unfiltered 等）**：
  - `FieldPattern_Classic_1x1_Unflitered.png` (`2048×2048`，Mannfield 标准球场完整草皮与白线贴图)
  - `FieldSkin_Park_1x1_Unfiltered.png` (`2048×2048`，Beckwith Park 球场完整草皮与白线贴图)
  - `CHN_FieldGrassPattern_Day_Reconstructed_2048.png` (`2048×2048`，结合禁忌神庙草坪条纹色、地面光照图与 2048 高清标线合成的球场地面贴图)
  - 各球场原始草皮/泥土/砖石贴图：`CHN_FieldGrassPattern_Day_D.png`、`CS_FieldGrassPattern_D.png`、`FieldPattern_Euro_Rainy_1x1.png`、`Grass_1x1_D.png`、`Farm_Dirt_02_D.png`、`Farm_Mud_00_D.png`、`FloorLightMap.png` 等。

---

## 三、 常见后缀包（`MapImage_SF`、`OOB`、`Field`、`Grounds`、`Lights`）详解

在《Rocket League》（基于 Unreal Engine 3 开发）的 CookedPCConsole 目录中，一张地图往往被拆分为多个带后缀的 `.upk` 文件：

1. **`*_P.upk`（Persistent Level / 主持久关卡包）**
   - `_P` 代表 **Persistent Level（主关卡）**。它是进入地图时首先加载的根关卡文件，包含世界物理边界（防穿模碰撞盒 `Field_STD_Collision`）、出生点、加速垫（Boost Pads）、主天空盒（SkySphere/SkyDome）以及管理其他子关卡流式加载的 `WorldInfo.StreamingLevels` 列表。
2. **`*_MapImage_SF.upk`（Scaleform UI 地图缩略图包）**
   - `_MapImage` 指地图预览图，`_SF` 代表 **Scaleform GFx**（Rocket League 早期和主菜单 UI 使用的 Flash/Scaleform 界面中间件）。
   - 这些包**不包含任何 3D 模型**，每个包里只有一张 `2048×1024` 分辨率的高清 2D 贴图（统一命名为 `MapImage`），用于在比赛匹配加载界面、主菜单地图选择界面和自定义比赛列表里展示该球场的宣传预览图（已全部提取至 `skyboxes_and_textures/03_MapImages_UI_Previews/`）。
3. **`*_OOB.upk` / `*_OOB2.upk` / `*_OOBTerrain.upk`（Out Of Bounds / 场外远景环境子关卡）**
   - `OOB` 是 **Out Of Bounds（界外/赛场外部区域）** 的缩写。
   - 在《Rocket League》中，玩家车辆只能在透明力场笼（Arena Cage）内部活动，笼子外面所有看台、宫殿建筑、长城、摩天轮、森林、谷仓、远山等纯视觉背景都放在 `_OOB` 子关卡中。这样游戏可以根据画质设置（如世界细节度 World Detail）独立控制场外景物的加载与裁剪，不影响场内物理帧率。
4. **`*_Field.upk` / `*_Grounds.upk` / `*_Lights.upk` / `*_Mountains.upk`（模块化流式子关卡）**
   - **`_Field`**：专用于存放核心球场地面草皮、球门框、圆角坡道（QuarterPipe）和场内装饰浮雕。
   - **`_Grounds`**：专用于存放球场外围紧邻的地面、观众席底座、周边草地（例如冠军球场 `CS_Day_Grounds.upk`）。
   - **`_Lights`**：专用于存放大型球场的聚光灯架、体积光束（LightCones）和灯光贴图（例如 `CS_Lights.upk`、`CS_Day_Lights.upk`）。
   - **`_Mountains`**：专用于存放极远处的背景群山和云雾面片（例如 `CHN_Stadium_Day_Mountains.upk`）。

---

## 四、 当前压缩包中缺失/可补充的文件说明

经对 `Skybox.zip`（共 36 个 `.upk` 文件）的完整扫描对比，以下文件尚未包含在本次压缩包内（如需提取可随时补充上传）：

1. **Core 707（七零七核心 / Dropshot 掉落模式）**：
   - 列表中提到的 `ShatterShot_P.upk`（以及对应的 `ShatterShot_*` 子包）未包含在 `Skybox.zip` 中。
2. **Forbidden Temple 标准/黄昏版**：
   - 本次压缩包内包含的是日间版全套（`CHN_Stadium_Day_P.upk` 等 5 个包），不包含标准/黄昏版 `CHN_Stadium_P.upk`。
3. **Champions Field 夜间版的场地子包与 Farmstead 白天版的地形子包**：
   - `CS_P.upk`（冠军球场夜间版）引用了子关卡 `CS_Field.upk` 和 `CS_Grounds.upk`（未在包内，不过日间版 `CS_Day_Field.upk` 和 `CS_Day_Grounds.upk` 已在包内并已完整提取）。
   - `Farm_P.upk`（农场标准版）引用了子关卡 `Farm_OOBTerrain.upk`、`Farm_OOBProps.upk`、`Farm_Field.upk`（包内目前只有夜间版 `Farm_Night_OOBTerrain.upk`）。
4. **全局纹理缓存文件 `Textures*.tfc`（Texture File Cache）**：
   - 在 UE3 的 `CookedPCConsole` 目录中，部分带流式 Mipmap 的贴图会将高分辨率层级（如 1024×1024 / 2048×2048）统一存储在同目录的 **`Textures.tfc` ~ `Textures7.tfc`（或 `CharTextures.tfc`）** 文件中，而在 `.upk` 内部仅保留 `64×64` 的基础 Miptail（除非该贴图被标记为 `Unfiltered` 或无外部 TFC 引用，如本次已完美提取的 `4096×1024` 天空盒、`2048×2048` 球场标线图、`2048×1024` MapImage 等）。如果您手头有 `CookedPCConsole` 目录下的 `*.tfc` 文件，传过来后即可将剩余 `64×64` 的细节贴图也全部还原为最高分辨率。
