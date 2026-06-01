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

# 添加项目根目录到 Python 路径
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
import numpy as np
from contracts import ProcessedResult
from simulators.mimo_simulator import MimoAntennaArray


def process_mimo_tdma(
    sim_result,
    antenna_array: Optional[MimoAntennaArray] = None,
    window_type: str = 'hamming'
) -> ProcessedResult:
    """
    处理 TDMA MIMO 数据
    
    Args:
        sim_result: 仿真结果契约对象
        antenna_array: MIMO 天线阵列配置（如果为 None，从 target_info 推断）
        window_type: 窗函数类型
        
    Returns:
        processed_result: 处理结果契约对象
    """
    raw_data = sim_result.baseband  # [num_rx, total_chirps, num_samples]
    target_info = sim_result.target_info
    
    # 获取天线配置
    if antenna_array is None:
        num_tx = target_info.get('num_tx', 4)
        num_rx = target_info.get('num_rx', 4)
        fc = sim_result.fc
        antenna_array = MimoAntennaArray(num_tx=num_tx, num_rx=num_rx, fc=fc)
    
    num_tx = antenna_array.num_tx
    num_rx = antenna_array.num_rx
    num_samples = raw_data.shape[2]
    
    # TDMA: 重构虚拟阵列
    # raw_data shape: [num_rx, num_tx * num_chirps_per_frame, num_samples]
    total_chirps = raw_data.shape[1]
    num_chirps_per_frame = total_chirps // num_tx
    
    # 重塑数据: [num_rx, num_tx, num_chirps_per_frame, num_samples]
    rx_data_reshaped = raw_data.reshape(num_rx, num_tx, num_chirps_per_frame, num_samples)
    
    # 构建虚拟阵列数据 [virtual_elements, num_chirps_per_frame, num_samples]
    virtual_elements = num_tx * num_rx
    virtual_data = np.zeros((virtual_elements, num_chirps_per_frame, num_samples), 
                           dtype=np.complex128)
    
    virtual_idx = 0
    for tx_idx in range(num_tx):
        for rx_idx in range(num_rx):
            virtual_data[virtual_idx, :, :] = rx_data_reshaped[rx_idx, tx_idx, :, :]
            virtual_idx += 1
    
    # 应用窗函数
    if window_type == 'hamming':
        window = np.hamming(num_samples)
    elif window_type == 'hanning':
        window = np.hanning(num_samples)
    else:
        window = np.ones(num_samples)
    
    # 距离 FFT
    range_fft_data = np.fft.fft(virtual_data * window[np.newaxis, np.newaxis, :], 
                                axis=2)
    range_fft_data = np.fft.fftshift(range_fft_data, axes=2)
    
    # 计算距离轴
    fs = sim_result.fs
    bandwidth = sim_result.bandwidth
    num_range_bins = num_samples
    range_resolution = fs / (2 * bandwidth)
    max_range = num_range_bins * range_resolution
    range_axis = np.linspace(0, max_range, num_range_bins, endpoint=False)
    
    # 多普勒 FFT
    doppler_fft_data = np.fft.fft(range_fft_data, axis=1)
    doppler_fft_data = np.fft.fftshift(doppler_fft_data, axes=1)
    
    # 计算多普勒轴
    prf = sim_result.prf
    num_doppler_bins = num_chirps_per_frame
    velocity_resolution = prf / num_doppler_bins
    max_velocity = prf / 2
    doppler_axis = np.linspace(-max_velocity, max_velocity, num_doppler_bins, endpoint=False)
    
    # 提取 RD 谱（第一个虚拟元素作为示例）
    rd_spectrum = np.abs(doppler_fft_data[0, :, :])  # [doppler_bins, range_bins]
    rd_spectrum = np.fft.fftshift(rd_spectrum, axes=0)
    
    # 计算距离剖面
    range_profile = np.mean(np.abs(range_fft_data), axis=(0, 1))  # [range_bins]
    
    return ProcessedResult(
        name='mimo_tdma',
        range_doppler=rd_spectrum.T,  # [range_bins, doppler_bins]
        range_profile=range_profile,
        range_axis=range_axis,
        doppler_axis=doppler_axis,
        extra_data={
            'virtual_array_data': doppler_fft_data,  # [virtual_elements, doppler_bins, range_bins]
            'antenna_array': antenna_array,
            'waveform_mode': 'tdma'
        }
    )


def process_mimo_ddma(
    sim_result,
    antenna_array: Optional[MimoAntennaArray] = None,
    window_type: str = 'hamming'
) -> ProcessedResult:
    """
    处理 DDMA MIMO 数据
    
    Args:
        sim_result: 仿真结果契约对象
        antenna_array: MIMO 天线阵列配置
        window_type: 窗函数类型
        
    Returns:
        processed_result: 处理结果契约对象
    """
    raw_data = sim_result.baseband  # [num_rx, num_chirps, num_samples]
    target_info = sim_result.target_info
    
    # 获取天线配置
    if antenna_array is None:
        num_tx = target_info.get('num_tx', 4)
        num_rx = target_info.get('num_rx', 4)
        fc = sim_result.fc
        antenna_array = MimoAntennaArray(num_tx=num_tx, num_rx=num_rx, fc=fc)
    
    num_tx = antenna_array.num_tx
    num_rx = antenna_array.num_rx
    num_samples = raw_data.shape[2]
    num_chirps = raw_data.shape[1]
    
    # DDMA: 需要解码相位编码分离不同 TX
    ddma_codes = target_info.get('ddma_codes', None)
    if ddma_codes is None:
        raise ValueError("DDMA 模式需要 ddma_codes 进行解码")
    
    # 应用窗函数
    if window_type == 'hamming':
        window = np.hamming(num_samples)
    elif window_type == 'hanning':
        window = np.hanning(num_samples)
    else:
        window = np.ones(num_samples)
    
    # 距离 FFT
    windowed_data = raw_data * window[np.newaxis, np.newaxis, :]
    range_fft_data = np.fft.fft(windowed_data, axis=2)
    range_fft_data = np.fft.fftshift(range_fft_data, axes=2)
    
    # DDMA 解码：对每个 chirp 应用逆相位编码
    decoded_data = np.zeros((num_rx * num_tx, num_chirps, range_fft_data.shape[2]), 
                           dtype=np.complex128)
    
    virtual_idx = 0
    for rx_idx in range(num_rx):
        for tx_idx in range(num_tx):
            # 提取该 RX 的数据
            rx_data = range_fft_data[rx_idx, :, :]  # [num_chirps, range_bins]
            
            # 应用逆相位编码（共轭相乘）
            phase_correction = np.conj(ddma_codes[tx_idx, :])[:, np.newaxis]
            decoded_virtual = rx_data * phase_correction
            
            decoded_data[virtual_idx, :, :] = decoded_virtual
            virtual_idx += 1
    
    # 多普勒 FFT
    doppler_fft_data = np.fft.fft(decoded_data, axis=1)
    doppler_fft_data = np.fft.fftshift(doppler_fft_data, axes=1)
    
    # 计算坐标轴
    fs = sim_result.fs
    bandwidth = sim_result.bandwidth
    num_range_bins = num_samples
    range_resolution = fs / (2 * bandwidth)
    max_range = num_range_bins * range_resolution
    range_axis = np.linspace(0, max_range, num_range_bins, endpoint=False)
    
    prf = sim_result.prf
    num_doppler_bins = num_chirps
    velocity_resolution = prf / num_doppler_bins
    max_velocity = prf / 2
    doppler_axis = np.linspace(-max_velocity, max_velocity, num_doppler_bins, endpoint=False)
    
    # 提取 RD 谱
    rd_spectrum = np.abs(doppler_fft_data[0, :, :])
    rd_spectrum = np.fft.fftshift(rd_spectrum, axes=0)
    
    # 计算距离剖面
    range_profile = np.mean(np.abs(range_fft_data), axis=(0, 1))
    
    return ProcessedResult(
        name='mimo_ddma',
        range_doppler=rd_spectrum.T,
        range_profile=range_profile,
        range_axis=range_axis,
        doppler_axis=doppler_axis,
        extra_data={
            'virtual_array_data': doppler_fft_data,  # [virtual_elements, doppler_bins, range_bins]
            'antenna_array': antenna_array,
            'waveform_mode': 'ddma'
        }
    )


def mimo_dbf_angle_estimation(
    processed_result: ProcessedResult,
    angle_search_range: tuple = (-np.pi/3, np.pi/3),
    angle_resolution: float = np.pi/180
) -> dict:
    """
    MIMO DBF 角度估计
    
    Args:
        processed_result: 处理结果契约对象（必须包含 virtual_array_data）
        angle_search_range: 角度搜索范围 (min, max)，单位：弧度
        angle_resolution: 角度分辨率，单位：弧度
        
    Returns:
        dbf_result: DBF 结果字典
    """
    from simulators.mimo_simulator import dbf_angle_estimation
    
    # 检查是否有虚拟阵列数据
    if 'virtual_array_data' not in processed_result.extra_data:
        raise ValueError("ProcessedResult 中缺少 virtual_array_data，无法进行 DBF")
    
    virtual_array_data = processed_result.extra_data['virtual_array_data']
    # Shape: [virtual_elements, doppler_bins, range_bins]
    
    # 转置为 [range_bins, doppler_bins, virtual_elements]
    rd_virtual = np.transpose(virtual_array_data, (2, 1, 0))
    
    antenna_array = processed_result.extra_data['antenna_array']
    
    # 调用 DBF 函数
    dbf_result = dbf_angle_estimation(
        rd_virtual,
        antenna_array,
        processed_result.doppler_axis,
        processed_result.range_axis,
        angle_search_range=angle_search_range,
        angle_resolution=angle_resolution
    )
    
    return dbf_result


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
    # 测试 MIMO 处理器
    print("=" * 70)
    print("MIMO 雷达处理器测试")
    print("=" * 70)
    
    from simulators.mimo_simulator import MimoLfmcwSimulator, MimoAntennaArray
    
    # 创建 4T4R MIMO 配置
    antenna_array = MimoAntennaArray(num_tx=4, num_rx=4, fc=77e9)
    
    # 创建 MIMO 仿真器（TDMA 模式）
    mimo_sim = MimoLfmcwSimulator(
        antenna_array=antenna_array,
        waveform_mode='tdma',
        fc=77e9,
        bandwidth=150e6,
        chirp_duration=50e-6,
        fs=10e6,
        prf=5e3,
        num_chirps_per_frame=128
    )
    
    # 定义目标场景
    targets = [
        {"range": 50.0, "velocity": 3.0, "angle": np.radians(10), "rcs": 15},
        {"range": 100.0, "velocity": -2.0, "angle": np.radians(-15), "rcs": 10},
    ]
    
    print(f"\n运行 TDMA MIMO 仿真...")
    sim_result = mimo_sim.simulate(targets, snr_db=25.0, seed=42)
    print(f"✓ 仿真完成，数据形状: {sim_result.raw_data.shape}")
    
    print(f"\n处理 TDMA MIMO 数据...")
    processed = process_mimo(sim_result)
    print(f"✓ 处理完成")
    print(f"  RD 谱形状: {processed.range_doppler.shape}")
    print(f"  距离轴范围: [{processed.range_axis[0]:.1f}, {processed.range_axis[-1]:.1f}] m")
    print(f"  多普勒轴范围: [{processed.doppler_axis[0]:.2f}, {processed.doppler_axis[-1]:.2f}] m/s")
    
    print(f"\n执行 DBF 角度估计...")
    dbf_result = mimo_dbf_angle_estimation(processed)
    print(f"✓ DBF 完成")
    print(f"  检测到的角度数: {len(dbf_result['detected_angles'])}")
    
    if dbf_result['detected_angles']:
        print(f"\n  检测结果:")
        for det in dbf_result['detected_angles'][:5]:  # 只显示前5个
            print(f"    R={det['range']:.1f}m, V={det['doppler']:.2f}m/s, "
                  f"Angle={det['angle_deg']:.1f}°")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)
