# 三蹦子模式 (`Confidential_ThirdWheel_Test` / `Body_Topple` / 愚人节 LTM) 与 Mutator 特殊球体/道具独立分支 (`tricycle-thirdwheel-test`)

本分支专门用于存放从 `GameInfo_LTM_AprilFool_SF.upk`、`Mutators_SF.upk`、`Mutators_Balls_SF.upk`、`Mutators_Items_SF.upk` 以及 `body_topple_SF.upk`、`Body_Topple_T_SF.upk`、`Body_Octane_SF.upk` 中完整解密与提取的 **三蹦子（Three-Wheeler / Topple / Psyclops）3D 模型（含前轮居中的三轮改造版与骨骼绑定版）**、**16 种 Mutator 特殊球体 GLB**、**9 种大乱斗（Rumble）道具 GLB** 以及 **完整的物理悬挂/摩擦曲线元数据**。

---

## 一、 仓库目录结构

```text
├── models/
│   ├── tricycle_cars/                                 # 三蹦子 (Body_Topple & Octane) 分材质 GLB 模型
│   │   ├── Topple_Tricycle_ThreeWheel.glb             # 三蹦子前轮收拢版模型（保留全部 7 个原生表面细节材质槽 + 氮气喷口 + 烘焙 PBR 贴图）
│   │   ├── Topple_Tricycle_ThreeWheel_SkeletalRigged.glb # 保留完整 55 根骨骼层级并将前轮骨骼横向收拢至 ±5.0 UU 的骨骼绑定版 GLB
│   │   ├── Topple_Standard_FourWheel.glb              # Body_Topple 标准四轮姿态 7 材质槽 PBR 模型
│   │   ├── Topple_WhiteModel.glb                      # 三蹦子几何白模（保留半透明车窗与 7 材质分类）
│   │   └── Octane_Tricycle_ThreeWheel.glb             # 基于 Body_Octane_PremiumSkin_SK 按 UV 遮罩拆分为底盘/车漆/挡风玻璃/饰条的三蹦子模型
│   ├── mutator_balls/                                 # 从 Mutators_Balls_SF.upk 提取合成的 16 种特殊球体 GLB
│   │   ├── Ball_DefaultBall00.glb                     # 标准比赛球
│   │   ├── Ball_Soccer_SM.glb                         # 经典黑白足球
│   │   ├── ball_adidas_sm.glb                         # Adidas 联名足球
│   │   ├── Ball_Nike_SM.glb                           # Nike 联名足球
│   │   ├── Ball_LuminousAirplane_SM.glb               # 发光飞机球
│   │   ├── Ball_SphereGulp_SM.glb                     # 2K 高清吞噬球
│   │   ├── GodBall_RL_SM.glb                          # Heatseeker 追热模式神球
│   │   ├── Ball_CubeBall_SM.glb                       # 方块球 (Cubic)
│   │   ├── PumpkinCube2_SM.glb                        # 万圣节南瓜方块球
│   │   ├── Ball_Basketball_SM.glb                     # Hoops 篮球模式篮球
│   │   ├── Ball_Beachball_SM.glb                      # 沙滩球
│   │   ├── Football_06_SM.glb                         # Gridiron 美式橄榄球
│   │   ├── HockeyPuck_SM.glb                          # Snow Day 冰球
│   │   ├── PizzaCheezyPuck_SM.glb                     # 忍者神龟披萨冰球
│   │   ├── Ball_Breakout_SM.glb                       # Core 707 (Dropshot) 能量球
│   │   └── eggball_sm.glb                             # 彩蛋球
│   └── mutator_items/                                 # 从 Mutators_Items_SF.upk 提取合成的 9 种大乱斗道具 GLB
│       ├── Items_BoxingGlove2_SM.glb                  # 拳击手套 (Haymaker)
│       ├── Items_BoxingGloveB_SM.glb                  # 蝙蝠侠拳套
│       ├── Items_Boot_SM.glb                          # 踢人靴子 (The Boot)
│       ├── Items_Plunger_SM.glb                       # 搋子 (Plunger)
│       ├── Items_Hammer_SM.glb                        # 重锤 (Powerhitter)
│       ├── Batarang_SM.glb                            # 蝙蝠镖
│       ├── Items_Spikes_01.glb                        # 尖刺 (Spikes)
│       ├── clayspikes_sm.glb                          # 泥土尖刺
│       └── Spring02.glb                               # 弹簧
├── metadata/
│   ├── tricycle_aprilfool_ltm_config.json             # 三蹦子完整物理参数、悬挂偏移、转向/摩擦曲线与 Mutator 配置
│   └── scene_dumps/                                   # 6 个 UPK 包的完整属性树 JSON 转储
├── textures_and_icons/                                # 提取的全部原始贴图与技能图标 (.png)
├── raw/                                               # 6 个 UPK 包的 100% 原始导出资产
└── tools/
    └── build_tricycle_ltm.py                          # 自动化三蹦子模型构建与材质分类脚本
```

---

## 二、 三蹦子模式（Three-Wheeler / `Body_Topple` / `CAR_CONFIG_PSYCLOPS`）核心参数解析

1. **UPK 内部资产映射**：
   - 在 `Mutators_SF.upk` 与 `GameInfo_LTM_AprilFool_SF.upk` 中，愚人节三蹦子加载器为 `Mutator_Loadout_TA'Tritip'`，强制指定车身产品为 `body_tritip`，对应包 `body_topple_SF.upk` 中的 `ProductAsset_Body_TA'Body_Topple'`（`ProductID = 12314`，`HandlingPreset = 100`）。
   - `Body_Topple_SK` 原生包含 **7 个独立的表面细节材质槽**：
     1. `MIC_Topple_Chassis`（金属底盘、悬挂与排气管）
     2. `MIC_Topple_CarbonFiber`（碳纤维内衬）
     3. `MIC_Topple_Windshield`（前挡风玻璃）
     4. `MIC_Topple_Lenses`（车前大灯透镜）
     5. `MIC_Topple_Plastic`（哑光塑料护板）
     6. `MAT_Vehicle_Glass_Translucent`（半透明侧窗/顶窗玻璃）
     7. `MIC_Topole_Body`（主车漆与金属曲率）
2. **三蹦子物理与常规四轮八角车（Octane）的 4 处核心差异**：
   - **前轮横向间距缩窄**：标准 Octane 前轮横向偏移为 `Y = ±25.90 UU`，而三蹦子模式（`CAR_CONFIG_PSYCLOPS`，`threeWheels = true`）将前轮连接点横向偏移缩窄至 **`Y = ±5.00 UU`**（几乎合并在车头正中央）。
   - **前后悬挂静止长度调整**：前轮悬挂静止长度由 `38.75 UU` 缩短为 `33.0 UU`，后轮由 `37.05 UU` 缩短为 `31.3 UU`。
   - **取消地面吸附力 (`stickyForceScale = 0`)**：常规四轮车在地面行驶时拥有 `0.5` 倍重力的下压力吸附，而三蹦子模式在 `Car.cpp` 中将 `stickyForceScale` 设为 `0.0`，导致急转弯时离心力矩直接克服极窄的前轮支撑基线而侧翻。
   - **专属三轮转向角与侧向摩擦曲线**：启用 `STEER_ANGLE_FROM_SPEED_CURVE_THREEWHEEL` 与 `LAT_FRICTION_CURVE_THREEWHEEL`（已在 `TricycleCoreWASM` 中完整桥接为 `hitboxIndex = 6` 及 `_physics_setCarThreeWheels(carId, 1)`）。
