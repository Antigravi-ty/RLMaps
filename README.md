# Rocket League — 愚人节三轮车模式 (April Fool LTM) 与 Mutators 完整数据分支

本分支包含《Rocket League》愚人节限时模式 (`GameInfo_LTM_AprilFool_SF.upk`) 及配套变异器包 (`Mutators_SF.upk`、`Mutators_Items_SF.upk`、`Mutators_Balls_SF.upk`) 的完整解包资源、GLB 模型与递归解析的物理属性元数据。

---

## 1. 愚人节“三轮车/三蹦子”模式 (`GameInfo_LTM_AprilFool_SF.upk`) 核心机制解析

通过对 `GameInfo_LTM_AprilFool_SF.upk` 内 1,899 个导出对象和 557 个导入引用进行完整递归属性反序列化（详见 `metadata/april_fool_ltm_analysis.json`），其底层实现结构如下：

1. **主入口 (`GameInfo_LTM_AprilFool_TA'GameInfo.GameInfo_LTM_AprilFool'`)**：
   - 绑定主比赛事件原型 `GameEvent_Soccar_TA'GameInfo_LTM_AprilFool.Archetype'`。
2. **强制开启的两个核心变异器 (`DefaultMutators`)**：
   - **`Mutator_Loadout_TA'GameInfo_LTM_AprilFool.Mutators.Tritip'`**：
     - 属性：`Products: [ProductAsset_Body_TA'body_tritip_SF.body_tritip']`
     - 作用：强制将场内所有玩家的载具配置覆写为三轮车专用车体资产 `body_tritip`（即火箭联盟内部将单前轮居中、移除双前轮支撑的特殊三轮 Octane 变体，对应 RocketSim / `TricycleCoreWASM` 中的 `CAR_CONFIG_PSYCLOPS`）。
   - **`Mutator_Booster_TA'GameInfo_LTM_AprilFool.Mutators.SlowRecharge'`**：
     - 属性：`BoostRechargeRate: 0.0666`、`BoostRechargeDelay: 2.0`
     - 作用：提供缓慢自动充能氮气。
3. **车轮与悬挂力学参数 (`VehicleSim_TA` & `Wheel_TA`)**：
   - `DriveTorque`: `288000`
   - `BrakeTorque`: `10500`
   - `IdleBrakeFactor`: `0.15`
   - `bUseAckermannSteering`: `true`
   - `SteerAngleCurve`: `(0 uu/s -> 35°, 500 -> 20°, 1000 -> 11°, 1500 -> 6.25°, 1750 -> 5°, 3000 -> 2°)`
   - `SuspensionStiffness`: `500`, `SuspensionDampingCompression`: `25`, `SuspensionDampingRelaxation`: `40`, `SuspensionTravel`: `12`, `SuspensionMaxRaise`: `2.5`
   - 在 `Car_Test` 原型中，`LatFrictionCurve` 的侧向抓地系数被加倍至 `(0 -> 2.0, 1 -> 0.4)`，`HandbrakeLatFrictionCurve` 降至 `0.05`，配合三点接地支撑的几何结构，在急转弯时产生剧烈的侧倾力矩。

---

## 2. 目录结构

- **`models/balls/`**：从 `Mutators_Balls_SF.upk` 合成的 23 个特殊球体 GLB 模型（包括标准球 `Ball_DefaultBall00.glb`、篮球 `Ball_Basketball_SM.glb`、立方体球 `Ball_CubeBall_SM.glb`、冰球 `HockeyPuck_SM.glb`、橄榄球 `Football_06_SM.glb`、沙滩球 `Ball_Beachball_SM.glb`、披萨冰球 `PizzaCheezyPuck_SM.glb`、南瓜球 `PumpkinCube2_SM.glb` 等）。
- **`models/items/`**：从 `Mutators_Items_SF.upk` 合成的 18 个道具赛 (Rumble) 3D 武器/道具 GLB 模型（包括龙卷风、拳击手套、马桶搋子、抓钩、靴子、尖刺、蝙蝠镖、大锤、弹簧等）。
- **`metadata/`**：
  - `april_fool_ltm_analysis.json`：愚人节三轮车模式核心配置与物理曲线提取汇总。
  - `GameInfo_LTM_AprilFool_SF_scene.json`：完整递归反序列化的包级对象属性表。
  - `Mutators_SF_scene.json`、`Mutators_Items_SF_scene.json`、`Mutators_Balls_SF_scene.json`：所有变异器包的完整对象属性表。
- **`raw/`**：按 UPK Group 路径完整保留的原始 `.gltf`、`.bin`、`.png`、`.mat`、`.props.txt` 文件。
