# 代码示例集

本目录包含多个实用示例，帮助你快速上手使用雷达仿真框架。

## 📚 示例列表

### 示例 1: 基础使用 (`example1_basic.py`)
**适合人群**: 初学者  
**学习目标**: 了解如何运行最简单的雷达仿真

```bash
pixi run python examples/example1_basic.py
```

**主要内容**:
- 定义单个目标
- 运行仿真
- 查看结果

---

### 示例 2: 多目标场景 (`example2_multi_target.py`)
**适合人群**: 初级用户  
**学习目标**: 模拟真实的交通场景

```bash
pixi run python examples/example2_multi_target.py
```

**主要内容**:
- 配置多个目标（不同距离、速度、RCS）
- 分析检测结果
- 理解目标检测原理

---

### 示例 3: 参数调优 (`example3_parameter_tuning.py`)
**适合人群**: 中级用户  
**学习目标**: 探索雷达参数对性能的影响

```bash
pixi run python examples/example3_parameter_tuning.py
```

**主要内容**:
- 带宽对距离分辨率的影响
- Chirp 数量对速度分辨率的影响
- 参数对比可视化

---

### 示例 4: 信噪比分析 (`example4_snr_analysis.py`)
**适合人群**: 中级用户  
**学习目标**: 研究噪声对检测性能的影响

```bash
pixi run python examples/example4_snr_analysis.py
```

**主要内容**:
- 不同 SNR 条件下的检测能力
- 目标功率与噪声水平分析
- SIR（信干比）计算

---

### 示例 5: 自定义可视化 (`example5_custom_visualization.py`)
**适合人群**: 高级用户  
**学习目标**: 创建专业的雷达数据报告

```bash
pixi run python examples/example5_custom_visualization.py
```

**主要内容**:
- 多面板专业图表
- 系统参数展示
- 定制化报告格式

---

### 示例 6: 批量仿真 (`example6_batch_simulation.py`)
**适合人群**: 工程师/研究人员  
**学习目标**: 自动化测试多个场景

```bash
pixi run python examples/example6_batch_simulation.py
```

**主要内容**:
- 批量运行多个场景
- 自动生成测试报告
- JSON 格式结果导出

---

### 示例 7: 多普勒模糊可视化 (`example7_doppler_aliasing.py`)
**适合人群**: 中级/高级用户  
**学习目标**: 正确处理速度混叠目标的标注

```bash
pixi run python examples/example7_doppler_aliasing.py
```

**主要内容**:
- 计算多普勒模糊后的速度
- 不同目标使用不同颜色和标记
- 在 RD 谱上标注模糊位置（而非真实位置）
- 用虚线连接真实位置和模糊位置
- 清晰的图例说明

**特色功能**:
- ✅ 自动检测哪些目标会发生模糊
- ✅ 10种不同的标记样式和颜色
- ✅ 智能图例生成
- ✅ 模糊位置对比图

---
## 🚀 快速开始

### 第一步：运行基础示例

```bash
# 进入项目目录
cd radar_simu_ai

# 运行第一个示例
pixi run python examples/example1_basic.py
```

### 第二步：查看所有输出

生成的图表会保存在 `output/` 目录下：

```
output/
├── example1/              # 示例1的输出
│   ├── comprehensive.png
│   ├── range_doppler.png
│   └── range_profile.png
├── example2/              # 示例2的输出
├── example3_bandwidth_comparison.png
├── example3_chirps_comparison.png
├── example4_snr_analysis.png
├── example5_custom_visualization.png
└── example6_batch_results.json
```

### 第三步：修改和实验

打开任意示例文件，尝试修改参数：
- 改变目标位置和速度
- 调整雷达系统参数
- 修改信噪比
- 添加更多目标

---

## 💡 学习建议

### 初学者路径
1. ✅ 先运行 **示例1**，理解基本流程
2. ✅ 再运行 **示例2**，学习多目标场景
3. ✅ 阅读代码，理解每个参数的含义

### 进阶路径
1. ✅ 运行 **示例3**，学习参数调优
2. ✅ 运行 **示例4**，理解噪声影响
3. ✅ 尝试修改参数，观察效果变化

### 专家路径
1. ✅ 研究 **示例5**，学习自定义可视化
2. ✅ 使用 **示例6**，进行批量测试
3. ✅ 基于示例创建自己的应用

---

## 🔧 常见问题

### Q1: 如何更改雷达参数？

在创建仿真器时指定参数：

```python
from simulators import LfmcwSimulator

simulator = LfmcwSimulator(
    fc=77e9,           # 载波频率 77 GHz
    bandwidth=150e6,   # 带宽 150 MHz
    chirp_duration=50e-6,  # Chirp 持续时间 50 μs
    fs=10e6,           # 采样率 10 MHz
    prf=5e3,           # 脉冲重复频率 5 kHz
    num_chirps=128     # Chirp 数量 128
)
```

### Q2: 如何添加更多目标？

```python
targets = [
    {"range": 50.0, "velocity": 3.0, "rcs": 15},
    {"range": 100.0, "velocity": -5.0, "rcs": 10},
    {"range": 150.0, "velocity": 0.0, "rcs": 8},
]
```

### Q3: 如何提取原始数据？

```python
# 从处理结果中提取
rd_spectrum = processed_result.range_doppler      # RD谱
range_profile = processed_result.range_profile    # 距离剖面
range_axis = processed_result.range_axis          # 距离轴
doppler_axis = processed_result.doppler_axis      # 速度轴
```

### Q4: 如何保存自定义图表？

```python
import matplotlib.pyplot as plt

plt.savefig('my_plot.png', dpi=150, bbox_inches='tight')
```

---

## 📖 相关文档

- [README.md](../README.md) - 完整项目说明
- [QUICKSTART.md](../QUICKSTART.md) - 5分钟快速上手
- [PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md) - 技术总结
- [base_rule.md](../base_rule.md) - 架构设计指南

---

## 🎓 下一步

学完这些示例后，你可以：

1. **创建自己的应用场景**
   - 高速公路巡航控制
   - 城市道路防撞
   - 自动泊车辅助

2. **开发新算法**
   - CFAR 检测
   - DOA 估计
   - 目标跟踪

3. **集成到实际系统**
   - 实时数据处理
   - 硬件在环测试
   - 性能评估工具

---

**祝你学习愉快！** 🚗📡
