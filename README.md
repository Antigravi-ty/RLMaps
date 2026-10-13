# RLMaps - Driftwoods Arena 场景复原工程

本仓库致力于对《火箭联盟》（Rocket League）经典竞技场场地（Driftwoods / 漂流木）进行 100% 比特级（Bit-Exact）逆向解析、资源提取与原汁原味的三维场景全合成。

---

## 模型交付清单 (`models/`)

| 模型文件 | 包含内容 | 材质/贴图状态 | 文件大小 |
| :--- | :--- | :--- | :--- |
| **`Driftwoods_Day.glb`** | 全场景（含球场、外部森林、木屋、湖面、旧车等 711 个实例） | **完整嵌入漫反射贴图**（含 2048x2048 高清地面，51张嵌入贴图） | ~39.4 MB |
| **`Driftwoods_Day_WhiteModel.glb`** | 全场景（711 个实例） | **纯几何白模（Clay Model）**，无贴图 | ~36.3 MB |
| **`Driftwoods_Field.glb`** | **仅包含 `Woods_Field*` 核心球场结构**（地面、球门、看台、围墙、坡道共 27 个主体实例，排除重复 LOD 地面） | **嵌入 2048x2048 高清地面纹理、半透明力场网与 PBR 金属/木纹/发光材质** | ~1.7 MB |
| **`Driftwoods_Field_WhiteModel.glb`** | **仅包含 `Woods_Field*` 核心球场结构**（27 个实例） | **纯几何白模（Clay Model）**，无贴图 | ~1.3 MB |

---

## 目录结构

```
RLMaps/
├── models/
│   ├── Driftwoods_Day.glb              # 全场景 1:1 GLB 模型（带高清地面与完整嵌入贴图）
│   ├── Driftwoods_Day_WhiteModel.glb   # 全场景 1:1 GLB 白模（纯几何体）
│   ├── Driftwoods_Field.glb            # 仅包含 Woods_Field* 前缀的球场主体核心结构（带 2048x2048 高清地面与半透力场贴图）
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

1. **`Woods_Field` 核心场地纯净结构与高清材质修正**：
   - 过滤了外部所有大型湖面、森林低模树木、远景广告牌及废旧车辆，专注于竞技场主体结构。
   - **高清地面纹理修正**：直接映射并嵌入虚幻 3 中全分辨率未压缩的 2048x2048 核心场地贴图（`Woods_FieldLines_D_Unfiltered.png`），修正了上一版本错误加载 64x64 流式缩略图的配置问题。
   - **材质与物理着色修正**：消除了旧脚本中将非木质模型（看台金属架、围墙立柱、球门网、力场网）错误回退为木纹的问题，准确配置了黑金属 PBR、透明蜂窝力场网（`ForcefieldHex.png`）与霓虹发光材质。
   - **消除 Z-Fighting**：移除了高度仅差 0.75cm 的远景 LOD 草地重叠层（`Woods_Field_Ground_LOD`），确保地面显示平整无闪烁。
2. **严谨的数学坐标系对齐**：
   - 严格遵循从虚幻引擎左手系厘米坐标到 glTF 右手系米级坐标的仿射变换：
     $$M_{\text{glTF}} = C \cdot M_{\text{UE}} \cdot C^{-1}$$
     保证导出的每个局部网格体顶点位姿 100% 比特精确。
3. **白模与贴图双重输出**：
   - 白模版本（`*_WhiteModel.glb`）：适合导入建模软件进行拓扑分析、二次修改、碰撞检测或物理网格烘焙。
   - 贴图版本（`*.glb`）：直接将原版漫反射材质打包进入 glTF buffer，可直接在 3D 查看器、游戏引擎（Three.js、Babylon.js、Godot、Blender）中开箱即用。
