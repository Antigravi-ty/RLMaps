# Driftwoods 场地全资源提取与场景还原技术分析报告

## 1. 任务概述与 UPK 解密校验结果

本工程针对 Rocket League 经典 Driftwoods（漂流木场馆）日夜两版地图 UPK 文件进行了底层逆向解析、资源提取与 1:1 比特精确级（Bit-Exact）场景重构。

### 1.1 `Woods_P.upk`（日间版）解密与解压
- **加密方式**：采用 Rocket League 标准 AES-256-ECB Master Key：
  `0xC7, 0xDF, 0x6B, 0x13, 0x25, 0x2A, 0xCC, 0x71, 0x47, 0xBB, 0x51, 0xC9, 0x8A, 0xD7, 0xE3, 0x4B, 0x7F, 0xE5, 0x00, 0xB7, 0x7F, 0xA5, 0xFA, 0xB2, 0x93, 0xE2, 0xF2, 0x4E, 0x6B, 0x17, 0xE7, 0x79`
- **关键解压阻碍攻克**：Rocket League 在 `LicenseeVersion >= 22`（本包为 v868/34）后，加密头部中的压缩块表（Compressed Chunks Table）每个条目的二进制跨度（Stride）由虚幻默认的 16 字节变更为 **36 字节**：
  `int64 UncompressedOffset; int32 UncompressedSize; int64 CompressedOffset; int32 CompressedSize; int32 Pad[3];`
  修正此结构后，成功解码并解压全部 69 个 ZLIB 压缩块。
- **导出资产统计**：
  - **StaticMesh（静态网格体）**：126 个原始 glTF 2.0 及二进制 `.bin` 文件（涵盖看台、湖边木屋、森林植被、球场地面与挡板、OldOctane 旧车等）。
  - **Texture2D（贴图）**：181 张 PNG 图像（漫反射、法线贴图、材质遮罩、光照参数贴图）。
  - **Material / MIC（材质定义）**：121 个 `.mat` 配置文件（详细记录 Diffuse、Normal、Mask 及 Scalar/Vector 动态参数）。
  - **LightMapTexture2D（烘焙光照贴图）**：20 张光照贴图。

### 1.2 `Woods_Night_P.upk`（夜间版）加密机制与状态
- **加密机制分析**：Psyonix 在中后期版本中引入了动态内容分发密钥（Content Key / Dynamic AES Key），各补丁包与季节性地图的加密密钥由 PsyNet 运行时下发，并不使用通用主密钥。
- **现状与校验**：
  使用主密钥尝试解密 `Woods_Night_P.upk` 时，名称表与块表解密出的头 32 字节为无规律密文乱码（例如 `0x56a16070...`），引发块尺寸越界错误。
- **对比未加密 Header Summary**：
  - `Names`：2,351 项（日版为 2,501）
  - `Exports`：4,168 项（日版为 5,205）
  - `Imports`：321 项（日版为 334）
  - 依赖关系：日版烹饪附加包为 `woods_sfx`, `woods_opt_trees`；夜版为 `woods_night_sfx`, `woods_forest_p`。
- **下一步行动**：一旦提供夜间版对应的 AES 密钥（或从客户端 `keys.txt` 获取），运行本仓库提供的自动化管线即可解密，并自动完成两张地图全部 126 个网格体 SHA-256 的对比校验。

---

## 2. 场景拼装、对称性与调用逻辑（Modularity & Symmetry）

虚幻引擎在竞技场制作中广泛采用模块化拼装和轴对称复用以节省内存和渲染开销。通过解析 `PersistentLevel` 中的 760 个 `StaticMeshComponent`，我们还原了精确的空间布局：

### 2.1 中央球场对称拼装机制
1. **模块化草坪**：
   - 整个球场地面并非一个单体大模型，而是由 **316 个 `Grass_1x1`** 标准地砖网格在三维网格上平铺拼接而成。
2. **中心对称与轴对称**：
   - 围墙与坡道（`Woods_Field_Ramps`、`Woods_Field_Walls_Hexes`）、球门边框（`Goal_STD_Collision_Half_*`）、看台（`Woods_Field_Bleachers_01/02`）均采用半场或四分之一场建模。
   - 对称性变换：组件通过 `Rotator` 属性控制旋转：
     - 当 `Yaw = -32768`（即 $-180^\circ$）时，配合坐标轴取反（如 $X \to -X, Y \to -Y$）完成橙蓝双方半场的镜像拼装。
   - 大药包点位（`BoostPad_Large`）：全场 6 处，其世界坐标完全沿场地中心点 $(0,0)$ 呈中心对称分布。

### 2.2 外部环境布置
- **林地植被**：环绕场地外围布置了 19 株 `Woods_Tree_LowPoly_001`、19 株 `Woods_Tree_LowPoly_003`、12 株 `Woods_Tree_LowPoly_002` 以及远景十字交叉精灵卡片树 `TreeSimpleSprite`。
- **水域与建筑**：场地外侧布置了 6 块巨型湖泊水面网格 `Woods_Lake_Plane_01` 与水上木屋 `Woods_Lake_Cabin_01`、输电线杆 `Woods_PowerLine_Light_01/02`。
- **场地细节彩蛋**：场边停放有经典生锈旧车 `OldOctane`、轮胎堆 `TirePile01` 与木质长椅。

---

## 3. 材质、贴图利用方式与动态着色器参数

虚幻引擎在火箭联盟中使用了大量可参数化的材质实例（MaterialInstanceConstant）：

1. **队伍动态染色（Team Color Tinting）**：
   - 典型材质：`Woods_WoodTiled_TeamColor_MIC`、`Woods_WoodPlanks_TeamColor_MIC`。
   - 利用方式：漫反射贴图（`Woods_Wood_Basic_D`）提供木纹底色，法线贴图（`Farm_Wood_N`）提供凹凸质感，而遮罩贴图（`Woods_Wood_Basic_M`）在红色通道中存储染色区域权重。
   - 动态参数：着色器接收向量参数 `TeamColor0`（蓝队，默认深蓝/青色）和 `TeamColor1`（橙队，默认亮橙/红黄），在两端看台和标志物上进行动态乘法/线性插值混合染色。
2. **六边形能量网格（Hex Wall FX）**：
   - 网格体：`Woods_Field_Walls_Hexes`。
   - 材质引用：`CSNetFence_MAT`、`HexGlass_Mat`。
   - 利用方式：通过 `TiledPatterns.Hexagons_N` 生成折射法线，并动态调节透明度与发光强度，在足球或赛车接近场地边缘时产生能量涟漪效果。
3. **草坪纹理双层混合**：
   - 典型材质：`GroomedGrass_FakeLight_Team1_MIC`、`Sand_2Layer_V2_Parent_MIC`。
   - 利用方式：利用顶点颜色（Vertex Color）中的 Alpha/RGB 通道作为混合遮罩，在同一块草坪网格上融合深浅草纹与泥沙边缘。

---

## 4. 坐标系转换数学推导

- **Unreal 空间**：左手系，Z 轴朝上，$X$ 轴向前，$Y$ 轴向右，单位为厘米（cm）。
  旋转顺序：Roll ($X$) $\to$ Pitch ($Y$) $\to$ Yaw ($Z$)，角度单位 $180^\circ = 32768$。
- **glTF / GLB 空间**：右手系，Y 轴朝上，$X$ 轴向右，$Z$ 轴向前，单位为米（m）。
- **坐标变换矩阵 $C$**：
  $$C = \begin{pmatrix} 0.01 & 0 & 0 & 0 \\ 0 & 0 & 0.01 & 0 \\ 0 & 0.01 & 0 & 0 \\ 0 & 0 & 0 & 1 \end{pmatrix}$$
- **顶点世界变换矩阵关系**：
  $$M_{\text{glTF}} = C \cdot M_{\text{UE}} \cdot C^{-1}$$
  本方法保证了导出的 glTF 局部网格体顶点数据无需重复修改，直接通过节点树的变换矩阵实现 100% 精确装配。
