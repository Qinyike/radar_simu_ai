"""
示例 12: 受干扰的 LFMCW 雷达仿真与可视化

模拟真实车载雷达可能遇到的三种干扰：
1. FMCW 雷达互扰（RRI）：对向车辆雷达同频段不同斜率 chirp
2. CW 干扰：单频连续波干扰源（如工业设备泄漏）
3. 宽带噪声压制干扰：噪声干扰机

可视化：
- 上排：三种干扰下的距离-多普勒谱
- 下排：距离剖面对比 + 干扰信号示意
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import numpy as np
import matplotlib.pyplot as plt
from simulators import get_simulator
from processors import get_processor
from processors.window_utils import get_window

print("=" * 70)
print("示例 12: 受干扰的 LFMCW 雷达仿真")
print("=" * 70)

# ============================================================================
# 1. 生成干净的 LFMCW 回波
# ============================================================================
print("\n[1/4] 生成干净 LFMCW 回波...")

sim = get_simulator("lfmcw")
targets = [
    {"range": 40.0, "velocity": 1.5, "rcs": 10},
    {"range": 100.0, "velocity": -3.0, "rcs": 7},
    {"range": 180.0, "velocity": 0.5, "rcs": 4},
]

sim_result = sim.simulate(targets=targets, snr_db=25.0, seed=42)
processor = get_processor("lfmcw")
clean = processor(sim_result)

print(f"  ✓ 基带形状: {sim_result.baseband.shape}")
print(f"  ✓ RD 谱形状: {clean.range_doppler.shape}")
print(f"  ✓ 目标: {len(targets)} 个")

# 提取关键参数
baseband = sim_result.baseband.copy()
fc = sim_result.fc
bandwidth = sim_result.bandwidth
fs = sim_result.fs
prf = sim_result.prf
num_chirps = sim_result.num_chirps
samples_per_chirp = sim_result.samples_per_chirp
chirp_duration = samples_per_chirp / fs
chirp_slope = bandwidth / chirp_duration
c = sim_result.c

t_fast = np.arange(samples_per_chirp) / fs
t_slow = np.arange(num_chirps) / prf


def add_fmcw_interference(baseband, num_interferers, int_snr_db, chirp_slope, fs, fc, prf, seed=None):
    """
    添加 FMCW 雷达互扰（RRI）

    干扰源：不同斜率/起始频率的 FMCW chirp
    特征：在 RD 谱上产生斜线或散布干扰
    """
    if seed is not None:
        np.random.seed(seed)

    bb = baseband.copy()
    _, num_chirps, num_samples = bb.shape
    t_fast = np.arange(num_samples) / fs
    t_slow = np.arange(num_chirps) / prf

    for _ in range(num_interferers):
        # 干扰雷达参数（随机化）
        slope_ratio = np.random.uniform(0.6, 1.4)    # 斜率比本机 0.6~1.4
        int_slope = chirp_slope * slope_ratio
        int_delay = np.random.uniform(0, chirp_duration)  # 时间偏移
        int_freq_offset = np.random.uniform(-1e6, 1e6)     # 频率偏移

        for n in range(num_chirps):
            t = t_fast + int_delay
            # 干扰 chirp（去斜后的差频信号）
            f_beat = int_slope * int_delay + int_freq_offset
            phase = 2 * np.pi * f_beat * t_fast + 2 * np.pi * np.random.uniform(-500, 500) * t_slow[n]
            interference = np.exp(1j * phase)
            bb[0, n, :] += interference

    # 调整干扰功率
    sig_power = np.mean(np.abs(bb) ** 2)
    int_power = sig_power / (10 ** (int_snr_db / 10))
    # 干扰功率相对于信号
    current_int_power = np.mean(np.abs(bb - baseband) ** 2)
    if current_int_power > 1e-30:
        scale = np.sqrt(int_power / current_int_power)
        bb = baseband + (bb - baseband) * scale

    return bb


def add_cw_interference(baseband, num_interferers, int_snr_db, fs, prf, seed=None):
    """
    添加 CW（连续波）干扰

    干扰源：单频信号泄漏
    特征：在 RD 谱上产生水平线（固定距离门）或垂直线（固定多普勒）
    """
    if seed is not None:
        np.random.seed(seed)

    bb = baseband.copy()
    _, num_chirps, num_samples = bb.shape
    t_fast = np.arange(num_samples) / fs

    for _ in range(num_interferers):
        # CW 干扰频率（在采样带宽内随机）
        int_freq = np.random.uniform(-fs / 2, fs / 2)
        int_phase = np.random.uniform(0, 2 * np.pi)

        for n in range(num_chirps):
            cw = np.exp(1j * (2 * np.pi * int_freq * t_fast + int_phase))
            bb[0, n, :] += cw

    # 调整干扰功率
    sig_power = np.mean(np.abs(baseband) ** 2)
    int_power = sig_power / (10 ** (int_snr_db / 10))
    current_int = np.mean(np.abs(bb - baseband) ** 2)
    if current_int > 1e-30:
        scale = np.sqrt(int_power / current_int)
        bb = baseband + (bb - baseband) * scale

    return bb


def add_noise_jamming(baseband, int_snr_db, seed=None):
    """
    添加宽带噪声压制干扰

    特征：抬高整个 RD 谱噪底，降低信噪比
    """
    if seed is not None:
        np.random.seed(seed)

    bb = baseband.copy()
    sig_power = np.mean(np.abs(baseband) ** 2)
    jam_power = sig_power / (10 ** (int_snr_db / 10))

    noise = np.sqrt(jam_power / 2) * (
        np.random.randn(*bb.shape) + 1j * np.random.randn(*bb.shape)
    )
    bb += noise
    return bb


# ============================================================================
# 2. 生成三种干扰信号
# ============================================================================
print("\n[2/4] 生成三种干扰信号...")

bb_fmcw = add_fmcw_interference(baseband, num_interferers=3, int_snr_db=-5,
                                 chirp_slope=chirp_slope, fs=fs, fc=fc, prf=prf, seed=100)
bb_cw = add_cw_interference(baseband, num_interferers=2, int_snr_db=-10,
                             fs=fs, prf=prf, seed=200)
bb_noise = add_noise_jamming(baseband, int_snr_db=5, seed=300)

print(f"  ✓ FMCW 互扰: 3 个干扰源，干信比 -5 dB")
print(f"  ✓ CW 干扰: 2 个干扰源，干信比 -10 dB")
print(f"  ✓ 噪声压制: 干信比 +5 dB")

# ============================================================================
# 3. 处理受干扰信号
# ============================================================================
print("\n[3/4] 处理受干扰信号...")

from contracts import SimResult as SR

def make_result(bb, orig):
    return SR(name=orig.name, baseband=bb, fc=orig.fc, bandwidth=orig.bandwidth,
              fs=orig.fs, prf=orig.prf, num_chirps=orig.num_chirps,
              samples_per_chirp=orig.samples_per_chirp, c=orig.c,
              target_info=orig.target_info)

proc = get_processor("lfmcw")
rd_fmcw = proc(make_result(bb_fmcw, sim_result))
rd_cw = proc(make_result(bb_cw, sim_result))
rd_noise = proc(make_result(bb_noise, sim_result))

print(f"  ✓ 全部处理完成")

# ============================================================================
# 4. 可视化：ADC 时域 + RD 谱 + 距离剖面
# ============================================================================
print("\n[4/4] 生成可视化图表...")

# 选一个 chirp 展示 ADC 时域波形（选第 10 个 chirp，避免边界）
chirp_idx = 10
adc_clean = baseband[0, chirp_idx, :]
adc_fmcw = bb_fmcw[0, chirp_idx, :]
adc_cw = bb_cw[0, chirp_idx, :]
adc_noise = bb_noise[0, chirp_idx, :]
t_us = t_fast * 1e6  # 转为 μs

all_adcs = [adc_clean, adc_fmcw, adc_cw, adc_noise]
all_rds = [clean, rd_fmcw, rd_cw, rd_noise]
adc_titles = ['Clean', 'FMCW RRI (ISR=-5dB)', 'CW Interference (ISR=-10dB)', 'Noise Jamming (ISR=+5dB)']
rd_titles = ['Clean RD', 'FMCW RRI RD', 'CW Interf. RD', 'Noise Jam. RD']
adc_colors = ['#2c3e50', '#e74c3c', '#3498db', '#2ecc71']

# ---- 图 1：ADC 时域波形（I/Q 实部/虚部）----
fig1, axes1 = plt.subplots(2, 4, figsize=(22, 8))

for col in range(4):
    # 上排：I/Q 实部
    ax = axes1[0, col]
    ax.plot(t_us, np.real(all_adcs[col]), color=adc_colors[col], linewidth=0.6, alpha=0.9)
    ax.set_title(adc_titles[col], fontsize=11, fontweight='bold',
                 color=adc_colors[col] if col > 0 else '#2c3e50')
    ax.set_ylabel('I (Real)', fontsize=10)
    ax.grid(True, alpha=0.3)
    if col == 0:
        ax.set_ylabel('I (Real)', fontsize=10, fontweight='bold')
    # 统一 y 轴范围方便对比
    ymax = max(np.max(np.abs(np.real(a))) for a in all_adcs) * 1.1
    ax.set_ylim(-ymax, ymax)

    # 下排：Q 虚部
    ax = axes1[1, col]
    ax.plot(t_us, np.imag(all_adcs[col]), color=adc_colors[col], linewidth=0.6, alpha=0.9)
    ax.set_xlabel('Fast Time (μs)', fontsize=10)
    ax.set_ylabel('Q (Imag)', fontsize=10)
    ax.grid(True, alpha=0.3)
    if col == 0:
        ax.set_ylabel('Q (Imag)', fontsize=10, fontweight='bold')
    ax.set_ylim(-ymax, ymax)

fig1.suptitle(f'ADC Chirp Signal Comparison (Chirp #{chirp_idx})\n'
              f'77 GHz, {bandwidth/1e6:.0f} MHz BW, {fs/1e6:.0f} MHz Fs, '
              f'{samples_per_chirp} samples',
              fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('./output/example12_adc_comparison.png', dpi=150, bbox_inches='tight')
print("  ✓ ADC 对比图已保存")
plt.show()

# ---- 图 2：RD 谱（干净 vs 三种干扰）----
fig2, axes2 = plt.subplots(2, 2, figsize=(18, 14))

for idx in range(4):
    ax = axes2[idx // 2, idx % 2]
    res = all_rds[idx]
    title = rd_titles[idx]

    rd_db = 20 * np.log10(res.range_doppler + 1e-10)
    r_ax = res.range_axis
    d_ax = res.doppler_axis

    r_edges = np.zeros(len(r_ax) + 1)
    r_edges[:-1] = r_ax - (r_ax[1] - r_ax[0]) / 2
    r_edges[-1] = r_ax[-1] + (r_ax[1] - r_ax[0]) / 2
    d_edges = np.zeros(len(d_ax) + 1)
    d_edges[:-1] = d_ax - (d_ax[1] - d_ax[0]) / 2
    d_edges[-1] = d_ax[-1] + (d_ax[1] - d_ax[0]) / 2

    mesh = ax.pcolormesh(r_edges, d_edges, rd_db.T, shading='flat', cmap='jet')
    ax.set_xlabel('Range (m)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Velocity (m/s)', fontsize=11, fontweight='bold')
    color_label = adc_colors[idx] if idx > 0 else '#2c3e50'
    ax.set_title(title, fontsize=12, fontweight='bold', color=color_label)
    plt.colorbar(mesh, ax=ax, shrink=0.85, label='dB')

    # 标注目标
    for t in targets:
        ax.plot(t['range'], t['velocity'], 'w+', markersize=12, markeredgewidth=2)

fig2.suptitle('Range-Doppler Spectrum Under Different Interference',
              fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('./output/example12_rd_comparison.png', dpi=150, bbox_inches='tight')
print("  ✓ RD 谱对比图已保存")
plt.show()

# ---- 图 3：距离剖面对比 ----
fig3, ax = plt.subplots(figsize=(14, 6))
range_axis = clean.range_axis

rp_clean = 20 * np.log10(clean.range_profile + 1e-10)
rp_fmcw = 20 * np.log10(rd_fmcw.range_profile + 1e-10)
rp_cw = 20 * np.log10(rd_cw.range_profile + 1e-10)
rp_noise = 20 * np.log10(rd_noise.range_profile + 1e-10)

ax.plot(range_axis, rp_clean, 'k-', linewidth=2, label='Clean', alpha=0.9)
ax.plot(range_axis, rp_fmcw, '-', color='#e74c3c', linewidth=1.3, label='FMCW RRI (-5dB)', alpha=0.8)
ax.plot(range_axis, rp_cw, '-', color='#3498db', linewidth=1.3, label='CW Interf. (-10dB)', alpha=0.8)
ax.plot(range_axis, rp_noise, '-', color='#2ecc71', linewidth=1.3, label='Noise Jam. (+5dB)', alpha=0.8)

for t in targets:
    ax.axvline(x=t['range'], color='gray', linestyle='--', alpha=0.4, linewidth=0.8)
    ax.annotate(f'R={t["range"]:.0f}m', (t['range'], ax.get_ylim()[1] * 0.95),
                ha='center', fontsize=8, color='gray')

ax.set_xlabel('Range (m)', fontsize=12, fontweight='bold')
ax.set_ylabel('Amplitude (dB)', fontsize=12, fontweight='bold')
ax.set_title('Range Profile: Clean vs Interference', fontsize=14, fontweight='bold')
ax.legend(fontsize=10, loc='upper right')
ax.grid(True, alpha=0.3)
ax.set_xlim([0, range_axis[-1]])

plt.tight_layout()
plt.savefig('./output/example12_range_profile.png', dpi=150, bbox_inches='tight')
print("  ✓ 距离剖面对比图已保存")
plt.show()

# ---- 图 4：交互式对比（干净 vs FMCW 互扰）----
print("\n  打开交互式对比窗口...")
print("  操作：鼠标悬停显示坐标，点击查看详情，ESC 清除选中")

from visualizers.interactive import plot_comparison_interactive

target_info = {
    'targets': [{"range": t['range'], "velocity": t['velocity'], "rcs": t['rcs']}
                for t in targets]
}
plot_comparison_interactive(
    clean, rd_fmcw,
    target_info=target_info,
    clean_label="Clean",
    processed_label="FMCW Radar Interference (RRI)",
    title="Interactive Comparison: Clean vs FMCW Interference",
    save_path="./output/example12_interactive_compare.png",
    show=True
)
print("  ✓ 交互式对比图已保存")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 70)
print("示例完成！")
print("=" * 70)
print("""
干扰类型分析：
┌──────────────┬────────────────────────────┬─────────────────────────────┐
│ 干扰类型      │ RD 谱特征                    │ 对检测的影响                  │
├──────────────┼────────────────────────────┼─────────────────────────────┤
│ FMCW 互扰     │ 斜线/散布条纹                │ 距离门虚警，遮蔽弱目标          │
│ CW 干扰       │ 水平条纹（固定距离门）         │ 特定距离门被污染               │
│ 噪声压制      │ 全谱噪底抬高                 │ 整体信噪比下降，弱目标丢失       │
└──────────────┴────────────────────────────┴─────────────────────────────┘
""")
