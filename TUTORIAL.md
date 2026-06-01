# 🚗 雷达仿真框架 - 完整教程

欢迎使用汽车雷达 LFMCW 仿真框架！本教程将带你从零开始，逐步掌握雷达仿真技术。

---

## 📖 学习路径

### 🌟 第一阶段：入门（1-2小时）

**目标**: 理解基本概念，能运行简单仿真

1. **阅读快速开始**
   - [QUICKSTART.md](QUICKSTART.md) - 5分钟了解项目

2. **运行基础示例**
   ```bash
   # 示例1: 最简单的仿真
   pixi run python examples/example1_basic.py
   ```
   - 学习如何定义目标
   - 理解仿真流程
   - 查看输出结果

3. **探索多目标场景**
   ```bash
   # 示例2: 真实交通场景
   pixi run python examples/example2_multi_target.py
   ```
   - 学习配置多个目标
   - 理解距离和速度的概念
   - 分析检测结果

**✅ 完成标志**: 能独立修改目标参数并观察效果

---

### 🎯 第二阶段：进阶（3-5小时）

**目标**: 理解雷达参数对性能的影响

4. **参数调优实验**
   ```bash
   # 示例3: 探索参数影响
   pixi run python examples/example3_parameter_tuning.py
   ```
   - 带宽 vs 距离分辨率
   - Chirp数量 vs 速度分辨率
   - 学习权衡设计

5. **信噪比分析**
   ```bash
   # 示例4: 噪声影响研究
   pixi run python examples/example4_snr_analysis.py
   ```
   - 理解 SNR 的概念
   - 学习检测灵敏度分析
   - 掌握 SIR 指标

**✅ 完成标志**: 能根据需求选择合适的雷达参数

---

### 🚀 第三阶段：精通（5-10小时）

**目标**: 能创建自定义应用和报告

6. **自定义可视化**
   ```bash
   # 示例5: 专业报告制作
   pixi run python examples/example5_custom_visualization.py
   ```
   - 学习 Matplotlib 高级用法
   - 创建多面板图表
   - 定制化报告格式

7. **批量仿真**
   ```bash
   # 示例6: 自动化测试
   pixi run python examples/example6_batch_simulation.py
   ```
   - 批量运行多个场景
   - 自动生成测试报告
   - JSON 数据导出

**✅ 完成标志**: 能独立开发新的应用场景

---

## 📚 示例代码索引

| 示例 | 文件 | 难度 | 学习时间 | 核心内容 |
|------|------|------|----------|----------|
| 1 | `example1_basic.py` | ⭐ | 15分钟 | 基础仿真流程 |
| 2 | `example2_multi_target.py` | ⭐⭐ | 30分钟 | 多目标场景 |
| 3 | `example3_parameter_tuning.py` | ⭐⭐⭐ | 1小时 | 参数调优 |
| 4 | `example4_snr_analysis.py` | ⭐⭐⭐ | 1小时 | 信噪比分析 |
| 5 | `example5_custom_visualization.py` | ⭐⭐⭐⭐ | 2小时 | 自定义可视化 |
| 6 | `example6_batch_simulation.py` | ⭐⭐⭐⭐ | 2小时 | 批量仿真 |

---

## 🎓 实战项目建议

学完所有示例后，尝试以下项目：

### 项目1: 高速公路自适应巡航控制 (ACC)
**场景**: 前车在100-200m范围内，速度变化
**挑战**: 
- 实时跟踪前车距离和速度
- 计算安全距离
- 模拟制动决策

### 项目2: 城市道路防撞系统 (AEB)
**场景**: 行人突然横穿马路
**挑战**:
- 检测弱反射目标（行人RCS小）
- 快速响应时间
- 虚警率控制

### 项目3: 自动泊车辅助
**场景**: 停车场环境，多障碍物
**挑战**:
- 近距离高精度测量
- 多角度目标检测
- 静态障碍物识别

### 项目4: 盲点监测系统 (BSD)
**场景**: 侧后方车辆接近
**挑战**:
- 大角度覆盖
- 相对速度测量
- 多车道监控

---

## 💻 常用代码片段

### 快速仿真模板

```python
import sys, os
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from main import run_simulation

# 定义目标
targets = [
    {"range": 50.0, "velocity": 3.0, "rcs": 15},
]

# 运行仿真
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

### 提取原始数据

```python
# 从处理结果中提取数据
rd_spectrum = processed_result.range_doppler      # RD谱 [range_bins, doppler_bins]
range_profile = processed_result.range_profile    # 距离剖面
range_axis = processed_result.range_axis          # 距离轴 (m)
doppler_axis = processed_result.doppler_axis      # 速度轴 (m/s)

# 找到最强目标
import numpy as np
max_idx = np.unravel_index(np.argmax(rd_spectrum), rd_spectrum.shape)
detected_range = range_axis[max_idx[0]]
detected_velocity = doppler_axis[max_idx[1]]
```

### 自定义雷达参数

```python
from simulators import LfmcwSimulator

simulator = LfmcwSimulator(
    fc=77e9,              # 载波频率 (Hz)
    bandwidth=150e6,      # 带宽 (Hz)
    chirp_duration=50e-6, # Chirp持续时间 (s)
    fs=10e6,              # 采样率 (Hz)
    prf=5e3,              # 脉冲重复频率 (Hz)
    num_chirps=128        # Chirp数量
)

# 仿真
sim_result = simulator.simulate(targets, snr_db=30.0, seed=42)
```

---

## 🔍 常见问题解答

### Q: 如何改变雷达工作频率？
```python
simulator = LfmcwSimulator(fc=79e9, ...)  # 改为 79 GHz
```

### Q: 如何提高距离分辨率？
增加带宽：
```python
simulator = LfmcwSimulator(bandwidth=200e6, ...)  # 200 MHz
```

### Q: 如何检测更多目标？
提高信噪比或增加 RCS：
```python
sim_result = simulator.simulate(targets, snr_db=35.0, ...)
```

### Q: 如何保存数据用于后续分析？
```python
import numpy as np
np.save('rd_spectrum.npy', processed_result.range_doppler)
np.save('range_axis.npy', processed_result.range_axis)
```

### Q: 出现多普勒混叠怎么办？
降低目标速度或提高 PRF：
```python
simulator = LfmcwSimulator(prf=10e3, ...)  # 提高到 10 kHz
```

---

## 📊 性能参考

基于默认参数（77 GHz, 150 MHz 带宽, 128 chirps）：

| 指标 | 数值 |
|------|------|
| 距离分辨率 | 1.0 m |
| 最大探测距离 | 249 m |
| 速度分辨率 | 0.08 m/s |
| 最大不模糊速度 | ±4.79 m/s |
| 典型处理时间 | < 1秒 |

---

## 🛠️ 调试技巧

### 1. 检查中间结果
```python
# 查看基带数据形状
print(f"Baseband shape: {sim_result.baseband.shape}")

# 查看RD谱最大值
print(f"Max power: {np.max(processed_result.range_doppler):.2f}")
```

### 2. 验证物理合理性
```python
# 距离应该在 0 到 max_range 之间
assert 0 <= detected_range <= range_axis[-1]

# 速度应该在不模糊范围内
assert abs(detected_velocity) <= doppler_axis[-1]
```

### 3. 对比理论值
```python
# 理论距离分辨率
theoretical_resolution = 3e8 / (2 * 150e6)  # = 1.0 m
actual_resolution = range_axis[1] - range_axis[0]
print(f"Theory: {theoretical_resolution:.2f}m, Actual: {actual_resolution:.2f}m")
```

---

## 📖 延伸阅读

- **理论基础**
  - [base_rule.md](base_rule.md) - 架构设计原则
  - [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 技术总结
  
- **代码文档**
  - [contracts.py](contracts.py) - 数据契约定义
  - [README.md](README.md) - 完整API文档

- **在线资源**
  - NumPy 文档: https://numpy.org/doc/
  - Matplotlib 教程: https://matplotlib.org/stable/tutorials/

---

## 🎉 下一步

完成本教程后，你可以：

1. **贡献代码**
   - 添加新的波形类型
   - 实现新算法（CFAR、DOA等）
   - 优化性能

2. **实际应用**
   - 集成到实际系统
   - 硬件在环测试
   - 性能基准测试

3. **继续学习**
   - MIMO 雷达
   - 毫米波雷达阵列
   - 机器学习辅助检测

---

**祝你学习顺利！** 🚀

如有问题，请查阅示例代码中的注释和文档。
