"""
示例 4: 信噪比分析 - 研究噪声对检测性能的影响

这个示例展示不同信噪比条件下的目标检测能力。
适合学习雷达探测理论和灵敏度分析。
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
print("示例 4: 信噪比 (SNR) 对检测性能的影响")
print("=" * 70)

# 固定目标
target = {"range": 100.0, "velocity": 3.0, "rcs": 10}

# 测试不同的信噪比
snr_values = [5, 10, 15, 20, 25, 30]  # dB

print(f"\n目标配置: 距离={target['range']}m, 速度={target['velocity']}m/s, RCS={target['rcs']}dBsm")
print(f"\n测试不同信噪比条件下的检测性能:")
print("-" * 70)

results = []
for snr_db in snr_values:
    # 仿真
    simulator = LfmcwSimulator(
        fc=77e9,
        bandwidth=150e6,
        chirp_duration=50e-6,
        fs=10e6,
        prf=5e3,
        num_chirps=128
    )
    
    sim_result = simulator.simulate([target], snr_db=snr_db, seed=42)
    processed = process_lfmcw(sim_result)
    
    # 找到目标位置的信号强度
    range_axis = processed.range_axis
    doppler_axis = processed.doppler_axis
    
    # 找到最接近真实目标的 bin
    target_range_idx = np.argmin(np.abs(range_axis - target['range']))
    target_doppler_idx = np.argmin(np.abs(doppler_axis - target['velocity']))
    
    # 提取目标位置的功率
    target_power = processed.range_doppler[target_range_idx, target_doppler_idx]
    target_power_db = 20 * np.log10(target_power + 1e-10)
    
    # 计算背景噪声水平（取中值）
    noise_level = np.median(processed.range_doppler)
    noise_level_db = 20 * np.log10(noise_level + 1e-10)
    
    # 信干比（SIR）
    sir_db = target_power_db - noise_level_db
    
    results.append({
        'snr_db': snr_db,
        'target_power_db': target_power_db,
        'noise_level_db': noise_level_db,
        'sir_db': sir_db,
        'processed': processed
    })
    
    print(f"SNR={snr_db:2d}dB: "
          f"目标功率={target_power_db:6.1f}dB, "
          f"噪声水平={noise_level_db:6.1f}dB, "
          f"SIR={sir_db:5.1f}dB")

# 可视化 1: SNR vs 目标功率和噪声水平
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# 左图：功率曲线
snr_array = [r['snr_db'] for r in results]
target_powers = [r['target_power_db'] for r in results]
noise_levels = [r['noise_level_db'] for r in results]
sir_values = [r['sir_db'] for r in results]

ax1.plot(snr_array, target_powers, 'b-o', linewidth=2, markersize=8, label='目标功率')
ax1.plot(snr_array, noise_levels, 'r-s', linewidth=2, markersize=8, label='噪声水平')
ax1.plot(snr_array, sir_values, 'g-^', linewidth=2, markersize=8, label='信干比 (SIR)')
ax1.set_xlabel('输入 SNR (dB)', fontsize=12)
ax1.set_ylabel('功率 (dB)', fontsize=12)
ax1.set_title('SNR 对目标检测和噪声的影响', fontsize=13, fontweight='bold')
ax1.legend(fontsize=11)
ax1.grid(True, alpha=0.3)

# 右图：RD 谱对比（选择几个典型的 SNR）
selected_snrs = [10, 20, 30]
axes_rd = [plt.subplot(1, 3, i+3) for i in range(len(selected_snrs))]

for idx, snr_val in enumerate(selected_snrs):
    result = next(r for r in results if r['snr_db'] == snr_val)
    processed = result['processed']
    
    rd_spectrum = processed.range_doppler
    range_axis = processed.range_axis
    doppler_axis = processed.doppler_axis
    
    rd_db = 20 * np.log10(rd_spectrum + 1e-10)
    
    R_edges = np.zeros(len(range_axis) + 1)
    R_edges[:-1] = range_axis - (range_axis[1] - range_axis[0]) / 2
    R_edges[-1] = range_axis[-1] + (range_axis[1] - range_axis[0]) / 2
    
    V_edges = np.zeros(len(doppler_axis) + 1)
    V_edges[:-1] = doppler_axis - (doppler_axis[1] - doppler_axis[0]) / 2
    V_edges[-1] = doppler_axis[-1] + (doppler_axis[1] - doppler_axis[0]) / 2
    
    ax = axes_rd[idx]
    mesh = ax.pcolormesh(R_edges, V_edges, rd_db.T, shading='flat', cmap='jet')
    ax.set_xlabel('Range (m)', fontsize=9)
    ax.set_ylabel('Velocity (m/s)', fontsize=9)
    ax.set_title(f'SNR = {snr_val} dB\nSIR = {result["sir_db"]:.1f} dB', 
                 fontsize=10, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.colorbar(mesh, ax=ax, label='Amplitude (dB)')
    
    # 标注真实目标位置
    ax.plot(target['range'], target['velocity'], 'w+', markersize=12, markeredgewidth=2)

plt.tight_layout()
plt.savefig('./output/example4_snr_analysis.png', dpi=150, bbox_inches='tight')
print(f"\n✓ SNR 分析图已保存到 ./output/example4_snr_analysis.png")
plt.show()

print("\n" + "=" * 70)
print("结论:")
print("=" * 70)
print("1. SNR 越高，目标检测越清晰")
print("2. 低 SNR (<10dB) 时，目标可能被噪声淹没")
print("3. 高 SNR (>20dB) 时，可以获得良好的检测性能")
print("4. SIR（信干比）是衡量检测质量的重要指标")
print("\n✓ 分析完成！")
