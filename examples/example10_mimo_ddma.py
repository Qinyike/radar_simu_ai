"""
示例 10: MIMO 雷达仿真 - DDMA 波形和 DBF 角度估计

与 TDMA 的区别：
- TDMA: 4 根 TX 按时序轮流发射，有效 PRF = PRF / 4
- DDMA: 4 根 TX 同时发射（通过相位编码区分），有效 PRF = PRF
- DDMA 优势：相同 PRF 下不模糊速度是 TDMA 的 4 倍

模拟高速公路典型场景（相对速度较大）：
- 前方车辆（快速接近）
- 旁车道车辆（慢速远离）
- 静止结构物（天桥/护栏）
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import numpy as np
from simulators.mimo_simulator import MimoLfmcwSimulator, MimoAntennaArray
from processors.mimo_processor import process_mimo, mimo_dbf_angle_estimation
from visualizers.rd_visualizer import (
    plot_antenna_array,
    plot_angle_spectrum,
    plot_mimo_comprehensive
)

print("=" * 70)
print("示例 10: MIMO 雷达仿真 - DDMA 波形和 DBF 角度估计")
print("=" * 70)

# ============================================================================
# 1. 创建 4T4R MIMO 天线阵列
# ============================================================================
print("\n[1/5] 创建 4T4R MIMO 天线阵列...")
antenna_array = MimoAntennaArray(
    num_tx=4,
    num_rx=4,
    fc=77e9,
)

print(f"  ✓ 天线阵列配置:")
print(f"    - TX 天线数: {antenna_array.num_tx}")
print(f"    - RX 天线数: {antenna_array.num_rx}")
print(f"    - 虚拟阵列大小: {antenna_array.virtual_array_size}")
print(f"    - 波长: {antenna_array.wavelength*1000:.2f} mm")
print(f"    - TX 间距: {antenna_array.tx_spacing*1000:.2f} mm ({antenna_array.num_rx}×λ/2)")
print(f"    - RX 间距: {antenna_array.rx_spacing*1000:.2f} mm (λ/2)")

# ============================================================================
# 2. 创建 MIMO 仿真器（DDMA 模式）
# ============================================================================
print("\n[2/5] 创建 MIMO 仿真器（DDMA 模式）...")
mimo_sim = MimoLfmcwSimulator(
    antenna_array=antenna_array,
    waveform_mode='ddma',       # DDMA 波形
    fc=77e9,                    # 77 GHz
    bandwidth=150e6,            # 150 MHz → 距离分辨率 1.0 m
    chirp_duration=40e-6,       # 40 μs
    fs=20e6,                    # 20 MHz → 800 采样点
    prf=20e3,                   # 20 kHz（DDMA 有效 PRF = 20 kHz，无需除以 TX 数）
    num_chirps_per_frame=128    # 每帧 128 chirps
)

max_velocity = mimo_sim.max_unambiguous_velocity
print(f"  ✓ 仿真参数:")
print(f"    - 波形模式: {mimo_sim.waveform_mode.upper()}")
print(f"    - 带宽: {mimo_sim.bandwidth/1e6:.1f} MHz → 距离分辨率 1.0 m")
print(f"    - Chirp 持续时间: {mimo_sim.chirp_duration*1e6:.1f} μs")
print(f"    - PRF: {mimo_sim.prf/1e3:.1f} kHz")
print(f"    - 最大不模糊速度: ±{max_velocity:.2f} m/s (±{max_velocity*3.6:.1f} km/h)")
print(f"    - 总 chirp 数: {mimo_sim.num_chirps_per_frame}（DDMA 不需要乘 TX 数）")

# ============================================================================
# 3. 定义目标场景（相对速度较大，利用 DDMA 的高速度范围优势）
# ============================================================================
print("\n[3/5] 定义目标场景...")
targets = [
    {
        "range": 30.0,                          # 前车 30m
        "velocity": -8.0,                       # 快速接近 -8.0 m/s (28.8 km/h)
        "angle": np.radians(1),                 # 正前方偏右 1°
        "rcs": 10                               # 轿车 RCS 10 dBsm
    },
    {
        "range": 60.0,                          # 旁车道车辆 60m
        "velocity": 4.0,                        # 慢速远离 4.0 m/s (14.4 km/h)
        "angle": np.radians(-12),               # 左侧 -12°
        "rcs": 12                               # SUV RCS 12 dBsm
    },
    {
        "range": 120.0,                         # 天桥/护栏 120m
        "velocity": 0.0,                        # 静止
        "angle": np.radians(0),                 # 正前方
        "rcs": 5                                # 金属结构 RCS 5 dBsm
    }
]

print(f"  ✓ 目标配置:")
for i, t in enumerate(targets, 1):
    angle_deg = np.degrees(t['angle'])
    print(f"    T{i}: R={t['range']:5.1f}m, V={t['velocity']:+5.1f}m/s "
          f"({t['velocity']*3.6:+.1f}km/h), "
          f"Angle={angle_deg:+6.1f}°, RCS={t['rcs']}dBsm")

# ============================================================================
# 4. 运行 MIMO 仿真
# ============================================================================
print("\n[4/5] 运行 MIMO 仿真...")
sim_result = mimo_sim.simulate(targets, snr_db=25.0, seed=42)
print(f"  ✓ 仿真完成")
print(f"    - SimResult.name: {sim_result.name}")
print(f"    - baseband shape: {sim_result.baseband.shape}")
print(f"      [RX天线={sim_result.baseband.shape[0]}, "
      f"Chirps={sim_result.baseband.shape[1]}, "
      f"采样点={sim_result.baseband.shape[2]}]")

# ============================================================================
# 5. 处理 MIMO 数据并执行 DBF
# ============================================================================
print("\n[5/5] 处理 MIMO 数据并执行 DBF 角度估计...")

processed = process_mimo(sim_result)
print(f"  ✓ DDMA 数据处理完成")
print(f"    - RD 谱形状: {processed.range_doppler.shape}")
print(f"    - 虚拟阵列数据形状: {processed.extra_data['virtual_array_data'].shape}")

dbf_result = mimo_dbf_angle_estimation(
    processed,
    angle_search_range=(-np.pi/3, np.pi/3),
    angle_resolution=np.pi/180
)
print(f"  ✓ DBF 角度估计完成")
print(f"    - 检测到的角度数: {len(dbf_result['detected_angles'])}")

if dbf_result['detected_angles']:
    print(f"\n  📊 检测结果:")
    print(f"  {'编号':<6}{'距离(m)':<10}{'速度(m/s)':<12}{'角度(°)':<10}{'功率(dB)':<10}")
    print(f"  {'-'*48}")

    for i, det in enumerate(dbf_result['detected_angles'], 1):
        power_db = 10 * np.log10(det['power'] + 1e-10)
        print(f"  {i:<6}{det['range']:<10.1f}{det['doppler']:<12.2f}"
              f"{det['angle_deg']:<10.1f}{power_db:<10.1f}")

    print(f"\n  🔍 与真实目标对比:")
    for true_target in targets:
        true_angle_deg = np.degrees(true_target['angle'])

        best_match = None
        min_error = float('inf')

        for det in dbf_result['detected_angles']:
            range_error = abs(det['range'] - true_target['range'])
            velocity_error = abs(det['doppler'] - true_target['velocity'])
            angle_error = abs(det['angle_deg'] - true_angle_deg)

            total_error = range_error + abs(velocity_error) * 10 + abs(angle_error) * 5

            if total_error < min_error:
                min_error = total_error
                best_match = det

        if best_match and min_error < 20:
            print(f"    ✓ T(R={true_target['range']}m, V={true_target['velocity']}m/s, "
                  f"A={true_angle_deg}°) → "
                  f"Detected(R={best_match['range']:.1f}m, V={best_match['doppler']:.2f}m/s, "
                  f"A={best_match['angle_deg']:.1f}°)")
        else:
            print(f"    ⚠ T(R={true_target['range']}m, V={true_target['velocity']}m/s, "
                  f"A={true_angle_deg}°) → 未检测到或误差较大")

# ============================================================================
# 6. 可视化
# ============================================================================
print("\n生成可视化图表...")

target_info_for_viz = {
    'targets': [
        {"range": t['range'], "velocity": t['velocity'], "rcs": t['rcs']}
        for t in targets
    ]
}

# 6a. 天线阵列布局
plot_antenna_array(
    antenna_array,
    title="MIMO 4T4R Antenna Array Layout (DDMA)",
    save_path="./output/example10_antenna_array.png",
    show=False
)
print("  ✓ 天线阵列图已保存")

# 6b. 角度谱
plot_angle_spectrum(
    dbf_result,
    processed,
    title="DBF Angle Spectrum (4T4R DDMA)",
    save_path="./output/example10_angle_spectrum.png",
    show=False
)
print("  ✓ 角度谱已保存")

# 6c. MIMO 综合图
plot_mimo_comprehensive(
    processed,
    dbf_result=dbf_result,
    antenna_array=antenna_array,
    target_info=target_info_for_viz,
    title="MIMO Radar Simulation (4T4R DDMA)",
    save_path="./output/example10_mimo_comprehensive.png",
    show=True
)
print("  ✓ 综合图已保存")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 70)
print("示例完成！")
print("=" * 70)
print("\n关键要点:")
print("  1. ✓ DDMA 所有 TX 同时发射，通过相位编码区分")
print("  2. ✓ 有效 PRF = PRF（不除以 TX 数），不模糊速度是 TDMA 的 4 倍")
print("  3. ✓ 适用于目标速度较大的场景（高速公路/城市快速路）")
print("  4. ✓ DDMA 编码会在多普勒域产生偏移分量，需注意解读")
print("  5. ✓ 与 TDMA 相同的天线阵列和 DBF 处理流程")

print("\nTDMA vs DDMA 对比:")
print(f"  {'参数':<20}{'TDMA':<15}{'DDMA':<15}")
print(f"  {'-'*50}")
print(f"  {'TX 发射方式':<20}{'轮流发射':<15}{'同时发射':<15}")
print(f"  {'TX 区分方式':<20}{'时分':<15}{'相位编码':<15}")
print(f"  {'有效 PRF':<20}{'PRF/N_tx':<15}{'PRF':<15}")
print(f"  {'最大不模糊速度':<20}{'±4.87 m/s':<15}{'±19.48 m/s':<15}")
print(f"  {'数据量':<20}{'N_tx × N_chirp':<15}{'N_chirp':<15}")
