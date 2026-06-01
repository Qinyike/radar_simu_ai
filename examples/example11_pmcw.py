"""
示例 11: PMCW 雷达仿真 - 真实汽车雷达参数

真实 77 GHz PMCW 车载雷达配置：
- 码片速率 250 Mchip/s → ΔR = 0.6 m
- m 序列 1023 chips → R_max = 614 m
- PRI = 50 μs（含 ~46 μs 保护间隔）→ PRF = 20 kHz
- v_max = ±19.5 m/s (±70 km/h)
- 256 脉冲 → 速度分辨率 0.15 m/s

对比 LFMCW：
  LFMCW: 线性调频斜坡 → 差频 → FFT
  PMCW:  BPSK 相位编码 → 匹配滤波 → Doppler FFT

PMCW 优势：
  - 自相关旁瓣极低（m 序列 ~-22 dB，Barker -22.3 dB）
  - 距离分辨率由码片速率独立控制
  - 无调频非线性问题
  - 多部雷达可通过不同码组实现码分复用
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import numpy as np
from simulators.pmcw_simulator import PmcwSimulator
from processors.pmcw_processor import process_pmcw
from visualizers.rd_visualizer import plot_comprehensive

print("=" * 70)
print("示例 11: PMCW 雷达仿真 — 真实汽车雷达参数")
print("=" * 70)

# ============================================================================
# 1. 创建 PMCW 仿真器（真实车载参数）
# ============================================================================
print("\n[1/4] 创建 PMCW 仿真器...")

sim = PmcwSimulator(
    fc=77e9,               # 77 GHz
    chip_rate=250e6,       # 250 Mchip/s
    code_type='mseq',      # m 序列（低自相关旁瓣）
    code_length=1023,      # 1023 chips (n=10, 2^10-1)
    pri=50e-6,             # PRI = 50 μs
    num_pulses=256,        # 256 个脉冲
)

print(f"  载波频率: {sim.fc/1e9:.0f} GHz")
print(f"  码片速率: {sim.chip_rate/1e6:.0f} Mchip/s")
print(f"  码型: m-sequence (n=10)")
print(f"  码长: {sim.code_length} chips")
print(f"  码持续时间: {sim.code_duration*1e6:.2f} μs")
print(f"  保护间隔: {sim.guard_interval*1e6:.2f} μs")
print(f"  PRI: {sim.pri*1e6:.1f} μs → PRF = {sim.prf/1e3:.1f} kHz")
print(f"  带宽: {sim.bandwidth/1e6:.0f} MHz")
print(f"  距离分辨率: {sim.c/(2*sim.bandwidth):.2f} m")
print(f"  最大不模糊距离: {sim.code_length * sim.c/(2*sim.bandwidth):.1f} m")
print(f"  最大不模糊速度: ±{sim.c*sim.prf/(4*sim.fc):.2f} m/s (±{sim.c*sim.prf/(4*sim.fc)*3.6:.0f} km/h)")
print(f"  速度分辨率: {2 * sim.c*sim.prf/(4*sim.fc) / sim.num_pulses:.3f} m/s")

# ============================================================================
# 2. 定义目标场景
# ============================================================================
print("\n[2/4] 定义目标场景...")

targets = [
    {"range": 25.0,  "velocity": 0.5,  "rcs": 15},   # 近距慢速（泊车场景）
    {"range": 80.0,  "velocity": -5.0, "rcs": 10},   # 中距快速靠近
    {"range": 200.0, "velocity": 2.0,  "rcs": 8},    # 远距慢速远离
    {"range": 350.0, "velocity": 0.0,  "rcs": 3},    # 超远距静止（桥梁）
]

print(f"  {'编号':<6}{'距离(m)':<10}{'速度(m/s)':<12}{'RCS(dBsm)':<10}")
print(f"  {'-'*38}")
for i, t in enumerate(targets, 1):
    print(f"  {i:<6}{t['range']:<10.0f}{t['velocity']:<12.1f}{t['rcs']:<10}")

# ============================================================================
# 3. 仿真与处理
# ============================================================================
print("\n[3/4] 运行仿真与信号处理...")

sim_result = sim.simulate(targets, snr_db=25.0, seed=42)
print(f"  ✓ 仿真完成，基带形状: {sim_result.baseband.shape}")

processed = process_pmcw(sim_result)
print(f"  ✓ 处理完成，RD 谱形状: {processed.range_doppler.shape}")
print(f"    距离轴: [{processed.range_axis[0]:.1f}, {processed.range_axis[-1]:.1f}] m")
print(f"    速度轴: [{processed.doppler_axis[0]:.2f}, {processed.doppler_axis[-1]:.2f}] m/s")

# 检测结果
rd = processed.range_doppler
print(f"\n  检测结果:")
print(f"  {'编号':<6}{'真实距离':<10}{'检测距离':<10}{'真实速度':<10}{'检测速度':<10}")
print(f"  {'-'*46}")
for i, t in enumerate(targets, 1):
    r_idx = np.argmin(np.abs(processed.range_axis - t['range']))
    d_slice = rd[r_idx, :]
    d_idx = np.argmax(d_slice)
    det_r = processed.range_axis[r_idx]
    det_v = processed.doppler_axis[d_idx]
    print(f"  {i:<6}{t['range']:<10.0f}{det_r:<10.1f}{t['velocity']:<10.1f}{det_v:<10.2f}")

# ============================================================================
# 4. 可视化
# ============================================================================
print("\n[4/4] 生成可视化图表...")

target_info = {
    'targets': [{"range": t['range'], "velocity": t['velocity'], "rcs": t['rcs']}
                for t in targets]
}

plot_comprehensive(
    processed,
    target_info=target_info,
    title="PMCW Automotive Radar (m-seq 1023, 250 Mchip/s, PRF 20 kHz)",
    save_path="./output/example11_pmcw.png",
    show=True
)
print("  ✓ 图表已保存")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 70)
print("示例完成！")
print("=" * 70)
print("\nPMCW vs LFMCW 对比（真实车载参数）:")
print(f"  {'参数':<20}{'LFMCW':<20}{'PMCW (m-1023)':<20}")
print(f"  {'-'*60}")
print(f"  {'载波频率':<20}{'77 GHz':<20}{'77 GHz':<20}")
print(f"  {'带宽/码片速率':<20}{'150 MHz':<20}{'250 Mchip/s':<20}")
print(f"  {'距离分辨率':<20}{'1.0 m':<20}{'0.6 m':<20}")
print(f"  {'最大不模糊距离':<20}{'399 m':<20}{'614 m':<20}")
print(f"  {'PRF':<20}{'20 kHz':<20}{'20 kHz':<20}")
print(f"  {'最大不模糊速度':<20}{'±19.3 m/s':<20}{'±19.5 m/s':<20}")
print(f"  {'速度分辨率':<20}{'0.15 m/s':<20}{'0.15 m/s':<20}")
print(f"  {'自相关旁瓣':<20}{'-13 dB (rect)':<20}{'~-22 dB':<20}")
print(f"  {'处理方式':<20}{'2D-FFT':<20}{'匹配滤波+FFT':<20}")
print(f"  {'多雷达共存':<20}{'困难（需错频）':<20}{'码分复用':<20}")
