"""
示例 7: 多普勒模糊可视化 - 正确处理混叠目标

这个示例展示当目标速度超过最大不模糊速度时，
如何在 RD 谱上正确标注目标的模糊位置。

关键特性：
- 不同目标使用不同颜色和标记
- 自动计算并标注模糊后的位置
- 用虚线连接真实位置和模糊位置
- 清晰的图例说明
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from simulators import LfmcwSimulator
from processors import process_lfmcw
from visualizers.rd_visualizer import plot_comprehensive, wrap_velocity
import numpy as np
import matplotlib.pyplot as plt

print("=" * 70)
print("示例 7: 多普勒模糊可视化")
print("=" * 70)

# 创建仿真器（使用较低的 PRF 以产生明显的模糊效果）
simulator = LfmcwSimulator(
    fc=77e9,
    bandwidth=150e6,
    chirp_duration=50e-6,
    fs=10e6,
    prf=3e3,           # 较低的 PRF (3 kHz)
    num_chirps=128
)

# 计算最大不模糊速度
max_velocity = simulator.c * simulator.prf / (4 * simulator.fc)
print(f"\n系统参数:")
print(f"  PRF: {simulator.prf/1e3:.1f} kHz")
print(f"  最大不模糊速度: ±{max_velocity:.2f} m/s")
print(f"  速度分辨率: {max_velocity / simulator.num_chirps * 2:.3f} m/s")

# 定义多个目标（包含会模糊的目标）
targets = [
    {"range": 40.0, "velocity": 2.0, "rcs": 18},      # T1: 不模糊
    {"range": 80.0, "velocity": -6.0, "rcs": 15},     # T2: 会模糊
    {"range": 120.0, "velocity": 4.5, "rcs": 12},     # T3: 接近边界
    {"range": 160.0, "velocity": -10.0, "rcs": 10},   # T4: 严重模糊
]

print(f"\n目标配置:")
print("-" * 70)
for i, target in enumerate(targets, 1):
    v = target['velocity']
    v_wrapped = wrap_velocity(v, max_velocity)
    is_aliased = abs(v) > max_velocity
    
    status = "⚠ ALIASED" if is_aliased else "✓ OK"
    if is_aliased:
        print(f"  T{i}: R={target['range']:4.0f}m, V={v:6.1f}m/s → {v_wrapped:6.1f}m/s  {status}")
    else:
        print(f"  T{i}: R={target['range']:4.0f}m, V={v:6.1f}m/s                       {status}")

# 运行仿真
print("\n正在运行仿真...")
sim_result = simulator.simulate(targets, snr_db=25.0, seed=42)
processed = process_lfmcw(sim_result)
print("✓ 仿真完成")

# 生成可视化
print("\n生成可视化图表...")
target_info = {'targets': targets}

plot_comprehensive(
    processed,
    target_info=target_info,
    title="Doppler Aliasing Visualization\n(Different markers and colors for each target)",
    save_path="./output/example7_doppler_aliasing.png",
    show=False
)

print("✓ 图表已保存到 ./output/example7_doppler_aliasing.png")

# 分析检测结果
print("\n" + "=" * 70)
print("检测结果分析:")
print("=" * 70)

rd_spectrum = processed.range_doppler
range_axis = processed.range_axis
doppler_axis = processed.doppler_axis

# 找到所有局部峰值
rd_flat = rd_spectrum.flatten()
top_indices = np.argsort(rd_flat)[-len(targets):][::-1]

print(f"\n检测到的 {len(targets)} 个最强目标:")
print("-" * 70)
for rank, idx in enumerate(top_indices, 1):
    range_idx, doppler_idx = np.unravel_index(idx, rd_spectrum.shape)
    R = range_axis[range_idx]
    V = doppler_axis[doppler_idx]
    power_db = 20 * np.log10(rd_spectrum[range_idx, doppler_idx] + 1e-10)
    
    # 匹配到最近的目标
    distances = [abs(R - t['range']) for t in targets]
    closest_target_idx = np.argmin(distances)
    closest_target = targets[closest_target_idx]
    
    match_status = "✓" if distances[closest_target_idx] < 2.0 else "?"
    
    print(f"  {rank}. 检测: R={R:6.1f}m, V={V:6.2f}m/s, Power={power_db:5.1f}dB "
          f"{match_status} (对应 T{closest_target_idx+1})")

# 创建额外的对比图：显示模糊前后的位置
print("\n创建模糊位置对比图...")
fig, ax = plt.subplots(figsize=(12, 8))

# 绘制 RD 谱
rd_db = 20 * np.log10(rd_spectrum + 1e-10)

range_edges = np.zeros(len(range_axis) + 1)
range_edges[:-1] = range_axis - (range_axis[1] - range_axis[0]) / 2
range_edges[-1] = range_axis[-1] + (range_axis[1] - range_axis[0]) / 2

doppler_edges = np.zeros(len(doppler_axis) + 1)
doppler_edges[:-1] = doppler_axis - (doppler_axis[1] - doppler_axis[0]) / 2
doppler_edges[-1] = doppler_axis[-1] + (doppler_axis[1] - doppler_axis[0]) / 2

mesh = ax.pcolormesh(range_edges, doppler_edges, rd_db.T, shading='flat', cmap='jet')
ax.set_xlabel('Range (m)', fontsize=12, fontweight='bold')
ax.set_ylabel('Velocity (m/s)', fontsize=12, fontweight='bold')
ax.set_title('Doppler Aliasing: True vs Wrapped Positions', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

# 标注目标
markers = ['o', 's', '^', 'D']
colors = ['red', 'blue', 'green', 'orange']

for i, target in enumerate(targets):
    R_true = target['range']
    V_true = target['velocity']
    V_wrapped = wrap_velocity(V_true, max_velocity)
    
    marker = markers[i % len(markers)]
    color = colors[i % len(colors)]
    
    is_aliased = abs(V_true) > max_velocity
    
    # 绘制真实位置（如果超出范围则用空心标记）
    if is_aliased:
        # 真实位置在可视范围外，用小圆圈标注
        ax.plot(R_true, V_true, marker='o', markerfacecolor='none', 
               markeredgecolor=color, markersize=10, markeredgewidth=2,
               linestyle='None', alpha=0.5, label=f'T{i+1} true (out of range)')
        
        # 绘制模糊后的位置
        ax.plot(R_true, V_wrapped, marker=marker, color=color,
               markersize=12, markeredgewidth=2, markeredgecolor='white',
               linestyle='None', label=f'T{i+1} wrapped: {V_wrapped:.1f}m/s')
        
        # 用箭头连接
        ax.annotate('', xy=(R_true, V_wrapped), xytext=(R_true, V_true),
                   arrowprops=dict(arrowstyle='->', color=color, 
                                 lw=2, linestyle='--', alpha=0.7))
    else:
        # 不模糊的目标
        ax.plot(R_true, V_true, marker=marker, color=color,
               markersize=12, markeredgewidth=2, markeredgecolor='white',
               linestyle='None', label=f'T{i+1}: R={R_true}m, V={V_true}m/s')

ax.legend(loc='upper right', fontsize=9, framealpha=0.9, title='Targets')
plt.colorbar(mesh, ax=ax, label='Amplitude (dB)')

plt.tight_layout()
plt.savefig('./output/example7_aliasing_comparison.png', dpi=150, bbox_inches='tight')
print("✓ 对比图已保存到 ./output/example7_aliasing_comparison.png")
plt.show()

print("\n" + "=" * 70)
print("关键要点:")
print("=" * 70)
print("1. 当目标速度 > 最大不模糊速度时，会发生多普勒模糊")
print("2. 模糊后的速度 = ((V + V_max) % (2*V_max)) - V_max")
print("3. 在 RD 谱上应该标注模糊后的位置，而不是真实位置")
print("4. 不同目标使用不同颜色和标记便于区分")
print("5. 可以用虚线连接真实位置和模糊位置，帮助理解")
print("\n✓ 示例完成！")
