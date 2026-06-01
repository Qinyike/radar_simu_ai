"""
物理层共享工具函数

提供跨模块使用的雷达物理计算，避免在仿真器和可视化器中重复实现。
"""

import numpy as np


def rcs_to_amplitude(rcs: float) -> float:
    """
    将 RCS (dBsm) 转换为线性幅度

    Args:
        rcs: 雷达截面积 (dBsm)

    Returns:
        线性幅度
    """
    return 10 ** (rcs / 20.0)


def compute_doppler_frequency(velocity: float, fc: float, c: float = 3e8) -> float:
    """
    计算多普勒频移

    Args:
        velocity: 目标径向速度 (m/s)
        fc: 载波频率 (Hz)
        c: 光速 (m/s)

    Returns:
        多普勒频率 (Hz)
    """
    return 2 * velocity * fc / c


def compute_max_unambiguous_velocity(prf: float, fc: float, c: float = 3e8) -> float:
    """
    计算最大不模糊速度

    Args:
        prf: 脉冲重复频率 (Hz)
        fc: 载波频率 (Hz)
        c: 光速 (m/s)

    Returns:
        最大不模糊速度 (m/s)，正值
    """
    return c * prf / (4 * fc)


def wrap_velocity(velocity: float, max_velocity: float) -> float:
    """
    计算多普勒模糊后的速度（考虑周期性）

    多普勒频率是周期性的，周期为 PRF，
    对应的速度周期为 2 * max_velocity。

    Args:
        velocity: 真实速度 (m/s)
        max_velocity: 最大不模糊速度 (m/s)

    Returns:
        模糊后的速度 (m/s)，在 [-max_velocity, max_velocity] 范围内
    """
    velocity_range = 2 * max_velocity
    return ((velocity + max_velocity) % velocity_range) - max_velocity


def compute_two_way_delay(distance: float, c: float = 3e8) -> float:
    """
    计算双程传播时延

    Args:
        distance: 目标距离 (m)
        c: 光速 (m/s)

    Returns:
        双程时延 (s)
    """
    return 2 * distance / c
