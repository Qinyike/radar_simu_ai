"""
示例 5: 自定义可视化 - 创建专业的雷达数据显示

这个示例展示如何提取原始数据并创建自定义的可视化效果。
适合需要定制报告或集成到其他系统的场景。
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
from matplotlib.gridspec import GridSpec

print("=" * 70)
print("示例 5: 自定义专业可视化")
print("=" * 70)

# 配置场景
targets = [
    {"range": 40.0, "velocity": 8.0, "rcs": 18},
    {"range": 90.0, "velocity": -3.0, "rcs": 12},
    {"range": 130.0, "velocity": 0.0, "rcs": 8},
]

print(f"\n场景: {len(targets)} 个目标")
for i, t in enumerate(targets, 1):
    print(f"  目标 {i}: R={t['range']}m, V={t['velocity']}m/s")

# 仿真
simulator = LfmcwSimulator(
    fc=77e9,
    bandwidth=150e6,
    chirp_duration=50e-6,
    fs=10e6,
    prf=5e3,
    num_chirps=128
)

print("\n正在运行仿真...")
sim_result = simulator.simulate(targets, snr_db=25.0, seed=42)
processed = process_lfmcw(sim_result)

# 提取数据
rd_spectrum = processed.range_doppler
range_profile = processed.range_profile
range_axis = processed.range_axis
doppler_axis = processed.doppler_axis

# 转换为 dB
rd_db = 20 * np.log10(rd_spectrum + 1e-10)
profile_db = 20 * np.log10(range_profile + 1e-10)

print("✓ 数据处理完成")

# 创建专业的多面板图
fig = plt.figure(figsize=(16, 10))
gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3)

# 面板 1: 完整的 RD 谱（左上，占 2x2）
ax1 = fig.add_subplot(gs[:2, :2])
R_edges = np.zeros(len(range_axis) + 1)
R_edges[:-1] = range_axis - (range_axis[1] - range_axis[0]) / 2
R_edges[-1] = range_axis[-1] + (range_axis[1] - range_axis[0]) / 2

V_edges = np.zeros(len(doppler_axis) + 1)
V_edges[:-1] = doppler_axis - (doppler_axis[1] - doppler_axis[0]) / 2
V_edges[-1] = doppler_axis[-1] + (doppler_axis[1] - doppler_axis[0]) / 2

mesh = ax1.pcolormesh(R_edges, V_edges, rd_db.T, shading='flat', cmap='jet')
ax1.set_xlabel('Range (m)', fontsize=11, fontweight='bold')
ax1.set_ylabel('Velocity (m/s)', fontsize=11, fontweight='bold')
ax1.set_title('Range-Doppler Spectrum', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle='--')

# 标注真实目标
for i, target in enumerate(targets, 1):
    ax1.plot(target['range'], target['velocity'], 'w+', 
            markersize=15, markeredgewidth=2.5, label=f'Target {i}')
ax1.legend(loc='upper right', fontsize=9, framealpha=0.8)

cbar1 = plt.colorbar(mesh, ax=ax1)
cbar1.set_label('Amplitude (dB)', fontsize=10)

# 面板 2: 距离剖面（右上）
ax2 = fig.add_subplot(gs[0, 2])
ax2.plot(range_axis, profile_db, 'b-', linewidth=1.5)
ax2.set_xlabel('Range (m)', fontsize=10)
ax2.set_ylabel('Power (dB)', fontsize=10)
ax2.set_title('Range Profile', fontsize=11, fontweight='bold')
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.set_xlim([0, range_axis[-1]])

# 标注目标距离
for target in targets:
    ax2.axvline(x=target['range'], color='r', linestyle='--', 
               alpha=0.7, linewidth=1.5)
    ax2.text(target['range'], ax2.get_ylim()[1]*0.95, 
            f"{target['range']}m", rotation=90, va='top', fontsize=8)

# 面板 3: 多普勒剖面（右中）
ax3 = fig.add_subplot(gs[1, 2])
doppler_profile = np.max(rd_db, axis=0)  # 沿距离维度的最大值
ax3.plot(doppler_axis, doppler_profile, 'g-', linewidth=1.5)
ax3.set_xlabel('Velocity (m/s)', fontsize=10)
ax3.set_ylabel('Max Power (dB)', fontsize=10)
ax3.set_title('Doppler Profile', fontsize=11, fontweight='bold')
ax3.grid(True, alpha=0.3, linestyle='--')

# 标注目标速度
for target in targets:
    ax3.axvline(x=target['velocity'], color='r', linestyle='--', 
               alpha=0.7, linewidth=1.5)

# 面板 4: 系统参数信息（右下）
ax4 = fig.add_subplot(gs[2, :])
ax4.axis('off')

info_text = f"""
Radar System Parameters:
• Carrier Frequency: {simulator.fc/1e9:.1f} GHz
• Bandwidth: {simulator.bandwidth/1e6:.0f} MHz
• Chirp Duration: {simulator.chirp_duration*1e6:.1f} μs
• Sampling Rate: {simulator.fs/1e6:.1f} MHz
• PRF: {simulator.prf/1e3:.1f} kHz
• Number of Chirps: {simulator.num_chirps}

Performance Metrics:
• Range Resolution: {range_axis[1]-range_axis[0]:.2f} m
• Max Range: {range_axis[-1]:.0f} m
• Velocity Resolution: {doppler_axis[1]-doppler_axis[0]:.3f} m/s
• Max Velocity: ±{doppler_axis[-1]:.2f} m/s
• SNR: 25 dB
"""

ax4.text(0.05, 0.95, info_text, transform=ax4.transAxes,
        fontsize=10, verticalalignment='top', family='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.suptitle('LFMCW Automotive Radar Simulation Report', 
            fontsize=16, fontweight='bold', y=0.995)

plt.savefig('./output/example5_custom_visualization.png', 
           dpi=150, bbox_inches='tight')
print("✓ 专业可视化图表已保存到 ./output/example5_custom_visualization.png")
plt.show()

print("\n" + "=" * 70)
print("提示:")
print("=" * 70)
print("你可以基于这个模板创建自己的报告格式")
print("包括添加公司 Logo、时间戳、更多统计信息等")
print("\n✓ 示例完成！")
