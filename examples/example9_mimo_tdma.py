"""
示例 9: MIMO 雷达仿真 - TDMA 波形和 DBF 角度估计

这个示例展示如何使用 MIMO 雷达进行角度测量：
- 4T4R（4发4收）天线阵列配置
- TDMA（时分多址）波形
- DBF（数字波束形成）角度估计
- 3D Range-Doppler-Angle 谱可视化
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import numpy as np
from simulators.mimo_simulator import MimoLfmcwSimulator, MimoAntennaArray
from processors.mimo_processor import process_mimo, mimo_dbf_angle_estimation
from visualizers.rd_visualizer import plot_comprehensive

print("=" * 70)
print("示例 9: MIMO 雷达仿真 - TDMA 波形和 DBF 角度估计")
print("=" * 70)

# ============================================================================
# 1. 创建 4T4R MIMO 天线阵列
# ============================================================================
print("\n[1/5] 创建 4T4R MIMO 天线阵列...")
antenna_array = MimoAntennaArray(
    num_tx=4,           # 4 个发射天线
    num_rx=4,           # 4 个接收天线
    fc=77e9,            # 77 GHz 载波频率
    tx_spacing=None,    # 默认半波长间距
    rx_spacing=None     # 默认半波长间距
)

print(f"  ✓ 天线阵列配置:")
print(f"    - TX 天线数: {antenna_array.num_tx}")
print(f"    - RX 天线数: {antenna_array.num_rx}")
print(f"    - 虚拟阵列大小: {antenna_array.virtual_array_size} (等效孔径)")
print(f"    - 有效孔径: {antenna_array.effective_aperture:.4f} m")
print(f"    - 波长: {antenna_array.wavelength*1000:.2f} mm")
print(f"    - 天线间距: {antenna_array.tx_spacing*1000:.2f} mm (λ/2)")

# ============================================================================
# 2. 创建 MIMO 仿真器（TDMA 模式）
# ============================================================================
print("\n[2/5] 创建 MIMO 仿真器（TDMA 模式）...")
mimo_sim = MimoLfmcwSimulator(
    antenna_array=antenna_array,
    waveform_mode='tdma',       # TDMA 波形
    fc=77e9,                    # 77 GHz
    bandwidth=150e6,            # 150 MHz 带宽
    chirp_duration=50e-6,       # 50 μs
    fs=10e6,                    # 10 MHz 采样率
    prf=5e3,                    # 5 kHz PRF
    num_chirps_per_frame=128    # 每帧 128 个 chirps
)

max_velocity = mimo_sim.max_unambiguous_velocity
print(f"  ✓ 仿真参数:")
print(f"    - 波形模式: {mimo_sim.waveform_mode.upper()}")
print(f"    - 带宽: {mimo_sim.bandwidth/1e6:.1f} MHz")
print(f"    - Chirp 持续时间: {mimo_sim.chirp_duration*1e6:.1f} μs")
print(f"    - PRF: {mimo_sim.prf/1e3:.1f} kHz")
print(f"    - 最大不模糊速度: ±{max_velocity:.2f} m/s")
print(f"    - 总 chirp 数: {mimo_sim.num_chirps_per_frame * antenna_array.num_tx}")

# ============================================================================
# 3. 定义目标场景（包含角度信息）
# ============================================================================
print("\n[3/5] 定义目标场景...")
targets = [
    {
        "range": 50.0,                          # 距离 50m
        "velocity": 3.0,                        # 速度 3 m/s
        "angle": np.radians(10),                # 角度 +10°
        "rcs": 15                               # RCS 15 dBsm
    },
    {
        "range": 100.0,                         # 距离 100m
        "velocity": -2.0,                       # 速度 -2 m/s
        "angle": np.radians(-15),               # 角度 -15°
        "rcs": 10                               # RCS 10 dBsm
    },
    {
        "range": 150.0,                         # 距离 150m
        "velocity": 0.0,                        # 静止
        "angle": np.radians(0),                 # 角度 0°（正前方）
        "rcs": 8                                # RCS 8 dBsm
    }
]

print(f"  ✓ 目标配置:")
for i, t in enumerate(targets, 1):
    angle_deg = np.degrees(t['angle'])
    print(f"    T{i}: R={t['range']:4.0f}m, V={t['velocity']:5.1f}m/s, "
          f"Angle={angle_deg:6.1f}°, RCS={t['rcs']}dBsm")

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

# 处理 TDMA MIMO 数据
processed = process_mimo(sim_result)
print(f"  ✓ TDMA 数据处理完成")
print(f"    - RD 谱形状: {processed.range_doppler.shape}")
print(f"    - 虚拟阵列数据形状: {processed.extra_data['virtual_array_data'].shape}")

# 执行 DBF 角度估计
dbf_result = mimo_dbf_angle_estimation(
    processed,
    angle_search_range=(-np.pi/3, np.pi/3),  # ±60°
    angle_resolution=np.pi/180                # 1° 分辨率
)
print(f"  ✓ DBF 角度估计完成")
print(f"    - 角度搜索范围: ±60°")
print(f"    - 角度分辨率: 1°")
print(f"    - 检测到的角度数: {len(dbf_result['detected_angles'])}")

# 显示检测结果
if dbf_result['detected_angles']:
    print(f"\n  📊 检测结果:")
    print(f"  {'编号':<6}{'距离(m)':<10}{'速度(m/s)':<12}{'角度(°)':<10}{'功率(dB)':<10}")
    print(f"  {'-'*48}")
    
    for i, det in enumerate(dbf_result['detected_angles'], 1):
        power_db = 10 * np.log10(det['power'] + 1e-10)
        print(f"  {i:<6}{det['range']:<10.1f}{det['doppler']:<12.2f}"
              f"{det['angle_deg']:<10.1f}{power_db:<10.1f}")
    
    # 与真实目标对比
    print(f"\n  🔍 与真实目标对比:")
    for true_target in targets:
        true_angle_deg = np.degrees(true_target['angle'])
        
        # 找到最接近的检测结果
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
        
        if best_match and min_error < 20:  # 容差范围内
            print(f"    ✓ T(R={true_target['range']}m, V={true_target['velocity']}m/s, "
                  f"A={true_angle_deg}°) → "
                  f"Detected(R={best_match['range']:.1f}m, V={best_match['doppler']:.2f}m/s, "
                  f"A={best_match['angle_deg']:.1f}°)")
        else:
            print(f"    ⚠ T(R={true_target['range']}m, V={true_target['velocity']}m/s, "
                  f"A={true_angle_deg}°) → 未检测到或误差较大")

# ============================================================================
# 6. 可视化（可选）
# ============================================================================
print("\n生成可视化图表...")

# 准备目标信息（用于标注）
target_info_for_viz = {
    'targets': [
        {"range": t['range'], "velocity": t['velocity'], "rcs": t['rcs']}
        for t in targets
    ]
}

plot_comprehensive(
    processed,
    target_info=target_info_for_viz,
    title="MIMO Radar Simulation (4T4R TDMA)\nwith DBF Angle Estimation",
    save_path="./output/example9_mimo_tdma.png",
    show=False
)

print("  ✓ 图表已保存到 ./output/example9_mimo_tdma.png")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 70)
print("示例完成！")
print("=" * 70)
print("\n关键要点:")
print("  1. ✓ MIMO 通过虚拟阵列提高角度分辨率")
print("  2. ✓ TDMA 波形按时间分离不同 TX 天线")
print("  3. ✓ DBF 实现高精度的角度估计")
print("  4. ✓ 4T4R 配置提供 16 个虚拟通道")
print("  5. ✓ 可以同时测量距离、速度和角度（3D 感知）")

print("\n下一步:")
print("  - 尝试 DDMA 波形（example10_mimo_ddma.py）")
print("  - 调整天线间距观察角度分辨率变化")
print("  - 增加目标数量测试多目标分辨能力")
print("  - 降低 SNR 测试鲁棒性")
