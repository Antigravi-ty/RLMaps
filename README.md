# RLMaps - Driftwoods Arena 场景复原工程

本仓库致力于对《火箭联盟》（Rocket League）经典竞技场场地（Driftwoods / 漂流木）进行 100% 比特级（Bit-Exact）逆向解析、资源提取与原汁原味的三维场景全合成。

---

## 目录结构

```
RLMaps/
├── models/
│   └── Driftwoods_Day.glb           # 完整合成的日间版 1:1 GLB 场景模型（711个可见物体实例）
├── raw/
│   └── Woods_P/                     # 从 Woods_P.upk 提取的原版离散资源
│       ├── StaticMesh3/             # 126 个原始 glTF 2.0 网格体与 .bin 数据文件
│       ├── Texture2D/               # 181 张原版 PNG 材质贴图（漫反射、法线、遮罩）
│       ├── Material3/               # 53 个材质定义文件
│       ├── MaterialInstanceConstant/# 68 个材质实例参数定义文件
│       └── LightMapTexture2D/       # 20 张光照烘焙贴图
├── metadata/
│   ├── driftwoods_day_scenegraph.json  # 760 个物体组件的完整空间位姿、缩放、层级与材质映射元数据
│   └── driftwoods_analysis_report.md   # 日夜版本对比、场景对称拼装、着色器动态参数技术分析报告
└── tools/
    ├── synthesize_scene.py          # 自动化装配生成 Driftwoods_Day.glb 的 Python 管线脚本
    └── rl_umodel_patch.diff         # 适配 Rocket League UPK 36字节块头与元数据导出的 UModel C++ 补丁
```

---

## 核心成果与技术特性

1. **原汁原味 1:1 合成场景 (`Driftwoods_Day.glb`)**：
   - 包含场地内部（316块草皮、半场对称看台、坡道、球门框、大药包）及外部完整环境（森林松树、水上木屋、巨型湖泊、输电线杆、生锈旧车 OldOctane）。
   - 严格遵循从虚幻引擎左手系厘米坐标到 glTF 右手系米级坐标的仿射变换（$M_{\text{glTF}} = C \cdot M_{\text{UE}} \cdot C^{-1}$）。
   - 保留了几何体实例化引用（Instancing），模型加载轻量高效。
2. **完整元数据 (`metadata/driftwoods_day_scenegraph.json`)**：
   - 导出了 `PersistentLevel` 中全部 760 个组件实例，包含精确的世界位移 $(X, Y, Z)$、旋转角（Rotator Pitch/Yaw/Roll）、缩放以及关联的材质槽。
3. **动态材质与团队着色解析**：
   - 看台与护栏木材质通过遮罩贴图（`Woods_Wood_Basic_M`）支持蓝队（`TeamColor0`）与橙队（`TeamColor1`）动态染色。
   - 蜂窝能量防护网（`Woods_Field_Walls_Hexes`）支持距离衰减透明度动效。

---

## 关于夜间版 (`Woods_Night_P.upk`) 的说明

- `Woods_P.upk`（日版）使用标准主密钥解密成功并完全导出。
- `Woods_Night_P.upk`（夜版）使用了客户端运行期下发的动态 AES ContentKey（存放于客户端工具的 `keys.txt`）。
- 待提供夜间版动态密钥或解密后包体，本工具链可无缝一键提取并执行日夜版本的 SHA-256 哈希校验对比。
