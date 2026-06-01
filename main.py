"""
入口/调度层 - 汽车雷达 LFMCW 仿真主程序

本模块是整个仿真框架的入口点，负责：
1. 解析配置参数
2. 注册并调用仿真模块
3. 执行信号处理
4. 触发可视化

遵循单向数据流：配置 -> 仿真 -> 处理 -> 可视化
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from contracts import SimResult, ProcessedResult
from simulators import get_simulator
from processors import get_processor
from visualizers import plot_comprehensive, plot_range_doppler, plot_range_profile


def run_simulation(
    waveform_type: str = "lfmcw",
    targets: list[dict] = None,
    snr_db: float = 20.0,
    seed: int = 42,
    visualize: bool = True,
    save_plots: bool = False,
    output_dir: str = "./output"
):
    """
    运行完整的雷达仿真流程
    
    Args:
        waveform_type: 波形类型（如 "lfmcw"）
        targets: 目标场景列表
        snr_db: 信噪比 (dB)
        seed: 随机数种子
        visualize: 是否进行可视化
        save_plots: 是否保存图表
        output_dir: 输出目录
        
    Returns:
        tuple: (SimResult, ProcessedResult)
    """
    print("=" * 70)
    print("汽车雷达 LFMCW 仿真系统")
    print("=" * 70)
    
    # Step 1: 配置目标场景（默认场景）
    if targets is None:
        targets = [
            {"range": 50.0, "velocity": 20.0, "rcs": 10},   # 50m, 72km/h 远离
            {"range": 100.0, "velocity": -10.0, "rcs": 5},  # 100m, 36km/h 靠近
            {"range": 150.0, "velocity": 0.0, "rcs": 0},    # 150m, 静止
        ]
    
    print(f"\n[1/4] 配置目标场景:")
    for i, target in enumerate(targets, 1):
        print(f"  目标 {i}: 距离={target['range']}m, "
              f"速度={target['velocity']}m/s, "
              f"RCS={target.get('rcs', 0)}dBsm")
    
    # Step 2: 创建仿真器并执行仿真
    print(f"\n[2/4] 执行 {waveform_type.upper()} 波形仿真...")
    simulator = get_simulator(waveform_type)
    sim_result = simulator.simulate(targets=targets, snr_db=snr_db, seed=seed)
    
    print(f"  ✓ 仿真完成")
    print(f"    - 载波频率: {sim_result.fc / 1e9:.2f} GHz")
    print(f"    - 带宽: {sim_result.bandwidth / 1e6:.2f} MHz")
    print(f"    - Chirp 数量: {sim_result.num_chirps}")
    print(f"    - 每 chirp 采样: {sim_result.samples_per_chirp}")
    print(f"    - 基带数据形状: {sim_result.baseband.shape}")
    
    # Step 3: 信号处理
    print(f"\n[3/4] 执行信号处理（2D-FFT）...")
    processor = get_processor(waveform_type)
    processed_result = processor(sim_result)
    
    print(f"  ✓ 处理完成")
    print(f"    - 距离分辨率: {processed_result.range_axis[1] - processed_result.range_axis[0]:.2f} m")
    print(f"    - 最大探测距离: {processed_result.range_axis[-1]:.2f} m")
    print(f"    - 速度分辨率: {processed_result.doppler_axis[1] - processed_result.doppler_axis[0]:.2f} m/s")
    print(f"    - 最大探测速度: ±{processed_result.doppler_axis[-1]:.2f} m/s")
    
    # Step 4: 可视化
    if visualize:
        print(f"\n[4/4] 生成可视化图表...")
        
        if save_plots:
            os.makedirs(output_dir, exist_ok=True)
        
        # 综合图
        plot_comprehensive(
            processed_result,
            target_info=sim_result.target_info,
            title="LFMCW Automotive Radar Simulation",
            save_path=os.path.join(output_dir, "comprehensive.png") if save_plots else None,
            show=True
        )
        
        # 单独的距离-多普勒谱
        plot_range_doppler(
            processed_result,
            title="Range-Doppler Spectrum",
            save_path=os.path.join(output_dir, "range_doppler.png") if save_plots else None,
            show=False
        )
        
        # 单独的距离剖面
        plot_range_profile(
            processed_result,
            title="Range Profile",
            save_path=os.path.join(output_dir, "range_profile.png") if save_plots else None,
            show=False
        )
        
        print(f"  ✓ 可视化完成")
    
    print("\n" + "=" * 70)
    print("仿真流程完成！")
    print("=" * 70)
    
    return sim_result, processed_result


def main():
    """主函数 - 演示完整的仿真流程"""
    
    # 运行仿真
    sim_result, processed_result = run_simulation(
        waveform_type="lfmcw",
        targets=[
            {"range": 50.0, "velocity": 20.0, "rcs": 10},
            {"range": 100.0, "velocity": -10.0, "rcs": 5},
            {"range": 150.0, "velocity": 0.0, "rcs": 0},
        ],
        snr_db=20.0,
        seed=42,
        visualize=True,
        save_plots=True,
        output_dir="./output"
    )
    
    # 物理验证：检查检测结果是否与真实目标一致
    print("\n物理验证:")
    rd_spectrum = processed_result.range_doppler
    range_axis = processed_result.range_axis
    doppler_axis = processed_result.doppler_axis
    
    # 计算最大不模糊速度
    max_unambiguous_velocity = abs(doppler_axis[-1])
    
    # 找到最强目标
    max_idx = np.unravel_index(np.argmax(rd_spectrum), rd_spectrum.shape)
    detected_range = range_axis[max_idx[0]]  # 第一维是 range
    detected_velocity = doppler_axis[max_idx[1]]  # 第二维是 doppler
    
    print(f"  检测到的最强目标:")
    print(f"    - 距离: {detected_range:.2f} m")
    print(f"    - 速度: {detected_velocity:.2f} m/s")
    print(f"    - 最大不模糊速度: ±{max_unambiguous_velocity:.2f} m/s")
    
    # 与真实目标对比
    true_target = sim_result.target_info['targets'][0]
    range_error = abs(detected_range - true_target['range'])
    velocity_error = abs(detected_velocity - true_target['velocity'])
    
    # 检查是否发生多普勒混叠
    is_aliased = abs(true_target['velocity']) > max_unambiguous_velocity
    
    print(f"\n  与真实目标对比 (目标 1):")
    print(f"    - 真实距离: {true_target['range']:.2f} m")
    print(f"    - 真实速度: {true_target['velocity']:.2f} m/s")
    print(f"    - 距离误差: {range_error:.2f} m")
    print(f"    - 速度误差: {velocity_error:.2f} m/s")
    
    if is_aliased:
        print(f"\n  ⚠ 注意：目标速度 ({true_target['velocity']:.2f} m/s) 超过最大不模糊速度 ({max_unambiguous_velocity:.2f} m/s)")
        print(f"     发生了多普勒混叠！检测到的速度是模糊后的值。")
        print(f"     建议：降低目标速度或提高 PRF 参数以避免混叠。")
    
    if range_error < 2.0 and (not is_aliased or velocity_error < max_unambiguous_velocity * 0.5):
        print("  ✓ 物理验证通过！检测结果符合预期。")
    else:
        if not is_aliased:
            print("  ⚠ 警告：检测结果与预期存在较大偏差。")


if __name__ == "__main__":
    main()
