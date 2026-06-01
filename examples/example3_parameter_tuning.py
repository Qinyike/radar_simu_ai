"""
示例 3: 参数调优 - 探索不同雷达参数的影响

这个示例展示如何调整雷达系统参数，并观察对性能的影响。
适合学习雷达系统设计原理。
"""

import sys
import os
# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from simulators import LfmcwSimulator
from processors import process_lfmcw
import numpy as np
import matplotlib.pyplot as plt

print("=" * 70)
print("示例 3: 雷达参数调优实验")
print("=" * 70)

# 固定目标场景
target = {"range": 100.0, "velocity": 5.0, "rcs": 15}

# 测试不同的带宽配置
bandwidths = [50e6, 100e6, 150e6, 200e6]  # 50, 100, 150, 200 MHz

print("\n实验 1: 带宽对距离分辨率的影响")
print("-" * 70)

results_bandwidth = []
for bw in bandwidths:
    # 创建仿真器
    simulator = LfmcwSimulator(
        fc=77e9,
        bandwidth=bw,
        chirp_duration=50e-6,
        fs=10e6,
        prf=5e3,
        num_chirps=128
    )
    
    # 仿真
    sim_result = simulator.simulate([target], snr_db=30.0, seed=42)
    processed = process_lfmcw(sim_result)
    
    range_resolution = processed.range_axis[1] - processed.range_axis[0]
    max_range = processed.range_axis[-1]
    
    results_bandwidth.append({
        'bandwidth': bw,
        'range_resolution': range_resolution,
        'max_range': max_range,
        'processed': processed
    })
    
    print(f"带宽 {bw/1e6:3.0f} MHz: "
          f"距离分辨率={range_resolution:.2f}m, "
          f"最大距离={max_range:.0f}m")

# 可视化带宽对比
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for i, result in enumerate(results_bandwidth):
    ax = axes[i]
    rd_spectrum = result['processed'].range_doppler
    range_axis = result['processed'].range_axis
    doppler_axis = result['processed'].doppler_axis
    
    rd_db = 20 * np.log10(rd_spectrum + 1e-10)
    
    R_edges = np.zeros(len(range_axis) + 1)
    R_edges[:-1] = range_axis - (range_axis[1] - range_axis[0]) / 2
    R_edges[-1] = range_axis[-1] + (range_axis[1] - range_axis[0]) / 2
    
    V_edges = np.zeros(len(doppler_axis) + 1)
    V_edges[:-1] = doppler_axis - (doppler_axis[1] - doppler_axis[0]) / 2
    V_edges[-1] = doppler_axis[-1] + (doppler_axis[1] - doppler_axis[0]) / 2
    
    mesh = ax.pcolormesh(R_edges, V_edges, rd_db.T, shading='flat', cmap='jet')
    ax.set_xlabel('Range (m)', fontsize=10)
    ax.set_ylabel('Velocity (m/s)', fontsize=10)
    ax.set_title(f'BW = {result["bandwidth"]/1e6:.0f} MHz\n'
                 f'Resolution: {result["range_resolution"]:.2f}m', 
                 fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.colorbar(mesh, ax=ax, label='Amplitude (dB)')

plt.tight_layout()
plt.savefig('./output/example3_bandwidth_comparison.png', dpi=150, bbox_inches='tight')
print(f"\n✓ 带宽对比图已保存到 ./output/example3_bandwidth_comparison.png")
plt.show()

# 实验 2: Chirp 数量对速度分辨率的影响
print("\n" + "=" * 70)
print("实验 2: Chirp 数量对速度分辨率的影响")
print("-" * 70)

num_chirps_list = [32, 64, 128, 256]

results_chirps = []
for num_chirps in num_chirps_list:
    simulator = LfmcwSimulator(
        fc=77e9,
        bandwidth=150e6,
        chirp_duration=50e-6,
        fs=10e6,
        prf=5e3,
        num_chirps=num_chirps
    )
    
    sim_result = simulator.simulate([target], snr_db=30.0, seed=42)
    processed = process_lfmcw(sim_result)
    
    velocity_resolution = processed.doppler_axis[1] - processed.doppler_axis[0]
    max_velocity = processed.doppler_axis[-1]
    
    results_chirps.append({
        'num_chirps': num_chirps,
        'velocity_resolution': velocity_resolution,
        'max_velocity': max_velocity,
        'processed': processed
    })
    
    print(f"Chirps {num_chirps:3d}: "
          f"速度分辨率={velocity_resolution:.3f}m/s, "
          f"最大速度=±{max_velocity:.2f}m/s")

# 可视化速度分辨率对比
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for i, result in enumerate(results_chirps):
    ax = axes[i]
    rd_spectrum = result['processed'].range_doppler
    range_axis = result['processed'].range_axis
    doppler_axis = result['processed'].doppler_axis
    
    rd_db = 20 * np.log10(rd_spectrum + 1e-10)
    
    R_edges = np.zeros(len(range_axis) + 1)
    R_edges[:-1] = range_axis - (range_axis[1] - range_axis[0]) / 2
    R_edges[-1] = range_axis[-1] + (range_axis[1] - range_axis[0]) / 2
    
    V_edges = np.zeros(len(doppler_axis) + 1)
    V_edges[:-1] = doppler_axis - (doppler_axis[1] - doppler_axis[0]) / 2
    V_edges[-1] = doppler_axis[-1] + (doppler_axis[1] - doppler_axis[0]) / 2
    
    mesh = ax.pcolormesh(R_edges, V_edges, rd_db.T, shading='flat', cmap='jet')
    ax.set_xlabel('Range (m)', fontsize=10)
    ax.set_ylabel('Velocity (m/s)', fontsize=10)
    ax.set_title(f'N_chirps = {result["num_chirps"]}\n'
                 f'Velocity Res: {result["velocity_resolution"]:.3f}m/s', 
                 fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.colorbar(mesh, ax=ax, label='Amplitude (dB)')

plt.tight_layout()
plt.savefig('./output/example3_chirps_comparison.png', dpi=150, bbox_inches='tight')
print(f"\n✓ Chirp 数量对比图已保存到 ./output/example3_chirps_comparison.png")
plt.show()

print("\n" + "=" * 70)
print("实验总结:")
print("=" * 70)
print("1. 带宽越大 → 距离分辨率越好，但最大探测距离可能受限")
print("2. Chirp 数量越多 → 速度分辨率越好，但帧率会降低")
print("3. 需要根据应用场景权衡选择参数")
print("\n✓ 所有图表已保存到 ./output/ 目录")
