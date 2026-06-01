# 汽车雷达 LFMCW 仿真框架

基于分层架构设计的可扩展、可维护的雷达仿真系统。

## 🚀 快速开始

**新手？从这里开始！**

1. 📖 [5分钟快速上手](QUICKSTART.md) - 了解项目概况
2. 🎓 [完整教程](TUTORIAL.md) - 从入门到精通的学习路径
3. 💻 [代码示例集](examples/README.md) - 6个实用示例教你如何使用

或者直接运行：
```bash
# Windows
run_examples.bat

# Linux/Mac
chmod +x run_examples.sh
./run_examples.sh
```

---

## 📋 项目概述

本项目实现了一个遵循严格分层架构的汽车雷达 LFMCW（线性调频连续波）仿真框架，使得新增功能（如新算法、新波形）像"插入模块"一样简单。

## 🏗️ 架构设计

### 分层结构（从底到顶）

```
┌─────────────────────────────────────┐
│   入口/调度层 (main.py)              │  ← 配置解析、流程编排
├─────────────────────────────────────┤
│   可视化/输出层 (visualizers/)       │  ← 图表绘制、结果输出
├─────────────────────────────────────┤
│   信号处理/算法层 (processors/)      │  ← FFT、CFAR、DOA 等算法
├─────────────────────────────────────┤
│   波形生成/仿真层 (simulators/)      │  ← LFMCW、FMCW 等波形仿真
├─────────────────────────────────────┤
│   数据定义/契约层 (contracts.py)     │  ← SimResult, ProcessedResult
└─────────────────────────────────────┘
```

### 核心设计原则

1. **单向数据流**: 配置 → 仿真 → 处理 → 可视化
2. **统一接口契约**: 层间通过 `SimResult` 和 `ProcessedResult` 通信
3. **模块独立**: 同层模块互不依赖
4. **无状态处理**: 算法层使用纯函数
5. **注册表模式**: 通过注册表管理模块，无需修改核心代码

## 📁 项目结构

```
radar_simu_ai/
├── contracts.py                  # 数据契约定义
├── main.py                       # 主程序入口
├── simulators/
│   ├── __init__.py              # 仿真器注册表
│   └── lfmcw_simulator.py       # LFMCW 仿真器
├── processors/
│   ├── __init__.py              # 处理器注册表
│   └── lfmcw_processor.py       # LFMCW 信号处理器
├── visualizers/
│   ├── __init__.py              # 可视化工具
│   └── rd_visualizer.py         # 距离-多普勒可视化
├── tests/
│   ├── __init__.py
│   └── test_contracts.py        # 单元测试
├── output/                       # 输出图表目录
├── base_rule.md                  # 架构指南
└── README.md                     # 本文件
```

## 🚀 快速开始

### 安装依赖

```bash
pip install numpy matplotlib
```

### 运行仿真

```bash
python main.py
```

这将执行：
1. 配置三目标场景（50m、100m、150m）
2. 生成 LFMCW 回波数据
3. 执行 2D-FFT 信号处理
4. 显示距离-多普勒谱和距离剖面图
5. 保存图表到 `output/` 目录

### 运行测试

```bash
python tests/test_contracts.py
```

测试包括：
- ✓ 契约完整性验证
- ✓ 模块接口测试
- ✓ 物理正确性验证

## 💡 使用示例

### 自定义目标场景

```python
from main import run_simulation

# 定义自己的目标场景
targets = [
    {"range": 30.0, "velocity": 15.0, "rcs": 10},   # 近距离快速目标
    {"range": 80.0, "velocity": -5.0, "rcs": 5},    # 中距离慢速目标
]

# 运行仿真
sim_result, processed_result = run_simulation(
    waveform_type="lfmcw",
    targets=targets,
    snr_db=25.0,
    seed=123,
    visualize=True,
    save_plots=True
)
```

### 添加新波形（扩展性演示）

只需三步：

1. **实现仿真器** (`simulators/new_waveform.py`)
```python
from contracts import SimResult

class NewWaveformSimulator:
    def simulate(self, targets, ...):
        # 实现仿真逻辑
        return SimResult(...)
```

2. **注册仿真器** (`simulators/__init__.py`)
```python
SIMULATOR_REGISTRY = {
    "lfmcw": create_automotive_lfmcw_simulator,
    "new_waveform": create_new_waveform_simulator,  # 新增
}
```

3. **实现处理器** (`processors/new_waveform_processor.py`)
```python
from contracts import ProcessedResult

def process_new_waveform(sim_result):
    # 实现处理逻辑
    return ProcessedResult(...)
```

**无需修改任何现有代码！**

## 🔬 技术细节

### LFMCW 参数（默认）

| 参数 | 值 | 说明 |
|------|-----|------|
| 载波频率 | 77 GHz | 汽车雷达频段 |
| 带宽 | 150 MHz | 决定距离分辨率 |
| Chirp 持续时间 | 50 μs | 单个调频周期 |
| 采样率 | 10 MHz | ADC 采样率 |
| PRF | 5 kHz | 脉冲重复频率 |
| Chirp 数量 | 128 | 决定速度分辨率 |

### 性能指标

- **距离分辨率**: ~1 m（取决于带宽）
- **最大探测距离**: ~200 m（取决于采样率）
- **速度分辨率**: ~0.5 m/s（取决于 chirp 数量）
- **最大探测速度**: ±50 m/s（取决于 PRF）

## 🧪 测试策略

### 分层测试

1. **契约测试**: 验证数据结构类型和完整性
2. **接口测试**: 验证模块输入输出符合契约
3. **算法验证**: 验证数学计算正确性
4. **物理验证**: 验证检测结果与已知目标一致
5. **集成测试**: 验证完整流程正常工作

## 📝 开发规范

### 添加新功能自查清单

- [ ] 是否在已有层次内工作？
- [ ] 是否明确了输入输出契约？
- [ ] 输出是否严格遵循统一格式？
- [ ] 是否避免了对同层其他模块的依赖？
- [ ] 是否通过注册表（而非修改核心代码）启用新功能？
- [ ] 是否编写了独立的测试？

### 代码风格

- 使用类型提示
- 编写 docstring
- 遵循单向依赖原则
- 保持模块无状态

## 📖 参考资料

- [base_rule.md](base_rule.md) - 详细架构指南
- 《雷达系统导论》- Merrill Skolnik
- 《Automotive Radar Signal Processing》- 相关论文

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

**架构心法**: 现在多花 20% 的时间定义清晰的边界和契约，未来每次修改和扩展时，就能节省 80% 的调试和重构成本。
