# RLMaps - Driftwoods Arena 场景复原工程

本仓库致力于对《火箭联盟》（Rocket League）经典竞技场场地（Driftwoods / 漂流木）进行 100% 比特级（Bit-Exact）逆向解析、资源提取与原汁原味的三维场景全合成。

---

## 模型交付清单 (`models/`)

| 模型文件 | 包含内容 | 材质/贴图状态 | 文件大小 |
| :--- | :--- | :--- | :--- |
| **`Driftwoods_Day.glb`** | 全场景（含球场、外部森林、木屋、湖面、旧车等 711 个实例） | **完整嵌入漫反射贴图**（49张嵌入贴图） | ~39 MB |
| **`Driftwoods_Day_WhiteModel.glb`** | 全场景（711 个实例） | **纯几何白模（Clay Model）**，无贴图 | ~36 MB |
| **`Driftwoods_Field.glb`** | **仅包含 `Woods_Field*` 核心球场结构**（地面、球门、看台、围墙、坡道共 28 个实例） | **嵌入漫反射材质贴图** | ~1.3 MB |
| **`Driftwoods_Field_WhiteModel.glb`** | **仅包含 `Woods_Field*` 核心球场结构**（28 个实例） | **纯几何白模（Clay Model）**，无贴图 | ~1.3 MB |

---

## 目录结构

```
RLMaps/
├── models/
│   ├── Driftwoods_Day.glb              # 全场景 1:1 GLB 模型（带完整嵌入贴图）
│   ├── Driftwoods_Day_WhiteModel.glb   # 全场景 1:1 GLB 白模（纯几何体）
│   ├── Driftwoods_Field.glb            # 仅包含 Woods_Field* 前缀的球场主体核心结构（带贴图）
│   └── Driftwoods_Field_WhiteModel.glb # 仅包含 Woods_Field* 前缀的球场主体白模
├── raw/
│   └── Woods_P/                        # 从 Woods_P.upk 提取的原版离散资源
│       ├── StaticMesh3/                # 126 个原始 glTF 2.0 网格体与 .bin 数据文件
│       ├── Texture2D/                  # 181 张原版 PNG 材质贴图（漫反射、法线、遮罩）
│       ├── Material3/                  # 53 个材质定义文件
│       ├── MaterialInstanceConstant/   # 68 个材质实例参数定义文件
│       └── LightMapTexture2D/          # 20 张光照烘焙贴图
├── metadata/
│   ├── driftwoods_day_scenegraph.json  # 760 个物体组件的完整空间位姿、缩放、层级与材质映射元数据
│   └── driftwoods_analysis_report.md   # 日夜版本对比、场景对称拼装、着色器动态参数技术分析报告
└── tools/
    ├── synthesize_scene.py             # 自动化装配生成上述 4 款 GLB 的 Python 管线脚本
    └── rl_umodel_patch.diff            # 适配 Rocket League UPK 36字节块头与元数据导出的 UModel C++ 补丁
```

---

## 核心成果与技术特性

1. **`Woods_Field` 核心场地纯净结构**：
   - 过滤了外部所有大型湖面、森林低模树木、远景广告牌及废旧车辆，专注于竞技场主体结构。
   - 包含对称布置的木质看台（`Woods_Field_Bleachers_01/02`）、球门框架与球网（`Woods_Field_Goal` / `Posts` / `Net`）、四角弧形坡道（`Woods_Field_Ramps`）、六边形防护网（`Woods_Field_Walls_Hexes`）及地面草皮。
2. **严谨的数学坐标系对齐**：
   - 严格遵循从虚幻引擎左手系厘米坐标到 glTF 右手系米级坐标的仿射变换：
     $$M_{\text{glTF}} = C \cdot M_{\text{UE}} \cdot C^{-1}$$
     保证导出的每个局部网格体顶点位姿 100% 比特精确。
3. **白模与贴图双重输出**：
   - 白模版本（`*_WhiteModel.glb`）：适合导入建模软件进行拓扑分析、二次修改、碰撞检测或物理网格烘焙。
   - 贴图版本（`*.glb`）：直接将原版漫反射材质打包进入 glTF buffer，可直接在 3D 查看器、游戏引擎（Three.js、Babylon.js、Godot、Blender）中开箱即用。
