"""
信号处理/算法层 - LFMCW 雷达信号处理

本模块实现 LFMCW 雷达的核心信号处理算法：
1. 距离 FFT（快时间 FFT）
2. 多普勒 FFT（慢时间 FFT）
3. 距离-多普勒谱生成
4. 距离剖面提取
"""

import sys
import os

# 添加项目根目录到 Python 路径（支持直接运行此文件）
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from contracts import SimResult, ProcessedResult
from processors.window_utils import get_window
from utils.axes import compute_range_axis, compute_doppler_axis


def range_fft(
    baseband: np.ndarray,
    window: str = "taylor"
) -> np.ndarray:
    """
    对基带数据进行距离 FFT（快时间维度）
    
    Args:
        baseband: 基带数据，形状 [channels, pulses, samples]
        window: 窗函数类型（hamming/hanning/blackman/taylor/kaiser/none）
        
    Returns:
        距离 FFT 结果，形状 [channels, pulses, samples//2]
    """
    _, num_pulses, num_samples = baseband.shape
    
    win = get_window(window, num_samples)
    
    windowed_data = baseband * win[np.newaxis, np.newaxis, :]
    range_fft_result = np.fft.fft(windowed_data, axis=2)
    
    # 只保留正频率部分
    num_range_bins = num_samples // 2
    range_fft_result = range_fft_result[:, :, :num_range_bins]
    
    return range_fft_result


def doppler_fft(
    range_fft_data: np.ndarray,
    window: str = "taylor"
) -> np.ndarray:
    """
    对距离 FFT 结果进行多普勒 FFT（慢时间维度）
    
    Args:
        range_fft_data: 距离 FFT 结果，形状 [channels, pulses, range_bins]
        window: 窗函数类型（hamming/hanning/blackman/taylor/kaiser/none）
        
    Returns:
        距离-多普勒谱，形状 [channels, doppler_bins, range_bins]
    """
    _, num_pulses, num_range_bins = range_fft_data.shape
    
    win = get_window(window, num_pulses)
    
    windowed_data = range_fft_data * win[np.newaxis, :, np.newaxis]
    rd_spectrum = np.fft.fftshift(np.fft.fft(windowed_data, axis=1), axes=1)
    
    return rd_spectrum


def process_lfmcw(
    sim_result: SimResult,
    range_window: str = "taylor",
    doppler_window: str = "taylor"
) -> ProcessedResult:
    """
    处理 LFMCW 仿真结果，生成距离-多普勒谱
    
    Args:
        sim_result: 仿真结果契约对象
        range_window: 距离维窗函数（hamming/hanning/blackman/taylor/kaiser/none）
        doppler_window: 多普勒维窗函数
        
    Returns:
        ProcessedResult: 处理结果契约对象
    """
    # 提取参数
    baseband = sim_result.baseband
    fc = sim_result.fc
    bandwidth = sim_result.bandwidth
    fs = sim_result.fs
    prf = sim_result.prf
    num_chirps = sim_result.num_chirps
    samples_per_chirp = sim_result.samples_per_chirp
    c = sim_result.c
    
    # Step 1: 距离 FFT
    range_fft_data = range_fft(baseband, window=range_window)
    
    # Step 2: 多普勒 FFT
    rd_spectrum = doppler_fft(range_fft_data, window=doppler_window)
    
    # Step 3: 计算坐标轴
    range_axis = compute_range_axis(bandwidth, samples_per_chirp, c, positive_only=True)
    doppler_axis = compute_doppler_axis(prf, num_chirps, fc, c)
    
    # Step 4: 提取距离剖面（沿多普勒维度的最大值投影）
    # rd_spectrum[0, :, :] 的形状是 [doppler_bins, range_bins]
    # 需要转置为 [range_bins, doppler_bins] 以符合契约
    rd_spectrum_2d = rd_spectrum[0, :, :].T  # 转置：[range_bins, doppler_bins]
    range_profile = np.max(np.abs(rd_spectrum_2d), axis=1)  # 沿多普勒维度取最大值
    
    # 构建处理结果
    processed_result = ProcessedResult(
        name=f"{sim_result.name}_processed",
        range_profile=range_profile,
        range_doppler=np.abs(rd_spectrum_2d),
        range_axis=range_axis,
        doppler_axis=doppler_axis
    )
    
    return processed_result
