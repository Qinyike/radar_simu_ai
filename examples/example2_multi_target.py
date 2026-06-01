"""
示例 2: 多目标场景 - 模拟真实的交通场景

这个示例展示如何设置多个目标，模拟高速公路上的车辆。
包括不同距离、速度和 RCS 的目标。
"""

import sys
import os
# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from main import run_simulation
import numpy as np

print("=" * 70)
print("示例 2: 多目标交通场景仿真")
print("=" * 70)

# 定义复杂的交通场景
targets = [
    # 近距离快速接近的车辆（可能是对向来车）
    {"range": 30.0, "velocity": -15.0, "rcs": 20},   # 30m, -54 km/h (靠近)
    
    # 中距离同向行驶的车辆
    {"range": 80.0, "velocity": 5.0, "rcs": 15},     # 80m, 18 km/h (远离)
    
    # 远距离静止物体（路标或护栏）
    {"range": 120.0, "velocity": 0.0, "rcs": 10},    # 120m, 静止
    
    # 很远的弱反射目标（行人或自行车）
    {"range": 150.0, "velocity": 2.0, "rcs": 5},     # 150m, 7.2 km/h
    
    # 超远距离的强反射目标（大型车辆）
    {"range": 200.0, "velocity": 4.0, "rcs": 25},    # 200m, 14.4 km/h
]

print(f"\n场景配置:")
print(f"  目标数量: {len(targets)}")
for i, target in enumerate(targets, 1):
    speed_kmh = target['velocity'] * 3.6  # 转换为 km/h
    direction = "→" if target['velocity'] > 0 else ("←" if target['velocity'] < 0 else "•")
    print(f"  目标 {i}: {target['range']:4.0f}m, "
          f"{direction} {abs(speed_kmh):5.1f} km/h, "
          f"RCS={target['rcs']}dBsm")

# 运行仿真
print("\n正在运行仿真...")
sim_result, processed_result = run_simulation(
    waveform_type="lfmcw",
    targets=targets,
    snr_db=20.0,      # 较低的信噪比，更接近真实环境
    seed=123,
    visualize=True,
    save_plots=True,
    output_dir="./output/example2"
)

# 分析检测结果
print("\n" + "=" * 70)
print("检测结果分析:")
print("=" * 70)

rd_spectrum = processed_result.range_doppler
range_axis = processed_result.range_axis
doppler_axis = processed_result.doppler_axis

# 找到所有局部峰值（简化版：找前5个最强目标）
rd_flat = rd_spectrum.flatten()
top_indices = np.argsort(rd_flat)[-5:][::-1]  # 最强的5个点

print("\n检测到的最强5个目标:")
for rank, idx in enumerate(top_indices, 1):
    range_idx, doppler_idx = np.unravel_index(idx, rd_spectrum.shape)
    R = range_axis[range_idx]
    V = doppler_axis[doppler_idx]
    power_db = 20 * np.log10(rd_spectrum[range_idx, doppler_idx] + 1e-10)
    
    speed_kmh = V * 3.6
    direction = "→" if V > 0 else ("←" if V < 0 else "•")
    
    print(f"  {rank}. 距离: {R:6.1f}m, "
          f"速度: {direction} {abs(speed_kmh):5.1f} km/h, "
          f"功率: {power_db:5.1f} dB")

print(f"\n✓ 仿真完成！图表已保存到 ./output/example2/")
