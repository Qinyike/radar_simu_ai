"""
MIMO 雷达仿真模块 - 支持 TDMA/DDMA 波形和 DBF 解角

本模块实现 MIMO（多输入多输出）汽车雷达的仿真，包括：
- 4T4R（4发4收）天线阵列配置
- TDMA（时分多址）波形
- DDMA（频分多址/相位编码）波形  
- DBF（数字波束形成）角度估计
"""

import sys
import os

# 添加项目根目录到 Python 路径
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, List
import numpy as np
from contracts import SimResult
from utils.noise import add_awgn


class MimoAntennaArray:
    """
    MIMO 天线阵列配置
    
    Attributes:
        num_tx: 发射天线数量
        num_rx: 接收天线数量
        tx_spacing: 发射天线间距 (米)
        rx_spacing: 接收天线间距 (米)
        wavelength: 波长 (米)
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
        
        # 默认天线间距：RX 半波长，TX 为 N_rx 倍半波长（形成均匀虚拟阵列）
        if tx_spacing is None:
            self.tx_spacing = num_rx * self.wavelength / 2
        else:
            self.tx_spacing = tx_spacing
            
        if rx_spacing is None:
            self.rx_spacing = self.wavelength / 2
        else:
            self.rx_spacing = rx_spacing
        
        # 计算虚拟阵列（等效孔径）- 使用已赋值的实例变量
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
                # 虚拟元素位置 = TX位置 + RX位置
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
        
        # 导向矢量: exp(j * 2π * d * sin(θ) / λ)
        k = 2 * np.pi / self.wavelength
        phase = k * virtual_positions * np.sin(angle)
        
        return np.exp(1j * phase)


class MimoLfmcwSimulator:
    """
    MIMO LFMCW 雷达仿真器
    
    支持 TDMA 和 DDMA 两种 MIMO 波形模式。
    
    Attributes:
        antenna_array: MIMO 天线阵列配置
        waveform_mode: 波形模式 ('tdma' 或 'ddma')
        fc: 载波频率 (Hz)
        bandwidth: 信号带宽 (Hz)
        chirp_duration: chirp 持续时间 (秒)
        fs: 采样率 (Hz)
        prf: 脉冲重复频率 (Hz)
        num_chirps_per_frame: 每帧 chirp 数量
        c: 光速 (m/s)
    """
    
    def __init__(
        self,
        antenna_array: Optional[MimoAntennaArray] = None,
        waveform_mode: str = 'tdma',
        fc: float = 77e9,
        bandwidth: float = 150e6,
        chirp_duration: float = 40e-6,
        fs: float = 20e6,
        prf: float = 20e3,
        num_chirps_per_frame: int = 128,
        c: float = 3e8
    ):
        # 默认使用 4T4R 配置
        if antenna_array is None:
            self.antenna_array = MimoAntennaArray(num_tx=4, num_rx=4, fc=fc, c=c)
        else:
            self.antenna_array = antenna_array
        
        self.waveform_mode = waveform_mode.lower()
        if self.waveform_mode not in ['tdma', 'ddma']:
            raise ValueError(f"不支持的波形模式: {waveform_mode}，请使用 'tdma' 或 'ddma'")
        
        self.fc = fc
        self.bandwidth = bandwidth
        self.chirp_duration = chirp_duration
        self.fs = fs
        self.prf = prf
        self.num_chirps_per_frame = num_chirps_per_frame
        self.c = c
        self.wavelength = c / fc
        self.chirp_slope = bandwidth / chirp_duration
        
        # 计算最大不模糊速度
        # TDMA 模式下有效 PRF = prf / num_tx
        if self.waveform_mode == 'tdma':
            effective_prf = self.prf / self.antenna_array.num_tx
        else:
            effective_prf = self.prf
        self.max_unambiguous_velocity = self.c * effective_prf / (4 * self.fc)
        
    def _calculate_target_beat(
        self,
        target_range: float,
        target_velocity: float,
        target_angle: float,
        target_rcs: float,
        tx_antenna_idx: int,
        rx_antenna_idx: int,
        chirp_idx: int,
        t_fast: np.ndarray,
    ) -> np.ndarray:
        """
        计算单个目标的差拍信号（beat signal）

        生成的是去斜（dechirp）后的基带差拍信号，与 LFMCW 处理器兼容。

        Args:
            target_range: 目标距离 (m)
            target_velocity: 目标速度 (m/s)
            target_angle: 目标角度 (rad)
            target_rcs: 目标 RCS (dBsm)
            tx_antenna_idx: 发射天线索引
            rx_antenna_idx: 接收天线索引
            chirp_idx: chirp 序号（慢时间索引）
            t_fast: 快时间向量（chirp 内采样时间）

        Returns:
            beat: 差拍信号
        """
        # 考虑目标运动引起的距离变化
        R_n = target_range + target_velocity * chirp_idx / self.prf
        tau_n = 2 * R_n / self.c

        # 差拍频率: f_beat = K * tau
        f_beat = self.chirp_slope * tau_n

        # 多普勒频率: fd = 2v*fc/c
        f_doppler = 2 * target_velocity * self.fc / self.c

        # 天线相位（导向矢量）
        tx_position = tx_antenna_idx * self.antenna_array.tx_spacing
        rx_position = rx_antenna_idx * self.antenna_array.rx_spacing
        k_wave = 2 * np.pi / self.wavelength
        phase_angle = k_wave * (tx_position + rx_position) * np.sin(target_angle)

        # 目标幅度
        amplitude = 10 ** (target_rcs / 20.0)

        # 差拍信号相位
        phase_fast = 2 * np.pi * f_beat * t_fast
        phase_slow = 2 * np.pi * f_doppler * chirp_idx / self.prf

        return amplitude * np.exp(1j * (phase_fast + phase_slow + phase_angle))
    
    def simulate_tdma(
        self,
        targets: List[dict],
        snr_db: float = 25.0,
        seed: Optional[int] = None
    ) -> SimResult:
        """
        TDMA MIMO 仿真
        
        TDMA 模式下，每个 chirp 只激活一个 TX 天线，按顺序轮流发射。
        
        Args:
            targets: 目标列表，每个目标包含 {'range', 'velocity', 'angle', 'rcs'}
            snr_db: 信噪比 (dB)
            seed: 随机种子
            
        Returns:
            sim_result: 仿真结果契约对象
        """
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = np.random.default_rng()
        
        num_tx = self.antenna_array.num_tx
        num_rx = self.antenna_array.num_rx
        num_samples = int(self.chirp_duration * self.fs)
        
        # TDMA 需要 num_tx 倍的时间来遍历所有 TX
        total_chirps = self.num_chirps_per_frame * num_tx
        
        # 时间向量（快时间）
        t_fast = np.arange(num_samples) / self.fs
        
        # 初始化接收数据 [num_rx, total_chirps, num_samples]
        rx_data = np.zeros((num_rx, total_chirps, num_samples), dtype=np.complex128)
        
        # 对每个 chirp 进行仿真
        for chirp_idx in range(total_chirps):
            # TDMA: 确定当前激活的 TX 天线
            tx_antenna_idx = chirp_idx % num_tx
            
            # 累加所有目标的回波
            for target in targets:
                # 对所有 RX 天线计算独立回波（含不同天线相位）
                for rx_idx in range(num_rx):
                    beat = self._calculate_target_beat(
                        target['range'],
                        target['velocity'],
                        target['angle'],
                        target['rcs'],
                        tx_antenna_idx,
                        rx_idx,
                        chirp_idx,
                        t_fast,
                    )
                    rx_data[rx_idx, chirp_idx, :] += beat
        
        # 添加噪声
        rx_data = add_awgn(rx_data, snr_db, rng=rng)
        
        # 构建目标信息
        target_info = {
            'targets': targets,
            'waveform_mode': 'tdma',
            'num_tx': num_tx,
            'num_rx': num_rx,
            'total_chirps': total_chirps
        }
        
        return SimResult(
            name='mimo_tdma',
            baseband=rx_data,
            fc=self.fc,
            bandwidth=self.bandwidth,
            fs=self.fs,
            prf=self.prf,
            num_chirps=self.num_chirps_per_frame,
            samples_per_chirp=num_samples,
            c=self.c,
            target_info=target_info
        )
    
    def simulate_ddma(
        self,
        targets: List[dict],
        snr_db: float = 25.0,
        seed: Optional[int] = None
    ) -> SimResult:
        """
        DDMA MIMO 仿真
        
        DDMA 模式下，所有 TX 天线同时发射，但使用不同的相位编码区分。
        
        Args:
            targets: 目标列表，每个目标包含 {'range', 'velocity', 'angle', 'rcs'}
            snr_db: 信噪比 (dB)
            seed: 随机种子
            
        Returns:
            sim_result: 仿真结果契约对象
        """
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = np.random.default_rng()
        
        num_tx = self.antenna_array.num_tx
        num_rx = self.antenna_array.num_rx
        num_samples = int(self.chirp_duration * self.fs)
        
        # DDMA: 所有 chirp 都使用
        total_chirps = self.num_chirps_per_frame
        
        # 时间向量（快时间）
        t_fast = np.arange(num_samples) / self.fs
        
        # 初始化接收数据 [num_rx, total_chirps, num_samples]
        rx_data = np.zeros((num_rx, total_chirps, num_samples), dtype=np.complex128)
        
        # DDMA 相位编码矩阵 [num_tx, total_chirps]
        # 使用正交相位序列区分不同 TX
        ddma_codes = self._generate_ddma_codes(num_tx, total_chirps)
        
        # 对每个 chirp 进行仿真
        for chirp_idx in range(total_chirps):
            # 累加所有目标的回波
            for target in targets:
                # 对所有 RX 天线计算独立回波
                for rx_idx in range(num_rx):
                    combined_beat = np.zeros(num_samples, dtype=np.complex128)
                    
                    # 对所有 TX 天线求和（DDMA 同时发射）
                    for tx_idx in range(num_tx):
                        # 应用 DDMA 相位编码
                        phase_code = ddma_codes[tx_idx, chirp_idx]
                        
                        beat = self._calculate_target_beat(
                            target['range'],
                            target['velocity'],
                            target['angle'],
                            target['rcs'],
                            tx_idx,
                            rx_idx,
                            chirp_idx,
                            t_fast,
                        )
                        
                        combined_beat += beat * phase_code
                    
                    rx_data[rx_idx, chirp_idx, :] += combined_beat
        
        # 添加噪声
        rx_data = add_awgn(rx_data, snr_db, rng=rng)
        
        # 构建目标信息
        target_info = {
            'targets': targets,
            'waveform_mode': 'ddma',
            'num_tx': num_tx,
            'num_rx': num_rx,
            'total_chirps': total_chirps,
            'ddma_codes': ddma_codes
        }
        
        return SimResult(
            name='mimo_ddma',
            baseband=rx_data,
            fc=self.fc,
            bandwidth=self.bandwidth,
            fs=self.fs,
            prf=self.prf,
            num_chirps=total_chirps,
            samples_per_chirp=num_samples,
            c=self.c,
            target_info=target_info
        )
    
    def _generate_ddma_codes(self, num_tx: int, num_chirps: int) -> np.ndarray:
        """
        生成 DDMA 相位编码
        
        使用正交相位序列（如 Hadamard 码或循环移位）
        
        Args:
            num_tx: TX 天线数量
            num_chirps: chirp 数量
            
        Returns:
            codes: 相位编码矩阵 [num_tx, num_chirps]
        """
        codes = np.zeros((num_tx, num_chirps), dtype=np.complex128)
        
        # 方法1: 使用循环相移（简单且有效）
        for tx_idx in range(num_tx):
            phase_shift = 2 * np.pi * tx_idx / num_tx
            codes[tx_idx, :] = np.exp(1j * phase_shift * np.arange(num_chirps))
        
        return codes
    
    def simulate(
        self,
        targets: List[dict],
        snr_db: float = 25.0,
        seed: Optional[int] = None
    ) -> SimResult:
        """
        MIMO 仿真主接口
        
        Args:
            targets: 目标列表，每个目标包含:
                - range: 距离 (m)
                - velocity: 速度 (m/s)
                - angle: 角度 (rad)，相对于法线方向
                - rcs: RCS (dBsm)
            snr_db: 信噪比 (dB)
            seed: 随机种子
            
        Returns:
            sim_result: 仿真结果契约对象
        """
        if self.waveform_mode == 'tdma':
            return self.simulate_tdma(targets, snr_db, seed)
        elif self.waveform_mode == 'ddma':
            return self.simulate_ddma(targets, snr_db, seed)
        else:
            raise ValueError(f"不支持的波形模式: {self.waveform_mode}")


def dbf_angle_estimation(
    rd_spectrum: np.ndarray,
    antenna_array: MimoAntennaArray,
    doppler_axis: np.ndarray,
    range_axis: np.ndarray,
    angle_search_range: tuple = (-np.pi/3, np.pi/3),
    angle_resolution: float = np.pi/180,
    angle_window: str = 'taylor'
) -> dict:
    """DBF 角度估计（已移至 processors.mimo_processor，保留向后兼容）"""
    from processors.mimo_processor import dbf_angle_estimation as _dbf
    return _dbf(rd_spectrum, antenna_array, doppler_axis, range_axis,
                angle_search_range, angle_resolution, angle_window)


if __name__ == "__main__":
    # 测试 MIMO 仿真器
    print("=" * 70)
    print("MIMO 雷达仿真器测试")
    print("=" * 70)
    
    # 创建 4T4R MIMO 配置
    antenna_array = MimoAntennaArray(num_tx=4, num_rx=4, fc=77e9)
    print(f"\n天线阵列配置:")
    print(f"  TX 天线数: {antenna_array.num_tx}")
    print(f"  RX 天线数: {antenna_array.num_rx}")
    print(f"  虚拟阵列大小: {antenna_array.virtual_array_size}")
    print(f"  有效孔径: {antenna_array.effective_aperture:.4f} m")
    
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
    
    print(f"\n仿真参数:")
    print(f"  波形模式: {mimo_sim.waveform_mode.upper()}")
    print(f"  最大不模糊速度: ±{mimo_sim.max_unambiguous_velocity:.2f} m/s")
    
    # 定义目标场景（包含角度信息）
    targets = [
        {"range": 50.0, "velocity": 3.0, "angle": np.radians(10), "rcs": 15},
        {"range": 100.0, "velocity": -2.0, "angle": np.radians(-15), "rcs": 10},
        {"range": 150.0, "velocity": 0.0, "angle": np.radians(0), "rcs": 8},
    ]
    
    print(f"\n目标场景:")
    for i, t in enumerate(targets, 1):
        print(f"  T{i}: R={t['range']}m, V={t['velocity']}m/s, "
              f"Angle={np.degrees(t['angle']):.1f}°, RCS={t['rcs']}dBsm")
    
    # 运行仿真
    print("\n正在运行 MIMO 仿真...")
    sim_result = mimo_sim.simulate(targets, snr_db=25.0, seed=42)
    print(f"✓ 仿真完成")
    print(f"  接收数据形状: {sim_result.raw_data.shape}")
    print(f"  [RX天线, Chirps, 采样点]")
    
    # 测试 DBF 角度估计
    print("\n测试 DBF 角度估计...")
    # 这里需要先将原始数据处理成 RD 谱 + 虚拟阵列维度
    # 简化示例：假设已经处理好了
    print("  DBF 功能已就绪，需要在处理器中集成")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)
