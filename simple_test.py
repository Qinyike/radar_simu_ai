"""
简单测试：验证距离检测
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from simulators import get_simulator
from processors import range_fft, compute_range_axis

# 创建仿真器
simulator = get_simulator("lfmcw")

# 单目标场景（静止）
targets = [{"range": 50.0, "velocity": 0.0, "rcs": 20}]

# 仿真
sim_result = simulator.simulate(targets=targets, snr_db=40.0, seed=42)

# 只做距离 FFT
baseband = sim_result.baseband
range_fft_data = range_fft(baseband, window="hamming")

# 查看第一个 chirp 的结果
first_chirp_fft = range_fft_data[0, 0, :]
peak_bin = np.argmax(np.abs(first_chirp_fft))

print(f"真实距离: 50.0 m")
print(f"检测到的峰值 bin: {peak_bin}")
print(f"FFT 结果长度: {len(first_chirp_fft)}")

# 计算距离轴
range_axis = compute_range_axis(sim_result.fs, sim_result.bandwidth, 
                                sim_result.samples_per_chirp, sim_result.c, 
                                use_positive_only=True)
print(f"距离轴长度: {len(range_axis)}")
print(f"检测到的距离: {range_axis[peak_bin]:.2f} m")
print(f"距离分辨率: {range_axis[1] - range_axis[0]:.2f} m")

# 查看 bin 45-55 的能量
print(f"\nBin 45-55 的能量 (dB):")
for i in range(45, 56):
    energy_db = 20 * np.log10(np.abs(first_chirp_fft[i]) + 1e-10)
    marker = " <-- PEAK" if i == peak_bin else ""
    print(f"  Bin {i:3d} ({range_axis[i]:5.1f}m): {energy_db:6.1f} dB{marker}")
