"""
数据定义/契约层 - 定义层间通信的核心数据结构

本模块定义了仿真框架的两个核心契约：
1. SimResult: 仿真层与处理层之间的契约
2. ProcessedResult: 处理层与可视化层之间的契约
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class SimResult:
    """
    仿真结果契约 (SimResult)
    
    目的：仿真层与处理层之间的契约
    内容：包含所有处理算法所需的原始数据与关键参数
    
    Attributes:
        name: 波形标识（如 "lfmcw", "fmcw"）
        baseband: 原始基带回波数据，维度 [channels, pulses, samples]
        fc: 载波频率 (Hz)
        bandwidth: 信号带宽 (Hz)
        fs: 采样率 (Hz)
        prf: 脉冲重复频率 (Hz)
        num_chirps: chirp 数量
        samples_per_chirp: 每个 chirp 的采样点数
        c: 光速 (m/s)，默认 3e8
        target_info: 目标信息字典（可选，用于验证）
    """
    name: str
    baseband: np.ndarray
    fc: float
    bandwidth: float
    fs: float
    prf: float
    num_chirps: int
    samples_per_chirp: int
    c: float = 3e8
    target_info: Optional[dict] = field(default_factory=dict)
    
    def __post_init__(self):
        """验证数据结构完整性"""
        if not isinstance(self.baseband, np.ndarray):
            raise TypeError("baseband 必须是 numpy ndarray")
        
        expected_shape = (1, self.num_chirps, self.samples_per_chirp)
        if self.baseband.shape != expected_shape:
            raise ValueError(
                f"baseband 形状应为 {expected_shape}，实际为 {self.baseband.shape}"
            )


@dataclass
class ProcessedResult:
    """
    处理结果契约 (ProcessedResult)
    
    目的：处理层与可视化层之间的契约
    内容：包含所有可视化所需的处理结果与坐标轴信息
    
    Attributes:
        name: 结果标识
        range_profile: 距离剖面，维度 [num_ranges]
        range_doppler: 距离-多普勒谱，维度 [num_ranges, num_dopplers]
        range_axis: 距离轴，物理单位米，维度 [num_ranges]
        doppler_axis: 多普勒轴，物理单位米/秒，维度 [num_dopplers]
    """
    name: str
    range_profile: np.ndarray
    range_doppler: np.ndarray
    range_axis: np.ndarray
    doppler_axis: np.ndarray
    
    def __post_init__(self):
        """验证数据结构完整性"""
        if not isinstance(self.range_profile, np.ndarray):
            raise TypeError("range_profile 必须是 numpy ndarray")
        if not isinstance(self.range_doppler, np.ndarray):
            raise TypeError("range_doppler 必须是 numpy ndarray")
        if not isinstance(self.range_axis, np.ndarray):
            raise TypeError("range_axis 必须是 numpy ndarray")
        if not isinstance(self.doppler_axis, np.ndarray):
            raise TypeError("doppler_axis 必须是 numpy ndarray")
        
        # 验证维度一致性
        if self.range_doppler.shape[0] != len(self.range_axis):
            raise ValueError(
                f"range_doppler 第一维 ({self.range_doppler.shape[0]}) "
                f"应与 range_axis 长度 ({len(self.range_axis)}) 一致"
            )
        if self.range_doppler.shape[1] != len(self.doppler_axis):
            raise ValueError(
                f"range_doppler 第二维 ({self.range_doppler.shape[1]}) "
                f"应与 doppler_axis 长度 ({len(self.doppler_axis)}) 一致"
            )
