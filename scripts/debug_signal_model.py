"""
调试脚本：验证 LFMCW 信号模型
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from simulators import get_simulator
from processors import get_processor

# 创建仿真器
simulator = get_simulator("lfmcw")

# 单目标场景
targets = [{"range": 50.0, "velocity": 0.0, "rcs": 20}]

# 仿真
print("执行仿真...")
sim_result = simulator.simulate(targets=targets, snr_db=40.0, seed=42)

# 检查第一个 chirp 的频谱
chirp_0 = sim_result.baseband[0, 0, :]
fft_result = np.fft.fft(chirp_0)
fft_magnitude = np.abs(fft_result[:len(fft_result)//2])

# 找到峰值
peak_bin = np.argmax(fft_magnitude)
peak_freq = peak_bin * sim_result.fs / len(chirp_0)
expected_freq = simulator.chirp_slope * (2 * 50.0 / simulator.c)

print(f"\n=== 第一个 Chirp 的频谱分析 ===")
print(f"预期差频: {expected_freq/1e6:.2f} MHz")
print(f"检测到的峰值 bin: {peak_bin}")
print(f"检测到的频率: {peak_freq/1e6:.2f} MHz")
print(f"频率误差: {abs(peak_freq - expected_freq)/1e3:.2f} kHz")

# 查看前100个bin
print(f"\n前100个 FFT bin 的幅度 (dB):")
for i in range(40, 80, 5):
    mag_db = 20 * np.log10(fft_magnitude[i] + 1e-10)
    marker = " <-- PEAK" if i == peak_bin else ""
    print(f"  Bin {i:3d}: {mag_db:6.1f} dB{marker}")
