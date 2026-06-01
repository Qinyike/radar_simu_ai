"""
坐标轴与绘图边缘计算工具
"""

import numpy as np


def compute_range_axis(
    bandwidth: float,
    num_samples: int,
    c: float = 3e8,
    positive_only: bool = True
) -> np.ndarray:
    """
    计算距离轴（米）

    Args:
        bandwidth: 信号带宽 (Hz)
        num_samples: 快时间采样点数
        c: 光速 (m/s)
        positive_only: 只保留正频率（默认 True）

    Returns:
        距离轴数组
    """
    n = num_samples // 2 if positive_only else num_samples
    dr = c / (2 * bandwidth)
    return np.arange(n) * dr


def compute_doppler_axis(
    prf: float,
    num_pulses: int,
    fc: float,
    c: float = 3e8
) -> np.ndarray:
    """
    计算多普勒速度轴（m/s）

    Args:
        prf: 脉冲重复频率 (Hz)
        num_pulses: 脉冲数
        fc: 载波频率 (Hz)
        c: 光速 (m/s)

    Returns:
        速度轴数组
    """
    freq_axis = np.fft.fftshift(np.fft.fftfreq(num_pulses, d=1 / prf))
    return freq_axis * c / (2 * fc)


def compute_edges(axis: np.ndarray) -> np.ndarray:
    """
    将坐标轴转为 pcolormesh 所需的边缘数组（长度 +1）

    Args:
        axis: 坐标轴数组

    Returns:
        边缘数组
    """
    d = axis[1] - axis[0]
    edges = np.zeros(len(axis) + 1)
    edges[:-1] = axis - d / 2
    edges[-1] = axis[-1] + d / 2
    return edges
