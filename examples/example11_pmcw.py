"""
示例 11: PMCW 雷达仿真 - 相位编码连续波

PMCW (Phase Modulated Continuous Wave) 使用伪随机相位编码序列：
- Barker-13 码：13 chips，自相关旁瓣极低（-22.3 dB）
- m 序列：127 chips，长码获得更远的最大探测距离

对比 LFMCW：
- LFMCW: 调频斜坡 → 差频 → FFT
- PMCW: 相位编码 → 匹配滤波（相关）→ Doppler FFT

真实 77GHz 车载雷达参数：
- 码片速率 50 Mchip/s → 距离分辨率 3 m
- Barker-13: 最大不模糊距离 39 m（短距高精度场景）
- m-127: 最大不模糊距离 381 m（长距场景）
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
print("示例 11: PMCW 雷达仿真")
print("=" * 70)

# ============================================================================
# 1. Barker-13 码仿真（短距高精度）
# ============================================================================
print("\n[1/3] Barker-13 码仿真（短距场景）...")

sim_barker = PmcwSimulator(
    fc=77e9,
    chip_rate=50e6,          # 50 Mchip/s
    code_type='barker',
    code_length=13,           # 13 chips
    num_pulses=128,
)

print(f"  码型: Barker-13")
print(f"  码长: {sim_barker.code_length} chips")
print(f"  码片速率: {sim_barker.chip_rate/1e6:.0f} Mchip/s")
print(f"  带宽: {sim_barker.bandwidth/1e6:.0f} MHz")
print(f"  距离分辨率: {sim_barker.c/(2*sim_barker.bandwidth):.2f} m")
print(f"  最大不模糊距离: {sim_barker.code_length * sim_barker.c/(2*sim_barker.bandwidth):.1f} m")
print(f"  PRF: {sim_barker.prf:.0f} Hz")
print(f"  最大不模糊速度: ±{sim_barker.c*sim_barker.prf/(4*sim_barker.fc):.2f} m/s")

targets_barker = [
    {"range": 15.0, "velocity": 1.5, "rcs": 10},
    {"range": 30.0, "velocity": -1.0, "rcs": 5},
]

print(f"\n  目标:")
for i, t in enumerate(targets_barker, 1):
    print(f"    T{i}: R={t['range']}m, V={t['velocity']}m/s, RCS={t['rcs']}dBsm")

sim_result_b = sim_barker.simulate(targets_barker, snr_db=25.0, seed=42)
processed_b = process_pmcw(sim_result_b)

print(f"  ✓ 处理完成")
print(f"    RD 谱形状: {processed_b.range_doppler.shape}")

# 检测
rd = processed_b.range_doppler
for t in targets_barker:
    r_idx = np.argmin(np.abs(processed_b.range_axis - t['range']))
    d_slice = rd[r_idx, :]
    d_idx = np.argmax(d_slice)
    det_v = processed_b.doppler_axis[d_idx]
    print(f"    T(R={t['range']}m) → 检测速度 {det_v:.2f} m/s (真实 {t['velocity']} m/s)")

# ============================================================================
# 2. m-127 序列仿真（长距场景）
# ============================================================================
print("\n[2/3] m-127 序列仿真（长距场景）...")

sim_mseq = PmcwSimulator(
    fc=77e9,
    chip_rate=50e6,
    code_type='mseq',
    code_length=127,          # 127 chips
    num_pulses=256,
)

print(f"  码型: m-sequence")
print(f"  码长: {sim_mseq.code_length} chips")
print(f"  距离分辨率: {sim_mseq.c/(2*sim_mseq.bandwidth):.2f} m")
print(f"  最大不模糊距离: {sim_mseq.code_length * sim_mseq.c/(2*sim_mseq.bandwidth):.1f} m")
print(f"  PRF: {sim_mseq.prf:.0f} Hz")
print(f"  最大不模糊速度: ±{sim_mseq.c*sim_mseq.prf/(4*sim_mseq.fc):.2f} m/s")

targets_mseq = [
    {"range": 40.0, "velocity": 1.5, "rcs": 10},
    {"range": 100.0, "velocity": -2.5, "rcs": 8},
    {"range": 200.0, "velocity": 0.0, "rcs": 3},
]

print(f"\n  目标:")
for i, t in enumerate(targets_mseq, 1):
    print(f"    T{i}: R={t['range']}m, V={t['velocity']}m/s, RCS={t['rcs']}dBsm")

sim_result_m = sim_mseq.simulate(targets_mseq, snr_db=25.0, seed=42)
processed_m = process_pmcw(sim_result_m)

print(f"  ✓ 处理完成")
print(f"    RD 谱形状: {processed_m.range_doppler.shape}")

rd = processed_m.range_doppler
for t in targets_mseq:
    r_idx = np.argmin(np.abs(processed_m.range_axis - t['range']))
    d_slice = rd[r_idx, :]
    d_idx = np.argmax(d_slice)
    det_v = processed_m.doppler_axis[d_idx]
    print(f"    T(R={t['range']}m) → 检测速度 {det_v:.2f} m/s (真实 {t['velocity']} m/s)")

# ============================================================================
# 3. 可视化
# ============================================================================
print("\n[3/3] 生成可视化图表...")

target_info_b = {
    'targets': [{"range": t['range'], "velocity": t['velocity'], "rcs": t['rcs']}
                for t in targets_barker]
}
plot_comprehensive(
    processed_b,
    target_info=target_info_b,
    title="PMCW Radar (Barker-13, 50 Mchip/s)",
    save_path="./output/example11_pmcw_barker13.png",
    show=False
)
print("  ✓ Barker-13 图已保存")

target_info_m = {
    'targets': [{"range": t['range'], "velocity": t['velocity'], "rcs": t['rcs']}
                for t in targets_mseq]
}
plot_comprehensive(
    processed_m,
    target_info=target_info_m,
    title="PMCW Radar (m-sequence 127, 50 Mchip/s)",
    save_path="./output/example11_pmcw_mseq127.png",
    show=True
)
print("  ✓ m-127 图已保存")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 70)
print("示例完成！")
print("=" * 70)
print("\nPMCW vs LFMCW 对比:")
print(f"  {'参数':<22}{'LFMCW':<18}{'PMCW Barker-13':<18}{'PMCW m-127':<18}")
print(f"  {'-'*76}")
print(f"  {'调制方式':<22}{'线性调频':<18}{'BPSK 相位编码':<18}{'BPSK 相位编码':<18}")
print(f"  {'距离分辨率':<22}{'1.0 m':<18}{'3.0 m':<18}{'3.0 m':<18}")
print(f"  {'最大不模糊距离':<22}{'399 m':<18}{'39 m':<18}{'381 m':<18}")
print(f"  {'自相关旁瓣':<22}{'-13 dB (rect)':<18}{'-22.3 dB':<18}{'-22 dB (approx)':<18}")
print(f"  {'处理方式':<22}{'FFT':<18}{'匹配滤波+FFT':<18}{'匹配滤波+FFT':<18}")
