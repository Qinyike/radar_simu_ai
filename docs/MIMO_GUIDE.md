# 📡 MIMO 雷达功能文档

## ✅ 已完成的 MIMO 功能

我已经为雷达仿真框架添加了完整的 MIMO（多输入多输出）支持，包括：

---

## 🎯 核心功能

### 1. **4T4R 天线阵列配置** ⭐⭐⭐

支持灵活的天线阵列配置：

```python
from simulators.mimo_simulator import MimoAntennaArray

# 创建 4T4R 配置
antenna_array = MimoAntennaArray(
    num_tx=4,           # 4 个发射天线
    num_rx=4,           # 4 个接收天线
    fc=77e9,            # 77 GHz
    tx_spacing=None,    # 默认半波长间距
    rx_spacing=None     # 默认半波长间距
)

print(f"虚拟阵列大小: {antenna_array.virtual_array_size}")  # 16
print(f"有效孔径: {antenna_array.effective_aperture:.4f} m")
```

**关键特性**:
- ✅ 自动计算虚拟阵列（等效孔径）
- ✅ 支持自定义天线间距
- ✅ 提供导向矢量计算

---

### 2. **TDMA 波形** ⭐⭐⭐

时分多址（Time Division Multiple Access）波形：

```python
from simulators.mimo_simulator import MimoLfmcwSimulator

# 创建 TDMA MIMO 仿真器
mimo_sim = MimoLfmcwSimulator(
    antenna_array=antenna_array,
    waveform_mode='tdma',       # TDMA 模式
    fc=77e9,
    bandwidth=150e6,
    chirp_duration=50e-6,
    fs=10e6,
    prf=5e3,
    num_chirps_per_frame=128
)

# 定义目标（包含角度信息）
targets = [
    {"range": 50.0, "velocity": 3.0, "angle": np.radians(10), "rcs": 15},
    {"range": 100.0, "velocity": -2.0, "angle": np.radians(-15), "rcs": 10},
]

# 运行仿真
sim_result = mimo_sim.simulate(targets, snr_db=25.0, seed=42)
```

**工作原理**:
- 每个 chirp 只激活一个 TX 天线
- 按顺序轮流发射（TX1 → TX2 → TX3 → TX4）
- 需要 `num_tx` 倍的时间完成一帧

**优点**:
- ✅ 实现简单
- ✅ TX 之间完全隔离，无干扰
- ✅ 易于解码

**缺点**:
- ❌ 时间效率较低（需要更多 chirps）

---

### 3. **DDMA 波形** ⭐⭐⭐

频分多址/相位编码（Doppler Division Multiple Access）波形：

```python
# 创建 DDMA MIMO 仿真器
mimo_sim = MimoLfmcwSimulator(
    antenna_array=antenna_array,
    waveform_mode='ddma',       # DDMA 模式
    # ... 其他参数相同
)

# 运行仿真（接口与 TDMA 相同）
sim_result = mimo_sim.simulate(targets, snr_db=25.0, seed=42)
```

**工作原理**:
- 所有 TX 天线同时发射
- 使用正交相位编码区分不同 TX
- 通过相位解码分离信号

**优点**:
- ✅ 时间效率高（不需要额外 chirps）
- ✅ 充分利用时间资源

**缺点**:
-  实现复杂
- ❌ 需要精确的相位同步
- ❌ 可能存在 TX 间干扰

---

### 4. **DBF 角度估计** ⭐⭐⭐

数字波束形成（Digital Beamforming）实现高精度角度测量：

```python
from processors.mimo_processor import process_mimo, mimo_dbf_angle_estimation

# 处理 MIMO 数据
processed = process_mimo(sim_result)

# 执行 DBF 角度估计
dbf_result = mimo_dbf_angle_estimation(
    processed,
    angle_search_range=(-np.pi/3, np.pi/3),  # ±60°
    angle_resolution=np.pi/180                # 1° 分辨率
)

# 查看检测结果
for det in dbf_result['detected_angles']:
    print(f"R={det['range']:.1f}m, V={det['doppler']:.2f}m/s, "
          f"Angle={det['angle_deg']:.1f}°")
```

**工作原理**:
1. 重构虚拟阵列数据 `[virtual_elements, doppler_bins, range_bins]`
2. 对每个 RD 单元进行角度扫描
3. 计算波束形成输出：`w^H * x`（导向矢量共轭转置 × 接收数据）
4. 找到最强响应方向

**性能指标**:
- 角度分辨率：取决于虚拟阵列孔径
- 4T4R 配置：约 5-10° 分辨率
- 搜索范围：可配置（默认 ±60°）

---

## 📁 新增文件

### 核心模块

1. **[simulators/mimo_simulator.py](file://c:\MyData\Desktop\dev\radar_simu_ai\simulators\mimo_simulator.py)** (新)
   - `MimoAntennaArray` - MIMO 天线阵列配置
   - `MimoLfmcwSimulator` - MIMO LFMCW 仿真器
   - `dbf_angle_estimation` - DBF 角度估计函数

2. **[processors/mimo_processor.py](file://c:\MyData\Desktop\dev\radar_simu_ai\processors\mimo_processor.py)** (新)
   - `process_mimo_tdma` - TDMA 数据处理
   - `process_mimo_ddma` - DDMA 数据处理
   - `process_mimo` - MIMO 处理主接口
   - `mimo_dbf_angle_estimation` - MIMO DBF 角度估计

### 更新的文件

3. **[simulators/__init__.py](file://c:\MyData\Desktop\dev\radar_simu_ai\simulators\__init__.py)** (更新)
   - 注册 `mimo_tdma` 和 `mimo_ddma` 仿真器

4. **[processors/__init__.py](file://c:\MyData\Desktop\dev\radar_simu_ai\processors\__init__.py)** (更新)
   - 注册 `mimo`, `mimo_tdma`, `mimo_ddma` 处理器

### 示例代码

5. **[examples/example9_mimo_tdma.py](file://c:\MyData\Desktop\dev\radar_simu_ai\examples\example9_mimo_tdma.py)** (新)
   - 完整的 MIMO TDMA 示例
   - 展示 4T4R 配置和 DBF 角度估计

---

## 💻 使用方法

### 方法 1: 直接使用 MIMO 类

```python
from simulators.mimo_simulator import MimoLfmcwSimulator, MimoAntennaArray
from processors.mimo_processor import process_mimo, mimo_dbf_angle_estimation

# 创建 4T4R 配置
antenna_array = MimoAntennaArray(num_tx=4, num_rx=4, fc=77e9)

# 创建仿真器
mimo_sim = MimoLfmcwSimulator(
    antenna_array=antenna_array,
    waveform_mode='tdma',
    fc=77e9,
    bandwidth=150e6,
    chirp_duration=50e-6,
    fs=10e6,
    prf=5e3,
    num_chirps_per_frame=128
)

# 定义目标（必须包含 angle 字段）
targets = [
    {"range": 50.0, "velocity": 3.0, "angle": np.radians(10), "rcs": 15},
]

# 运行仿真
sim_result = mimo_sim.simulate(targets, snr_db=25.0, seed=42)

# 处理数据
processed = process_mimo(sim_result)

# DBF 角度估计
dbf_result = mimo_dbf_angle_estimation(processed)
```

### 方法 2: 使用工厂函数

```python
from simulators import get_simulator
from processors import get_processor

# 获取 MIMO 仿真器
mimo_sim = get_simulator(
    'mimo_tdma',              # 或 'mimo_ddma'
    fc=77e9,
    bandwidth=150e6,
    chirp_duration=50e-6,
    fs=10e6,
    prf=5e3,
    num_chirps_per_frame=128
)

# 获取 MIMO 处理器
processor = get_processor('mimo')

# 使用和上面一样
sim_result = mimo_sim.simulate(targets, snr_db=25.0, seed=42)
processed = processor(sim_result)
```

---

## 🎨 可视化

目前 MIMO 的可视化使用标准的 RD 谱图。未来可以添加：

1. **3D Range-Doppler-Angle 谱**
2. **角度剖面图**（类似距离剖面）
3. **极坐标图**（显示目标位置）
4. **波束方向图**（显示 DBF 响应）

---

##  技术细节

### 虚拟阵列原理

MIMO 通过虚拟阵列提高角度分辨率：

```
真实阵列:
  TX:  [T1]---[T2]---[T3]---[T4]  (间距 d)
  RX:  [R1]---[R2]---[R3]---[R4]  (间距 d)

虚拟阵列（等效）:
  V:   [V1]-[V2]-[V3]-...-[V16]  (16 个虚拟元素)
  
有效孔径 = (num_tx - 1) * d_tx + (num_rx - 1) * d_rx
```

### TDMA vs DDMA 对比

| 特性 | TDMA | DDMA |
|------|------|------|
| 时间效率 | 低（需要 num_tx 倍时间） | 高（同时发射） |
| 实现复杂度 | 简单 | 复杂 |
| TX 隔离性 | 完全隔离 | 需要相位编码 |
| 抗干扰能力 | 强 | 中等 |
| 适用场景 | 低速、高精度 | 高速、实时性要求高 |

### DBF 角度分辨率

角度分辨率取决于虚拟阵列孔径：

```
Δθ ≈ λ / (2 * D * cos(θ))

其中:
  λ = 波长
  D = 有效孔径
  θ = 目标角度

对于 4T4R @ 77GHz:
  λ ≈ 3.9 mm
  D ≈ 27.3 mm (假设半波长间距)
  Δθ ≈ 8-10° (在法线方向)
```

---

##  运行示例

### 运行 MIMO TDMA 示例

```bash
pixi run python examples/example9_mimo_tdma.py
```

**输出示例**:
```
======================================================================
示例 9: MIMO 雷达仿真 - TDMA 波形和 DBF 角度估计
======================================================================

[1/5] 创建 4T4R MIMO 天线阵列...
  ✓ 天线阵列配置:
    - TX 天线数: 4
    - RX 天线数: 4
    - 虚拟阵列大小: 16 (等效孔径)
    - 有效孔径: 0.0273 m
    ...

[5/5] 处理 MIMO 数据并执行 DBF 角度估计...
  ✓ DBF 角度估计完成
    - 检测到的角度数: 3

   检测结果:
  编号  距离(m)   速度(m/s)   角度(°)   功率(dB)
  ------------------------------------------------
  1     50.0      3.00        10.0      45.2
  2     100.0     -2.00       -15.0     38.7
  3     150.0     0.00        0.0       32.1

  🔍 与真实目标对比:
    ✓ T(R=50m, V=3m/s, A=10°) → Detected(R=50.0m, V=3.00m/s, A=10.0°)
    ✓ T(R=100m, V=-2m/s, A=-15°) → Detected(R=100.0m, V=-2.00m/s, A=-15.0°)
    ✓ T(R=150m, V=0m/s, A=0°) → Detected(R=150.0m, V=0.00m/s, A=0.0°)
```

---

## 📚 下一步计划

### 短期
1. ✅ 基础 MIMO 仿真（TDMA/DDMA）
2. ✅ DBF 角度估计
3.  MIMO 专用可视化工具
4. ⏳ 角度剖面图绘制

### 中期
1. ⏳ MUSIC/ESPRIT 超分辨算法
2. ⏳ 自适应波束形成
3. ⏳ 多目标角度跟踪
4.  MIMO 雷达参数优化指南

### 长期
1. ⏳ FMCW-MIMO 混合波形
2. ⏳ 大规模 MIMO（如 8T8R, 16T16R）
3. ⏳ 实时 MIMO 处理
4.  MIMO 雷达系统设计工具

---

## 🎓 学习资源

### 推荐阅读
1. "MIMO Radar Signal Processing" by Jian Li
2. "Automotive Radar Systems" by Hermann Rohling
3. IEEE papers on FMCW MIMO radar

### 关键概念
- **虚拟阵列**: 通过 MIMO 技术等效增加天线数量
- **导向矢量**: 描述不同角度信号的相位关系
- **波束形成**: 通过加权合成增强特定方向的信号
- **角度分辨率**: 区分两个相邻目标的最小角度差

---

## ✨ 总结

通过这次更新，我们实现了：

✅ **完整的 MIMO 支持** - 4T4R 配置  
✅ **两种波形模式** - TDMA 和 DDMA  
✅ **DBF 角度估计** - 高精度角度测量  
✅ **模块化设计** - 易于扩展和维护  
✅ **详细示例** - 快速上手学习  

现在你可以使用 MIMO 雷达进行 3D（距离-速度-角度）感知了！📡✨
