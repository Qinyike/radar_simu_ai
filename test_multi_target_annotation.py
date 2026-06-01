"""
测试多目标标注和多普勒模糊可视化
"""

import sys
import os
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from simulators import LfmcwSimulator
from processors import process_lfmcw
from visualizers.rd_visualizer import plot_comprehensive
import numpy as np

print("=" * 70)
print("测试：多目标标注和多普勒模糊可视化")
print("=" * 70)

# 创建仿真器
simulator = LfmcwSimulator(
    fc=77e9,
    bandwidth=150e6,
    chirp_duration=50e-6,
    fs=10e6,
    prf=5e3,
    num_chirps=128
)

# 计算最大不模糊速度
max_velocity = simulator.c * simulator.prf / (4 * simulator.fc)
print(f"\n系统参数:")
print(f"  PRF: {simulator.prf/1e3:.1f} kHz")
print(f"  最大不模糊速度: ±{max_velocity:.2f} m/s")

# 定义多个目标（包含会模糊的目标）
targets = [
    {"range": 50.0, "velocity": 3.0, "rcs": 18},     # 不模糊
    {"range": 100.0, "velocity": -8.0, "rcs": 15},   # 会模糊（超过 max_velocity）
    {"range": 150.0, "velocity": 2.0, "rcs": 12},    # 不模糊
]

print(f"\n目标配置:")
for i, target in enumerate(targets, 1):
    v = target['velocity']
    is_aliased = abs(v) > max_velocity
    status = "⚠ ALIASED" if is_aliased else "✓ OK"
    print(f"  目标 {i}: R={target['range']:4.0f}m, V={v:5.1f}m/s {status}")

# 运行仿真
print("\n正在运行仿真...")
sim_result = simulator.simulate(targets, snr_db=25.0, seed=42)
processed = process_lfmcw(sim_result)

print("✓ 仿真完成")

# 准备目标信息
target_info = {'targets': targets}

# 生成可视化
print("\n生成可视化图表...")
plot_comprehensive(
    processed,
    target_info=target_info,
    title="Multi-Target Detection with Doppler Aliasing",
    save_path="./output/test_multi_target_annotation.png",
    show=False
)

print("✓ 图表已保存到 ./output/test_multi_target_annotation.png")

# 分析检测结果
print("\n" + "=" * 70)
print("检测结果分析:")
print("=" * 70)

rd_spectrum = processed.range_doppler
range_axis = processed.range_axis
doppler_axis = processed.doppler_axis

# 找到所有局部峰值
from scipy.ndimage import maximum_filter

# 简单的峰值检测：找前 N 个最强点
rd_flat = rd_spectrum.flatten()
top_indices = np.argsort(rd_flat)[-len(targets):][::-1]

print(f"\n检测到的 {len(targets)} 个最强目标:")
for rank, idx in enumerate(top_indices, 1):
    range_idx, doppler_idx = np.unravel_index(idx, rd_spectrum.shape)
    R = range_axis[range_idx]
    V = doppler_axis[doppler_idx]
    power_db = 20 * np.log10(rd_spectrum[range_idx, doppler_idx] + 1e-10)
    
    print(f"  {rank}. R={R:6.1f}m, V={V:6.2f}m/s, Power={power_db:5.1f}dB")

print("\n✓ 测试完成！请查看生成的图表验证标注效果。")
