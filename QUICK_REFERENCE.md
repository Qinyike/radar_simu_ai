# 🚀 雷达仿真框架 - 快速参考卡

## ⚡ 一键运行

```bash
# Windows
run_examples.bat

# Linux/Mac  
./run_examples.sh
```

---

## 📚 学习资源速查

| 资源 | 文件 | 适合人群 |
|------|------|----------|
| 5分钟入门 | [QUICKSTART.md](QUICKSTART.md) | 所有人 |
| 完整教程 | [TUTORIAL.md](TUTORIAL.md) | 系统学习者 |
| 示例说明 | [examples/README.md](examples/README.md) | 实践者 |
| 项目总览 | [README.md](README.md) | 开发者 |
| 架构指南 | [base_rule.md](base_rule.md) | 架构师 |

---

## 💻 6个示例速览

| # | 示例 | 命令 | 难度 |
|---|------|------|------|
| 1 | 基础使用 | `pixi run python examples/example1_basic.py` | ⭐ |
| 2 | 多目标场景 | `pixi run python examples/example2_multi_target.py` | ⭐⭐ |
| 3 | 参数调优 | `pixi run python examples/example3_parameter_tuning.py` | ⭐⭐⭐ |
| 4 | SNR分析 | `pixi run python examples/example4_snr_analysis.py` | ⭐⭐⭐ |
| 5 | 自定义可视化 | `pixi run python examples/example5_custom_visualization.py` | ⭐⭐⭐⭐ |
| 6 | 批量仿真 | `pixi run python examples/example6_batch_simulation.py` | ⭐⭐⭐⭐ |
| 7 | 多普勒模糊 | `pixi run python examples/example7_doppler_aliasing.py` | ⭐⭐⭐ |

---

## 🔧 常用代码片段

### 快速仿真
```python
from main import run_simulation

targets = [{"range": 50.0, "velocity": 3.0, "rcs": 15}]
sim_result, processed_result = run_simulation(
    waveform_type="lfmcw",
    targets=targets,
    snr_db=25.0,
    seed=42,
    visualize=True,
    save_plots=True,
    output_dir="./output"
)
```

### 提取数据
```python
rd_spectrum = processed_result.range_doppler
range_axis = processed_result.range_axis
doppler_axis = processed_result.doppler_axis

# 找到最强目标
import numpy as np
max_idx = np.unravel_index(np.argmax(rd_spectrum), rd_spectrum.shape)
detected_range = range_axis[max_idx[0]]
detected_velocity = doppler_axis[max_idx[1]]
```

### 自定义参数
```python
from simulators import LfmcwSimulator

simulator = LfmcwSimulator(
    fc=77e9,              # 77 GHz
    bandwidth=150e6,      # 150 MHz
    chirp_duration=50e-6, # 50 μs
    fs=10e6,              # 10 MHz
    prf=5e3,              # 5 kHz
    num_chirps=128        # 128 chirps
)
```

---

## 📊 性能指标（默认参数）

| 指标 | 数值 |
|------|------|
| 距离分辨率 | 1.0 m |
| 最大探测距离 | 249 m |
| 速度分辨率 | 0.08 m/s |
| 最大不模糊速度 | ±4.79 m/s |

---

## 🎯 典型应用场景

### 自适应巡航控制 (ACC)
```python
targets = [
    {"range": 100.0, "velocity": 5.0, "rcs": 15},  # 前车
]
```

### 自动紧急制动 (AEB)
```python
targets = [
    {"range": 30.0, "velocity": -10.0, "rcs": 10},  # 行人
]
```

### 盲点监测 (BSD)
```python
targets = [
    {"range": 15.0, "velocity": 8.0, "rcs": 12},   # 侧后方车辆
]
```

---

## ❓ 常见问题

**Q: 如何改变雷达频率？**
```python
simulator = LfmcwSimulator(fc=79e9, ...)  # 改为 79 GHz
```

**Q: 如何提高距离分辨率？**
```python
simulator = LfmcwSimulator(bandwidth=200e6, ...)  # 增加带宽
```

**Q: 出现多普勒混叠怎么办？**
```python
simulator = LfmcwSimulator(prf=10e3, ...)  # 提高 PRF
```

**Q: 如何保存数据？**
```python
import numpy as np
np.save('data.npy', processed_result.range_doppler)
```

---

## 📁 输出文件位置

```
output/
├── example1/           # 示例1的图表
├── example2/           # 示例2的图表
├── example3_*.png      # 示例3的对比图
├── example4_*.png      # 示例4的分析图
├── example5_*.png      # 示例5的自定义图
└── example6_*.json     # 示例6的测试结果
```

---

## 🛠️ 调试技巧

```python
# 查看数据形状
print(f"RD谱形状: {processed_result.range_doppler.shape}")
print(f"距离轴范围: {range_axis[0]} - {range_axis[-1]} m")
print(f"速度轴范围: {doppler_axis[0]} - {doppler_axis[-1]} m/s")

# 验证物理合理性
assert 0 <= detected_range <= range_axis[-1]
assert abs(detected_velocity) <= doppler_axis[-1]
```

---

## 🎓 学习路径

```
初学者: 示例1 → 示例2 → TUTORIAL.md 第一阶段
进阶者: 示例3 → 示例4 → TUTORIAL.md 第二阶段  
专家:   示例5 → 示例6 → TUTORIAL.md 第三阶段
```

---

## 📞 获取帮助

1. 查看 [TUTORIAL.md](TUTORIAL.md) 的常见问题章节
2. 阅读对应示例的代码注释
3. 检查 [examples/README.md](examples/README.md)

---

**祝你使用愉快！** 🚗📡✨

*提示：将此文件加入书签，方便随时查阅*
