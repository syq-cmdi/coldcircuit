# ColdCircuit API 设计说明

## 1. 顶层对象：ColdPlate

`ColdPlate` 是液冷板设计的声明式入口，相当于 tscircuit 中的顶层电路对象。

核心字段：

- `base_size_mm`: 冷板长宽；
- `thickness_mm`: 冷板总厚度；
- `material`: 冷板材料；
- `fluid`: 冷却液；
- `inlet_outlet`: 入口、出口、流量和压降约束；
- `channels`: 流道组件；
- `fins`: 扰流/针翅组件；
- `heat_sources`: 芯片/模块热源；
- `manufacturing_process`: 工艺路线。

## 2. 组件对象

### 2.1 SerpentineChannel

蛇形流道。适合快速形成高覆盖率换热面积，但压降较高，弯头局部损失明显。

### 2.2 ParallelMicrochannelBank

并联微通道。适合高热流密度芯片或 GPU 冷板，但对加工精度、堵塞风险、流量均匀性更敏感。

### 2.3 PinFinArray

针翅阵列。适合局部高热流密度区域，后续可与 CFD 后端耦合。

## 3. 快速仿真模型

当前 `simulate_1d()` 采用单等效流道或并联流道模型，输出雷诺数、水力直径、换热系数、冷却液温升、压降、热源估算最高温度和约束是否通过。

## 4. LLM 使用方式

推荐让 LLM 输出 JSON，再由 Pydantic 校验，避免“看起来对、实际不可运行”的代码。

## 5. 下一阶段扩展

- build123d STEP/STL 导出；
- OpenFOAM 可运行 case 生成；
- SciPy/Nevergrad 多目标优化；
- 车载 GaN、GPU、数据中心冷板模板库。
