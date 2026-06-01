# LFMCW 雷达仿真框架

一个模块化的汽车雷达 LFMCW（线性调频连续波）仿真框架，支持 MIMO、TDMA/DDMA 波形和 DBF 角度估计。

## ✨ 主要特性

- **模块化设计**: 仿真器、处理器、可视化分离
- **MIMO 支持**: 4T4R 配置，TDMA/DDMA 波形
- **DBF 角度估计**: 高精度角度测量（±60°）
- **丰富的示例**: 9+ 完整示例代码
- **完善的文档**: 详细的使用指南和教程

## 🚀 快速开始

### 安装依赖

```bash
# 使用 Pixi（推荐）
pixi install

# 或使用 pip
pip install numpy scipy matplotlib
```

### 运行示例

```bash
# 运行主程序
pixi run python main.py

# 运行示例 1（基础仿真）
pixi run python examples/example1_basic.py

# 运行 MIMO 示例
pixi run python examples/example9_mimo_tdma.py
```

### 运行测试

```bash
# 运行所有测试
pixi run test

# 运行快速测试
pixi run python scripts/test_mimo_quick.py
```

## 📁 项目结构

```
radar_simu_ai/
├── docs/                    # 📚 文档
│   ├── README.md           # 文档索引
│   ├── QUICKSTART.md       # 快速开始
│   ├── TUTORIAL.md         # 详细教程
│   ├── MIMO_GUIDE.md       # MIMO 指南
│   └── ...                 # 其他文档
├── scripts/                 # 🛠️ 工具和测试脚本
│   ├── test_mimo_quick.py  # MIMO 快速测试
│   ├── run_examples.bat    # Windows 批处理
│   ├── run_examples.sh     # Linux/Mac Shell
│   └── ...                 # 其他脚本
├── simulators/              # 📡 仿真器模块
│   ├── lfmcw_simulator.py  # LFMCW 仿真器
│   └── mimo_simulator.py   # MIMO 仿真器
├── processors/              # 🔧 处理器模块
│   ├── lfmcw_processor.py  # LFMCW 处理器
│   └── mimo_processor.py   # MIMO 处理器
├── visualizers/             # 📊 可视化工具
│   └── rd_visualizer.py    # RD 谱可视化工具
├── examples/                # 💡 示例代码
│   ├── example1_basic.py   # 基础仿真
│   ├── example2_multi_target.py  # 多目标
│   ├── ...
│   └── example9_mimo_tdma.py     # MIMO TDMA
├── tests/                   # ✅ 单元测试
│   └── test_contracts.py   # 契约测试
├── contracts.py             # 📋 数据契约
├── main.py                  # 🚀 主程序入口
├── base_rule.md             # 📖 基础规则
├── pixi.toml                # ⚙️ Pixi 配置
└── output/                  # 📤 输出目录
```

## 📖 文档

所有文档都在 [docs/](docs/) 目录中：

- **[快速开始](docs/QUICKSTART.md)** - 5 分钟上手
- **[详细教程](docs/TUTORIAL.md)** - 完整学习路径
- **[MIMO 指南](docs/MIMO_GUIDE.md)** - MIMO 雷达使用指南
- **[快速参考](docs/QUICK_REFERENCE.md)** - API 速查表
- **[示例说明](docs/EXAMPLES_SUMMARY.md)** - 所有示例介绍

## 💻 核心功能

### 1. LFMCW 仿真

```python
from simulators import LfmcwSimulator
from processors import process_lfmcw

# 创建仿真器
simulator = LfmcwSimulator(fc=77e9, bandwidth=150e6)

# 定义目标
targets = [{"range": 50.0, "velocity": 3.0, "rcs": 15}]

# 运行仿真
sim_result = simulator.simulate(targets, snr_db=25.0)

# 处理数据
processed = process_lfmcw(sim_result)
```

### 2. MIMO 仿真（4T4R）

```python
import numpy as np
from simulators.mimo_simulator import MimoLfmcwSimulator, MimoAntennaArray
from processors.mimo_processor import process_mimo, mimo_dbf_angle_estimation

# 创建 4T4R 配置
antenna_array = MimoAntennaArray(num_tx=4, num_rx=4, fc=77e9)

# 创建 MIMO 仿真器
mimo_sim = MimoLfmcwSimulator(
    antenna_array=antenna_array,
    waveform_mode='tdma',  # 或 'ddma'
    fc=77e9, bandwidth=150e6,
    chirp_duration=50e-6, fs=10e6,
    prf=5e3, num_chirps_per_frame=128
)

# 定义目标（必须包含 angle）
targets = [
    {"range": 50.0, "velocity": 3.0, 
     "angle": np.radians(10), "rcs": 15},
]

# 运行仿真
sim_result = mimo_sim.simulate(targets, snr_db=25.0)

# 处理数据
processed = process_mimo(sim_result)

# DBF 角度估计
dbf_result = mimo_dbf_angle_estimation(processed)
```

## 🎯 应用场景

- **汽车雷达算法开发**: FMCW/MIMO 雷达信号处理
- **教学演示**: 雷达原理可视化
- **研究验证**: 新算法原型验证
- **参数优化**: 系统参数调优

## 🛠️ 技术栈

- **Python 3.10+**
- **NumPy**: 数值计算
- **SciPy**: 科学计算
- **Matplotlib**: 数据可视化
- **Pixi**: 包管理和环境工具

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，欢迎通过 GitHub Issues 联系。

---

**📚 更多详情请查看 [docs/README.md](docs/README.md)**
