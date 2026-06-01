"""
MIMO 雷达信号处理模块

本模块实现 MIMO 雷达的信号处理流程，包括：
- TDMA/DDMA 波形解码
- 虚拟阵列重构
- DBF（数字波束形成）角度估计
- 3D Range-Doppler-Angle 谱生成
"""

import sys
import os

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
import numpy as np
from contracts import ProcessedResult, MimoAntennaArray
from processors.window_utils import get_window
from utils.axes import compute_range_axis, compute_doppler_axis


def process_mimo_tdma(
    sim_result,
    antenna_array: Optional[MimoAntennaArray] = None,
    range_window: str = 'taylor',
    doppler_window: str = 'taylor'
) -> ProcessedResult:
    """
    处理 TDMA MIMO 数据

    Args:
        sim_result: 仿真结果契约对象
        antenna_array: MIMO 天线阵列配置（如果为 None，从 target_info 推断）
        range_window: 距离维窗函数
        doppler_window: 多普勒维窗函数

    Returns:
        processed_result: 处理结果契约对象
    """
    raw_data = sim_result.baseband  # [num_rx, total_chirps, num_samples]
    target_info = sim_result.target_info

    if antenna_array is None:
        num_tx = target_info.get('num_tx', 4)
        num_rx = target_info.get('num_rx', 4)
        antenna_array = MimoAntennaArray(num_tx=num_tx, num_rx=num_rx, fc=sim_result.fc)

    num_tx = antenna_array.num_tx
    num_rx = antenna_array.num_rx
    num_samples = raw_data.shape[2]

    # TDMA: 重构虚拟阵列
    # chirp 排列: [TX0, TX1, TX2, TX3, TX0, TX1, ...]
    total_chirps = raw_data.shape[1]
    num_chirps_per_frame = total_chirps // num_tx

    # 重塑 → [num_rx, num_chirps_per_frame, num_tx, num_samples]
    # 转置 → [num_rx, num_tx, num_chirps_per_frame, num_samples]
    rx_data_reshaped = raw_data.reshape(num_rx, num_chirps_per_frame, num_tx, num_samples)
    rx_data_reshaped = rx_data_reshaped.transpose(0, 2, 1, 3)

    # 虚拟阵列 [virtual_elements, num_chirps_per_frame, num_samples]
    # 顺序与天线阵列一致：先 TX，再 RX
    virtual_elements = num_tx * num_rx
    virtual_data = np.zeros((virtual_elements, num_chirps_per_frame, num_samples),
                           dtype=np.complex128)
    virtual_idx = 0
    for tx_idx in range(num_tx):
        for rx_idx in range(num_rx):
            virtual_data[virtual_idx, :, :] = rx_data_reshaped[rx_idx, tx_idx, :, :]
            virtual_idx += 1

    # 距离 FFT（正频率）
    range_win = get_window(range_window, num_samples)
    range_fft_data = np.fft.fft(virtual_data * range_win[np.newaxis, np.newaxis, :], axis=2)
    num_range_bins = num_samples // 2
    range_fft_data = range_fft_data[:, :, :num_range_bins]

    # 距离轴
    c = sim_result.c
    range_axis = compute_range_axis(sim_result.bandwidth, num_samples, c, positive_only=True)

    # 多普勒 FFT（TDMA 有效 PRF = prf / num_tx）
    doppler_win = get_window(doppler_window, num_chirps_per_frame)
    doppler_fft_data = np.fft.fft(
        range_fft_data * doppler_win[np.newaxis, :, np.newaxis], axis=1)
    doppler_fft_data = np.fft.fftshift(doppler_fft_data, axes=1)

    effective_prf = sim_result.prf / num_tx
    doppler_axis = compute_doppler_axis(effective_prf, num_chirps_per_frame, sim_result.fc, c)

    # RD 谱（所有虚拟元素相干累加）
    rd_spectrum = np.abs(np.mean(doppler_fft_data, axis=0))  # [doppler, range]
    range_profile = np.mean(np.abs(range_fft_data), axis=(0, 1))

    return ProcessedResult(
        name='mimo_tdma',
        range_doppler=rd_spectrum.T,  # [range, doppler]
        range_profile=range_profile,
        range_axis=range_axis,
        doppler_axis=doppler_axis,
        extra_data={
            'virtual_array_data': doppler_fft_data,
            'antenna_array': antenna_array,
            'waveform_mode': 'tdma'
        }
    )


def process_mimo_ddma(
    sim_result,
    antenna_array: Optional[MimoAntennaArray] = None,
    range_window: str = 'taylor',
    doppler_window: str = 'taylor'
) -> ProcessedResult:
    """
    处理 DDMA MIMO 数据

    Args:
        sim_result: 仿真结果契约对象
        antenna_array: MIMO 天线阵列配置
        range_window: 距离维窗函数
        doppler_window: 多普勒维窗函数

    Returns:
        processed_result: 处理结果契约对象
    """
    raw_data = sim_result.baseband  # [num_rx, num_chirps, num_samples]
    target_info = sim_result.target_info

    if antenna_array is None:
        num_tx = target_info.get('num_tx', 4)
        num_rx = target_info.get('num_rx', 4)
        antenna_array = MimoAntennaArray(num_tx=num_tx, num_rx=num_rx, fc=sim_result.fc)

    num_tx = antenna_array.num_tx
    num_rx = antenna_array.num_rx
    num_samples = raw_data.shape[2]
    num_chirps = raw_data.shape[1]

    ddma_codes = target_info.get('ddma_codes', None)
    if ddma_codes is None:
        raise ValueError("DDMA 模式需要 ddma_codes 进行解码")

    # 距离 FFT（正频率）
    range_win = get_window(range_window, num_samples)
    range_fft_data = np.fft.fft(raw_data * range_win[np.newaxis, np.newaxis, :], axis=2)
    num_range_bins = num_samples // 2
    range_fft_data = range_fft_data[:, :, :num_range_bins]

    # DDMA 解码
    decoded_data = np.zeros((num_rx * num_tx, num_chirps, range_fft_data.shape[2]),
                           dtype=np.complex128)
    virtual_idx = 0
    for tx_idx in range(num_tx):
        for rx_idx in range(num_rx):
            rx_data = range_fft_data[rx_idx, :, :]
            phase_correction = np.conj(ddma_codes[tx_idx, :])[:, np.newaxis]
            decoded_data[virtual_idx, :, :] = rx_data * phase_correction
            virtual_idx += 1

    # 多普勒 FFT
    doppler_win = get_window(doppler_window, num_chirps)
    doppler_fft_data = np.fft.fft(
        decoded_data * doppler_win[np.newaxis, :, np.newaxis], axis=1)
    doppler_fft_data = np.fft.fftshift(doppler_fft_data, axes=1)

    # 坐标轴
    c = sim_result.c
    range_axis = compute_range_axis(sim_result.bandwidth, num_samples, c, positive_only=True)

    doppler_axis = compute_doppler_axis(sim_result.prf, num_chirps, sim_result.fc, c)

    # RD 谱
    rd_spectrum = np.abs(np.mean(doppler_fft_data, axis=0))
    range_profile = np.mean(np.abs(range_fft_data), axis=(0, 1))

    return ProcessedResult(
        name='mimo_ddma',
        range_doppler=rd_spectrum.T,
        range_profile=range_profile,
        range_axis=range_axis,
        doppler_axis=doppler_axis,
        extra_data={
            'virtual_array_data': doppler_fft_data,
            'antenna_array': antenna_array,
            'waveform_mode': 'ddma'
        }
    )


def dbf_angle_estimation(
    rd_spectrum: np.ndarray,
    antenna_array: MimoAntennaArray,
    doppler_axis: np.ndarray,
    range_axis: np.ndarray,
    angle_search_range: tuple = (-np.pi/3, np.pi/3),
    angle_resolution: float = np.pi/180,
    angle_window: str = 'taylor'
) -> dict:
    """
    DBF（数字波束形成）角度估计

    Args:
        rd_spectrum: [range_bins, doppler_bins, virtual_elements]
        antenna_array: MIMO 天线阵列配置
        doppler_axis: 多普勒轴
        range_axis: 距离轴
        angle_search_range: 角度搜索范围 (min, max)，弧度
        angle_resolution: 角度分辨率，弧度
        angle_window: 虚拟阵列加窗类型

    Returns:
        dict: angle_spectrum, angles, detected_angles
    """
    num_range = len(range_axis)
    num_doppler = len(doppler_axis)
    num_virtual = antenna_array.virtual_array_size

    angles = np.arange(angle_search_range[0],
                       angle_search_range[1] + angle_resolution,
                       angle_resolution)
    num_angles = len(angles)

    angle_win = get_window(angle_window, num_virtual)

    steering_vectors = np.array([
        antenna_array.get_steering_vector(angle) for angle in angles
    ])

    angle_spectrum = np.zeros((num_range, num_doppler, num_angles), dtype=np.float64)

    for r_idx in range(num_range):
        for d_idx in range(num_doppler):
            virtual_data = rd_spectrum[r_idx, d_idx, :] * angle_win
            for a_idx, sv in enumerate(steering_vectors):
                beam_output = np.dot(np.conj(sv), virtual_data)
                angle_spectrum[r_idx, d_idx, a_idx] = np.abs(beam_output) ** 2

    detected_angles = []
    threshold = np.max(angle_spectrum) * 0.1

    for r_idx in range(num_range):
        for d_idx in range(num_doppler):
            angle_profile = angle_spectrum[r_idx, d_idx, :]
            max_angle_idx = np.argmax(angle_profile)
            max_power = angle_profile[max_angle_idx]

            if max_power > threshold:
                detected_angles.append({
                    'range': range_axis[r_idx],
                    'doppler': doppler_axis[d_idx],
                    'angle': angles[max_angle_idx],
                    'angle_deg': np.degrees(angles[max_angle_idx]),
                    'power': max_power
                })

    return {
        'angle_spectrum': angle_spectrum,
        'angles': angles,
        'detected_angles': detected_angles
    }


def mimo_dbf_angle_estimation(
    processed_result: ProcessedResult,
    angle_search_range: tuple = (-np.pi/3, np.pi/3),
    angle_resolution: float = np.pi/180,
    angle_window: str = 'taylor'
) -> dict:
    """
    MIMO DBF 角度估计（从 ProcessedResult 中提取数据并调用 dbf_angle_estimation）

    Args:
        processed_result: 处理结果契约对象（必须包含 virtual_array_data）
        angle_search_range: 角度搜索范围 (min, max)，弧度
        angle_resolution: 角度分辨率，弧度
        angle_window: 虚拟阵列加窗类型

    Returns:
        dbf_result: DBF 结果字典
    """
    if 'virtual_array_data' not in processed_result.extra_data:
        raise ValueError("ProcessedResult 中缺少 virtual_array_data，无法进行 DBF")

    virtual_array_data = processed_result.extra_data['virtual_array_data']
    # [virtual_elements, doppler_bins, range_bins] → [range_bins, doppler_bins, virtual_elements]
    rd_virtual = np.transpose(virtual_array_data, (2, 1, 0))

    antenna_array = processed_result.extra_data['antenna_array']

    return dbf_angle_estimation(
        rd_virtual, antenna_array,
        processed_result.doppler_axis, processed_result.range_axis,
        angle_search_range=angle_search_range,
        angle_resolution=angle_resolution,
        angle_window=angle_window
    )


def process_mimo(sim_result, **kwargs) -> ProcessedResult:
    """
    MIMO 数据处理主接口

    根据波形模式自动选择处理流程。

    Args:
        sim_result: 仿真结果契约对象
        **kwargs: 传递给具体处理函数的参数

    Returns:
        processed_result: 处理结果契约对象
    """
    waveform_mode = sim_result.target_info.get('waveform_mode', 'tdma')

    if waveform_mode == 'tdma':
        return process_mimo_tdma(sim_result, **kwargs)
    elif waveform_mode == 'ddma':
        return process_mimo_ddma(sim_result, **kwargs)
    else:
        raise ValueError(f"不支持的波形模式: {waveform_mode}")


if __name__ == "__main__":
    print("=" * 70)
    print("MIMO 雷达处理器测试")
    print("=" * 70)

    from contracts import MimoAntennaArray
    from simulators.mimo_simulator import MimoLfmcwSimulator

    antenna_array = MimoAntennaArray(num_tx=4, num_rx=4, fc=77e9)
    mimo_sim = MimoLfmcwSimulator(
        antenna_array=antenna_array, waveform_mode='tdma',
        fc=77e9, bandwidth=150e6, chirp_duration=40e-6,
        fs=20e6, prf=20e3, num_chirps_per_frame=128
    )

    targets = [
        {"range": 50.0, "velocity": 3.0, "angle": np.radians(10), "rcs": 15},
        {"range": 100.0, "velocity": -2.0, "angle": np.radians(-15), "rcs": 10},
    ]

    print(f"\n运行 TDMA MIMO 仿真...")
    sim_result = mimo_sim.simulate(targets, snr_db=25.0, seed=42)
    print(f"✓ 仿真完成，数据形状: {sim_result.baseband.shape}")

    processed = process_mimo(sim_result)
    print(f"✓ 处理完成, RD 谱形状: {processed.range_doppler.shape}")

    dbf_result = mimo_dbf_angle_estimation(processed)
    print(f"✓ DBF 完成, 检测到 {len(dbf_result['detected_angles'])} 个角度")

    for det in dbf_result['detected_angles'][:5]:
        print(f"  R={det['range']:.1f}m, V={det['doppler']:.2f}m/s, A={det['angle_deg']:.1f}°")
