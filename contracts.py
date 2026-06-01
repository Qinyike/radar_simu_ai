"""
数据定义/契约层 - 定义层间通信的核心数据结构和共享领域模型

本模块定义了仿真框架的核心契约和共享模型：
1. Target: 雷达目标数据类
2. RadarConfig: 雷达参数配置
3. MimoAntennaArray: MIMO天线阵列配置
4. RadarSimulator: 仿真器抽象基类
5. SimResult: 仿真层与处理层之间的契约
6. ProcessedResult: 处理层与可视化层之间的契约
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable
import numpy as np


@dataclass
class Target:
    """
    雷达目标

    Attributes:
        range: 距离 (m)
        velocity: 径向速度 (m/s)
        rcs: 雷达截面积 (dBsm)，默认 0
        angle: 目标角度 (rad)，默认 0（非MIMO场景可忽略）
    """
    range: float
    velocity: float
    rcs: float = 0.0
    angle: float = 0.0

    def __post_init__(self):
        if self.range < 0:
            raise ValueError(f"目标距离不能为负: {self.range}")


@dataclass
class RadarConfig:
    """
    雷达参数配置

    Attributes:
        fc: 载波频率 (Hz)，默认 77 GHz
        bandwidth: 信号带宽 (Hz)，默认 150 MHz
        fs: 采样率 (Hz)，默认 20 MHz
        prf: 脉冲重复频率 (Hz)，默认 20 kHz
        num_chirps: chirp 数量，默认 256
        c: 光速 (m/s)，默认 3e8
    """
    fc: float = 77e9
    bandwidth: float = 150e6
    fs: float = 20e6
    prf: float = 20e3
    num_chirps: int = 256
    c: float = 3e8

    def __post_init__(self):
        if self.fc <= 0:
            raise ValueError(f"载波频率必须为正: {self.fc}")
        if self.bandwidth <= 0:
            raise ValueError(f"带宽必须为正: {self.bandwidth}")
        if self.fs <= 0:
            raise ValueError(f"采样率必须为正: {self.fs}")
        if self.prf <= 0:
            raise ValueError(f"PRF必须为正: {self.prf}")
        if self.num_chirps <= 0:
            raise ValueError(f"chirp数量必须为正: {self.num_chirps}")
        if self.c <= 0:
            raise ValueError(f"光速必须为正: {self.c}")


class RadarSimulator(ABC):
    """仿真器抽象基类"""

    @abstractmethod
    def simulate(self, targets, snr_db: float = 20.0, seed: Optional[int] = None) -> "SimResult":
        """
        执行雷达仿真

        Args:
            targets: 目标列表 (list[Target] 或 list[dict])
            snr_db: 信噪比 (dB)
            seed: 随机种子

        Returns:
            SimResult: 仿真结果
        """
        ...


@runtime_checkable
class SignalProcessor(Protocol):
    """信号处理器协议"""

    def __call__(self, sim_result: "SimResult", **kwargs) -> "ProcessedResult":
        """
        处理仿真结果

        Args:
            sim_result: 仿真结果契约对象
            **kwargs: 传递给处理函数的额外参数

        Returns:
            ProcessedResult: 处理结果
        """
        ...


def _normalize_targets(targets) -> list[Target]:
    """将 dict 或 Target 列表统一为 Target 列表"""
    normalized = []
    for t in targets:
        if isinstance(t, Target):
            normalized.append(t)
        elif isinstance(t, dict):
            normalized.append(Target(
                range=t['range'],
                velocity=t['velocity'],
                rcs=t.get('rcs', 0),
                angle=t.get('angle', 0)
            ))
        else:
            raise TypeError(f"不支持的目标类型: {type(t)}")
    return normalized


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
