"""
信号处理/算法层 - PMCW 雷达信号处理

PMCW 处理流程：
1. 距离压缩：接收信号与本地码做匹配滤波（相关运算）
2. 多普勒 FFT：对多个脉冲的相关输出做慢时间 FFT
3. 生成距离-多普勒谱

匹配滤波实现：FFT 循环相关（等效于脉冲压缩）
"""

import sys
import os

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from contracts import SimResult, ProcessedResult
from processors.window_utils import get_window


def matched_filter(
    baseband: np.ndarray,
    code: np.ndarray,
    window: str = 'taylor'
) -> np.ndarray:
    """
    匹配滤波（脉冲压缩）

    使用 FFT 循环相关实现：y = IFFT(FFT(rx) * conj(FFT(code)))

    Args:
        baseband: 接收信号 [channels, pulses, samples]
        code: 发射码序列 [code_length]
        window: 窗函数类型

    Returns:
        压缩输出 [channels, pulses, samples]
    """
    _, num_pulses, num_samples = baseband.shape
    N = len(code)

    # 码的频域参考（共轭）
    code_fft = np.conj(np.fft.fft(code, n=num_samples))

    # 窗函数
    win = get_window(window, num_samples)

    # 对每个脉冲做匹配滤波
    compressed = np.zeros_like(baseband)
    for n in range(num_pulses):
        rx = baseband[0, n, :] * win
        rx_fft = np.fft.fft(rx, n=num_samples)
        compressed[0, n, :] = np.fft.ifft(rx_fft * code_fft)

    return compressed


def process_pmcw(
    sim_result: SimResult,
    range_window: str = 'taylor',
    doppler_window: str = 'taylor'
) -> ProcessedResult:
    """
    处理 PMCW 仿真结果

    Args:
        sim_result: PMCW 仿真结果
        range_window: 距离维窗函数
        doppler_window: 多普勒维窗函数

    Returns:
        ProcessedResult: 处理结果
    """
    baseband = sim_result.baseband
    fc = sim_result.fc
    bandwidth = sim_result.bandwidth
    chip_rate = sim_result.fs
    prf = sim_result.prf
    num_pulses = sim_result.num_chirps
    code_length = sim_result.samples_per_chirp
    c = sim_result.c

    # 提取码序列
    code_info = sim_result.target_info.get('code', None)
    if code_info is not None:
        code = np.array(code_info)
    else:
        # 退化处理：如果没有码信息，使用全 1 序列
        code = np.ones(code_length)

    # Step 1: 距离压缩（匹配滤波）
    compressed = matched_filter(baseband, code, window=range_window)

    # Step 2: 多普勒 FFT
    doppler_win = get_window(doppler_window, num_pulses)
    rd_fft = np.fft.fft(compressed * doppler_win[np.newaxis, :, np.newaxis], axis=1)
    rd_fft = np.fft.fftshift(rd_fft, axes=1)

    # Step 3: 计算坐标轴
    # 距离轴：相关输出的每个采样点对应一个距离
    # 距离分辨率 = c / (2 * chip_rate)
    range_resolution = c / (2 * chip_rate)
    range_axis = np.arange(code_length) * range_resolution

    # 多普勒轴
    doppler_freq_axis = np.fft.fftshift(np.fft.fftfreq(num_pulses, d=1/prf))
    doppler_axis = doppler_freq_axis * c / (2 * fc)

    # Step 4: 提取 RD 谱
    # 只取有效距离范围（0 ~ code_length）
    rd_spectrum = rd_fft[0, :, :code_length]  # [doppler, range]
    rd_2d = np.abs(rd_spectrum).T             # [range, doppler]

    range_profile = np.max(rd_2d, axis=1)

    return ProcessedResult(
        name='pmcw_processed',
        range_profile=range_profile,
        range_doppler=rd_2d,
        range_axis=range_axis,
        doppler_axis=doppler_axis,
        extra_data={
            'compressed': compressed,
        }
    )


if __name__ == "__main__":
    print("=" * 60)
    print("PMCW 处理器测试")
    print("=" * 60)

    from simulators.pmcw_simulator import PmcwSimulator

    sim = PmcwSimulator(
        fc=77e9, chip_rate=50e6,
        code_type='barker', code_length=13,
        num_pulses=64
    )

    targets = [
        {"range": 30.0, "velocity": 2.0, "rcs": 10},
        {"range": 80.0, "velocity": -1.5, "rcs": 5},
    ]

    print(f"\n运行 PMCW 仿真...")
    result = sim.simulate(targets, snr_db=25.0, seed=42)
    print(f"  基带数据形状: {result.baseband.shape}")

    print(f"\n处理 PMCW 数据...")
    processed = process_pmcw(result)
    print(f"  RD 谱形状: {processed.range_doppler.shape}")
    print(f"  距离轴: [{processed.range_axis[0]:.1f}, {processed.range_axis[-1]:.1f}] m")
    print(f"  速度轴: [{processed.doppler_axis[0]:.2f}, {processed.doppler_axis[-1]:.2f}] m/s")

    # 检测最强目标
    rd = processed.range_doppler
    idx = np.unravel_index(np.argmax(rd), rd.shape)
    print(f"\n  最强目标检测:")
    print(f"    距离: {processed.range_axis[idx[0]]:.1f} m (真实: {targets[0]['range']} m)")
    print(f"    速度: {processed.doppler_axis[idx[1]]:.2f} m/s (真实: {targets[0]['velocity']} m/s)")
    print(f"  测试完成 ✓")
