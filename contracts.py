"""
数据定义/契约层 - 定义层间通信的核心数据结构和共享领域模型

本模块定义了仿真框架的核心契约和共享模型：
1. MimoAntennaArray: MIMO天线阵列配置（共享领域模型）
2. SimResult: 仿真层与处理层之间的契约
3. ProcessedResult: 处理层与可视化层之间的契约
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np


class MimoAntennaArray:
    """
    MIMO天线阵列配置

    Attributes:
        num_tx: 发射天线数量
        num_rx: 接收天线数量
        tx_spacing: 发射天线间距 (米)
        rx_spacing: 接收天线间距 (米)
        wavelength: 波长 (米)
        virtual_array_size: 虚拟阵列大小
        effective_aperture: 有效孔径 (米)
    """

    def __init__(
        self,
        num_tx: int = 4,
        num_rx: int = 4,
        tx_spacing: float = None,
        rx_spacing: float = None,
        fc: float = 77e9,
        c: float = 3e8
    ):
        self.num_tx = num_tx
        self.num_rx = num_rx
        self.wavelength = c / fc

        if tx_spacing is None:
            self.tx_spacing = num_rx * self.wavelength / 2
        else:
            self.tx_spacing = tx_spacing

        if rx_spacing is None:
            self.rx_spacing = self.wavelength / 2
        else:
            self.rx_spacing = rx_spacing

        self.virtual_array_size = num_tx * num_rx
        self.effective_aperture = (num_tx - 1) * self.tx_spacing + (num_rx - 1) * self.rx_spacing

    def get_virtual_element_positions(self) -> np.ndarray:
        """
        获取虚拟阵列元素位置

        Returns:
            virtual_positions: 虚拟阵列元素位置数组 (virtual_array_size,)
        """
        positions = []
        for tx_idx in range(self.num_tx):
            tx_pos = tx_idx * self.tx_spacing
            for rx_idx in range(self.num_rx):
                rx_pos = rx_idx * self.rx_spacing
                positions.append(tx_pos + rx_pos)

        return np.array(positions)

    def get_steering_vector(self, angle: float) -> np.ndarray:
        """
        计算导向矢量（Steering Vector）

        Args:
            angle: 目标角度（弧度），相对于法线方向

        Returns:
            steering_vec: 虚拟阵列导向矢量 (virtual_array_size,)
        """
        virtual_positions = self.get_virtual_element_positions()
        k = 2 * np.pi / self.wavelength
        phase = k * virtual_positions * np.sin(angle)
        return np.exp(1j * phase)


@dataclass
class SimResult:
    """
    仿真结果契约 (SimResult)
    
    目的：仿真层与处理层之间的契约
    内容：包含所有处理算法所需的原始数据与关键参数
    
    Attributes:
        name: 波形标识（如 "lfmcw", "fmcw", "mimo_tdma", "mimo_ddma"）
        baseband: 原始基带回波数据
                  - 对于 LFMCW: 维度 [1, num_chirps, samples]
                  - 对于 MIMO: 维度 [num_rx, total_chirps, samples]
        fc: 载波频率 (Hz)
        bandwidth: 信号带宽 (Hz)
        fs: 采样率 (Hz)
        prf: 脉冲重复频率 (Hz)
        num_chirps: chirp 数量（对于 MIMO 是每帧 chirp 数）
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
        
        # 对于 MIMO，baseband shape 是 [num_rx, total_chirps, samples]
        # 对于 LFMCW，baseband shape 是 [1, num_chirps, samples]
        if len(self.baseband.shape) != 3:
            raise ValueError(
                f"baseband 必须是 3D 数组，实际维度为 {len(self.baseband.shape)}"
            )

@dataclass
class ProcessedResult:
    """
    处理结果契约 (ProcessedResult)
    
    目的：处理层与可视化层之间的契约
    内容：包含所有可视化所需的处理结果与坐标轴信息
    
    Attributes:
        name: 结果标识（如 "lfmcw", "mimo_tdma", "mimo_ddma"）
        range_profile: 距离剖面，维度 [num_ranges]
        range_doppler: 距离-多普勒谱，维度 [num_ranges, num_dopplers]
        range_axis: 距离轴，物理单位米，维度 [num_ranges]
        doppler_axis: 多普勒轴，物理单位米/秒，维度 [num_dopplers]
        extra_data: 额外数据字典（可选，用于 MIMO 等特殊需求）
    """
    name: str
    range_profile: np.ndarray
    range_doppler: np.ndarray
    range_axis: np.ndarray
    doppler_axis: np.ndarray
    extra_data: Optional[dict] = field(default_factory=dict)
    
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
