// 雷达仿真框架工程总结
// 项目: radar_simu_ai

#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2cm),
)
#set text(
  font: ("Times New Roman", "SimSun"),
  size: 11pt,
  lang: "zh",
)
#set heading(numbering: "1.")
#show heading.where(level: 1): set text(size: 18pt, weight: "bold")
#show heading.where(level: 2): set text(size: 14pt, weight: "bold")
#show heading.where(level: 3): set text(size: 12pt, weight: "bold")

#align(center)[
  #text(size: 22pt, weight: "bold")[汽车雷达 LFMCW/MIMO 仿真框架]
  #v(0.3cm)
  #text(size: 14pt)[工程总结报告]
  #v(0.2cm)
  #text(size: 11pt, style: "italic")[radar_simu_ai · v0.1.0]
  #v(0.1cm)
  #line(length: 60%)
]

#v(0.5cm)

= 项目概述

本项目是一个模块化的汽车雷达仿真框架，用于模拟 LFMCW（线性调频连续波）和 MIMO（多输入多输出）雷达系统。它面向汽车雷达算法开发、教学演示、研究验证和系统参数优化等场景。

#v(0.3cm)

#table(
  columns: (auto, auto),
  stroke: 0.5pt,
  inset: 6pt,
  [#strong[语言 / 运行时]], [#mono[Python 3.14]],
  [#strong[包管理器]], [#mono[Pixi] (conda-forge)],
  [#strong[平台]], [#mono[win-64]],
  [#strong[许可证]], [MIT],
  [#strong[作者]], [zenghui.li],
  [#strong[Python 文件数]], [38 个],
  [#strong[示例数]], [12 个],
  [#strong[文档数]], [15 个 Markdown],
)

#v(0.5cm)

= 核心架构

#v(0.3cm)

== 分层设计（自底向上）

#v(0.2cm)

#table(
  columns: (auto, auto, auto),
  stroke: 0.5pt,
  inset: 6pt,
  table.header(
    [#strong[层级]], [#strong[模块]], [#strong[职责]],
  ),
  [第 1 层 — 数据契约], [`contracts.py`], [定义层间通信核心数据结构：`Target`、`RadarConfig`、`SimResult`、`ProcessedResult`、`MimoAntennaArray`、`RadarSimulator`（抽象基类）],
  [第 2 层 — 波形仿真], [`simulators/`], [生成雷达基带回波信号：`LfmcwSimulator`、`MimoLfmcwSimulator`（TDMA/DDMA）],
  [第 3 层 — 信号处理], [`processors/`], [2D-FFT 处理流程：距离 FFT → 多普勒 FFT → RD 谱，DBF 角度估计],
  [第 4 层 — 可视化], [`visualizers/`], [生成 RD 谱热力图、距离剖面、天线阵列布局、角度谱、MIMO 综合图],
  [第 5 层 — 入口调度], [`main.py`], [流程编排、物理验证、日志输出],
)

#v(0.3cm)

== 数据流

#v(0.1cm)

#align(center)[
  #text(size: 10pt)[`配置参数` → `仿真器.simulate()` → `SimResult` → `处理器()` → `ProcessedResult` → `可视化函数` → `图表`]
]

#v(0.3cm)

== 核心设计原则

- *单向数据流*：配置 → 仿真 → 处理 → 可视化，不可逆
- *契约优先*：层间通过 `SimResult` 和 `ProcessedResult` 标准数据结构通信，含 `__post_init__` 验证
- *模块独立*：同层模块互不依赖；新增波形只需实现仿真器并注册，无需修改现有代码
- *无状态处理*：算法层全部使用纯函数（`range_fft`、`doppler_fft`）
- *注册表模式*：`simulators/__init__.py` 和 `processors/__init__.py` 统一管理

#v(0.5cm)

= 目录结构

#v(0.2cm)

#table(
  columns: (auto, auto),
  stroke: 0.5pt,
  inset: 5pt,
  [#mono[contracts.py]], [数据契约定义层（291 行）],
  [#mono[main.py]], [主入口 / 调度层（199 行）],
  [#mono[simulators/]], [波形仿真层（LFMCW + MIMO）],
  [#mono[processors/]], [信号处理层（LFMCW + MIMO + DBF）],
  [#mono[visualizers/]], [可视化层（RD 谱、距离剖面、天线阵列等）],
  [#mono[utils/]], [物理计算（多普勒、RCS） + 噪声 + 坐标轴],
  [#mono[examples/]], [12 个分级示例（入门 → 专家）],
  [#mono[tests/]], [契约测试 + 接口测试 + 物理验证],
  [#mono[scripts/]], [工具脚本（快速测试、调试）],
  [#mono[docs/]], [完整文档（教程、指南、参考）],
  [#mono[output/]], [图表输出目录],
  [#mono[pixi.toml]], [Pixi 环境配置],
)

#v(0.5cm)

= 三大仿真模式

#v(0.3cm)

== 模式一：LFMCW 基础仿真

#v(0.1cm)

经典汽车雷达配置（#mono[77 GHz]、#mono[150 MHz] 带宽、#mono[256 chirps]）：

#v(0.1cm)
- 参数：#mono[fc=77GHz, B=150MHz, T_c=40μs, fs=20MHz, PRF=20kHz, N_chirps=256]
- 信号模型：$phi = 2pi dot.op f_"beat" dot.op t_"fast" + 2pi dot.op f_"doppler" dot.op t_"slow"$
- 距离分辨率：#mono[1.0 m]；最大探测距离：#mono[~250 m]
- 速度分辨率：#mono[0.08 m/s]；最大不模糊速度：#mono[±4.79 m/s]

#v(0.2cm)

== 模式二：MIMO TDMA 仿真

#v(0.1cm)

时分多址 MIMO，典型 #mono[4T4R] 配置：

#v(0.1cm)
- 发射天线轮流激活，每个 chirp 分配一个 TX
- 虚拟阵列大小：#mono[4 × 4 = 16 通道]
- 有效 PRF = PRF / num_tx（速度模糊区间缩小）
- 支持 DBF 角度估计（#mono[±60°]），角度分辨率 #mono[1°]
- 适用于 *高角度分辨率* 场景

#v(0.2cm)

== 模式三：MIMO DDMA 仿真

#v(0.1cm)

频分多址（相位编码）MIMO：

#v(0.1cm)
- 所有 TX 同时发射，通过正交相位编码区分
- 有效 PRF = PRF（不模糊速度是 TDMA 的 #mono[4] 倍）
- 适用于 *高速度动态* 场景
- DDMA 解码：接收数据与共轭码序列相乘恢复各 TX 信号

#v(0.5cm)

= 信号处理流程

#v(0.3cm)

== LFMCW 2D-FFT 处理

#v(0.1cm)

#table(
  columns: (auto, auto, auto, auto),
  stroke: 0.5pt,
  inset: 5pt,
  table.header([步骤], [操作], [输入形状], [输出形状]),
  [距离 FFT], [快时间维 FFT + 加窗], [#mono[[1, N_chirps, N_samples]]], [#mono[[1, N_chirps, N_range]]],
  [多普勒 FFT], [慢时间维 FFT + 加窗], [#mono[[1, N_chirps, N_range]]], [#mono[[1, N_doppler, N_range]]],
  [转置 + 取模], [转为 2D 物理坐标], [#mono[[1, N_doppler, N_range]]], [#mono[[N_range, N_doppler]]],
  [距离剖面], [沿多普勒维取 max], [#mono[[N_range, N_doppler]]], [#mono[[N_range]]],
)

#v(0.3cm)

== MIMO TDMA 处理

#v(0.1cm)

- *虚拟阵列重构*：原始数据 #mono[[N_rx, total_chirps, N_samples]] → 按 TX 索引分组 → 重排为 #mono[[N_virtual, N_chirps/frame, N_samples]]
- *距离 FFT* → *多普勒 FFT*（有效 PRF = PRF / num_tx）
- *DBF 角度估计*：对虚拟阵列 × 导向矢量做波束扫描

#v(0.3cm)

== MIMO DDMA 处理

#v(0.1cm)

- *距离 FFT* 后直接 *DDMA 解码*：各 RX × 共轭码 → 分离 TX 通道
- *多普勒 FFT*（全 PRF）
- *DBF 角度估计*（同 TDMA）

#v(0.5cm)

= 示例体系

#v(0.2cm)

#table(
  columns: (auto, auto, auto),
  stroke: 0.5pt,
  inset: 5pt,
  table.header([编号], [名称], [适用人群 / 学习目标]),
  [示例 1], [`example1_basic.py`], [初学者 — 单目标基础仿真],
  [示例 2], [`example2_multi_target.py`], [初级 — 高速公路多目标场景],
  [示例 3], [`example3_parameter_tuning.py`], [中级 — 带宽/Chirp 数对分辨率影响的参数扫描],
  [示例 4], [`example4_snr_analysis.py`], [中级 — 信噪比对检测性能影响],
  [示例 5], [`example5_custom_visualization.py`], [高级 — 专业多面板报表],
  [示例 6], [`example6_batch_simulation.py`], [工程师 — 批量仿真 + JSON 导出],
  [示例 7], [`example7_doppler_aliasing.py`], [中/高级 — 多普勒模糊可视化与标注],
  [示例 9], [`example9_mimo_tdma.py`], [雷达工程师 — MIMO TDMA + DBF 角度估计],
  [示例 10], [`example10_mimo_ddma.py`], [雷达工程师 — MIMO DDMA + TDMA 对比],
  [示例 11], [`example11_pmcw.py`], [雷达工程师 — PMCW 相位编码波形],
  [示例 12], [`example12_interference.py`], [雷达工程师 — 雷达间干扰仿真],
  [示例 13], [`example13_interactive.py`], [雷达工程师 — 交互式可视化],
)

#v(0.5cm)

= 性能指标

#v(0.2cm)

#table(
  columns: (auto, auto),
  stroke: 0.5pt,
  inset: 5pt,
  [#strong[参数]], [#strong[值（LFMCW 默认配置）]],
  [载波频率 $f_c$], [#mono[77 GHz]],
  [信号带宽 $B$], [#mono[150 MHz]],
  [距离分辨率 $Delta R$], [#mono[1.00 m]],
  [最大探测距离 $R_max$], [#mono[~250 m]],
  [速度分辨率 $Delta v$], [#mono[~0.08 m/s]],
  [最大不模糊速度 $v_max$], [#mono[±4.79 m/s]（LFMCW）/ ±1.20 m/s（TDMA）/ ±4.79 m/s（DDMA）],
  [MIMO 虚拟阵列], [#mono[4T4R → 16 通道]],
  [DBF 角度范围], [#mono[±60°]],
  [DBF 角度分辨率], [#mono[1°]],
)

#v(0.5cm)

= 测试验证

#v(0.2cm)

#table(
  columns: (auto, auto, auto),
  stroke: 0.5pt,
  inset: 5pt,
  table.header([测试类型], [文件], [验证内容]),
  [契约测试], [`tests/test_contracts.py`], [`SimResult` / `ProcessedResult` 数据结构完整性],
  [接口测试], [`tests/test_all.py`], [仿真器 / 处理器的输入输出接口],
  [物理验证], [`main.py`], [检测距离误差 #mono[0.00 m]，速度误差 #mono[0.03 m/s]（在分辨率范围内）],
  [快速测试], [`scripts/test_mimo_quick.py`], [MIMO 仿真器快速冒烟测试],
)

#v(0.5cm)

= 技术栈

#v(0.2cm)

#table(
  columns: (auto, auto, auto),
  stroke: 0.5pt,
  inset: 5pt,
  [#strong[组件]], [#strong[版本]], [#strong[用途]],
  [Python], [#mono[3.14]], [运行时],
  [NumPy], [#mono[>=2.4.6]], [数值计算 / FFT / 矩阵运算],
  [SciPy], [#mono[>=1.17.1]], [科学计算 / 信号处理],
  [Matplotlib], [#mono[>=3.10.9]], [数据可视化 / 图表生成],
  [Pixi], [最新], [包管理与虚拟环境],
)

#v(0.5cm)

= 关键物理公式

#v(0.2cm)

#table(
  columns: (auto, auto),
  stroke: 0.5pt,
  inset: 5pt,
  [距离分辨率], [$Delta R = c / (2 B)$],
  [最大探测距离], [$R_"max" = c dot.op f_s / (2 dot.op K)$，其中 $K = B / T_c$],
  [速度分辨率], [$Delta v = lambda / (2 dot.op T_"frame")$，其中 $lambda = c / f_c$],
  [最大不模糊速度], [$v_"max" = (c dot.op PRF) / (4 f_c)$],
  [多普勒频率], [$f_d = (2 v f_c) / c$],
  [差拍频率], [$f_"beat" = K dot.op tau = (B / T_c) dot.op (2R / c)$],
  [RCS 转幅度], [$A = 10^(RCS_("dBsm") / 20)$],
  [导向矢量], [$a(theta) = e^(j dot.op k dot.op x dot.op sin(theta))$，其中 $k = 2pi / lambda$],
)

#v(0.5cm)

= 扩展性

添加新波形只需 3 步：

#v(0.1cm)

+ 实现仿真器：`simulators/new_waveform.py`（继承或遵循 `RadarSimulator` 接口，返回 `SimResult`）
+ 注册仿真器：在 `simulators/__init__.py` 中添加一行 `register_simulator("new", NewWaveformSimulator)`
+ 实现处理器：`processors/new_waveform_processor.py`（接受 `SimResult`，返回 `ProcessedResult`）

#v(0.1cm)

*无需修改任何现有代码。*

#v(0.5cm)

= 已完成功能与待扩展

#v(0.2cm)

#strong[已完成：]

#v(0.1cm)

+ LFMCW 波形仿真（多目标、RCS、SNR 可配）
+ MIMO TDMA / DDMA 仿真（#mono[4T4R]）
+ DBF 数字波束形成角度估计（#mono[±60°]、#mono[1°] 分辨率）
+ 2D-FFT 信号处理（距离 + 多普勒）
+ 多种窗函数（Hamming / Hanning / Blackman / Taylor / Kaiser）
+ 多普勒模糊检测与可视化
+ 12 个分级示例 + 完整文档
+ 契约验证 + 单元测试 + 物理验证
+ 批量仿真 + JSON 结果导出

#v(0.3cm)

#strong[可扩展方向：]

#v(0.1cm)

+ CFAR（恒虚警率）目标检测算法
+ 超分辨 DOA 估计（MUSIC / ESPRIT）
+ 杂波建模（地物 / 海杂波）
+ 目标跟踪（Kalman / 粒子滤波）
+ FMCW 快速锯齿波模式
+ 实时可视化界面
+ 硬件在环（HIL）测试集成

#v(0.8cm)

#align(center)[
  #line(length: 60%)
  #v(0.2cm)
  #text(size: 9pt, style: "italic")[
    报告由 Hermes Agent 自动生成 · #datetime.now().display()
  ]
]
