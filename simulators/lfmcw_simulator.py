"""
波形生成/仿真层 - LFMCW 雷达仿真模块

本模块实现汽车雷达 LFMCW（线性调频连续波）波形的仿真，
包括目标场景建模和回波信号生成。
"""

import sys
import os

# 添加项目根目录到 Python 路径（支持直接运行此文件）
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional

import numpy as np
from contracts import SimResult
from utils.noise import add_awgn


class LfmcwSimulator:
    """
    LFMCW 雷达仿真器
    
    生成 LFMCW 波形的基带回波数据，模拟汽车雷达场景中的目标反射。
    
    Attributes:
        fc: 载波频率 (Hz)
        bandwidth: 信号带宽 (Hz)
        chirp_duration: chirp 持续时间 (秒)
        fs: 采样率 (Hz)
        prf: 脉冲重复频率 (Hz)
        num_chirps: chirp 数量
        c: 光速 (m/s)
    """
    
    def __init__(
        self,
        fc: float = 77e9,          # 77 GHz 汽车雷达
        bandwidth: float = 150e6,   # 150 MHz 带宽 → 距离分辨率 1.0 m
        chirp_duration: float = 40e-6,  # 40 μs chirp 持续时间
        fs: float = 20e6,           # 20 MHz 采样率 → 800 采样点/chirp
        prf: float = 20e3,          # 20 kHz PRF → chirp 周期 50 μs
        num_chirps: int = 256,      # 256 个 chirps → 速度分辨率 ~0.15 m/s
        c: float = 3e8              # 光速
    ):
        self.fc = fc
        self.bandwidth = bandwidth
        self.chirp_duration = chirp_duration
        self.fs = fs
        self.prf = prf
        self.num_chirps = num_chirps
        self.c = c
        
        # 计算派生参数
        self.samples_per_chirp = int(chirp_duration * fs)
        self.chirp_slope = bandwidth / chirp_duration  # Hz/s
    
    def simulate(
        self,
        targets: list[dict],
        snr_db: float = 20.0,
        seed: Optional[int] = None
    ) -> SimResult:
        """
        执行 LFMCW 雷达仿真
        
        Args:
            targets: 目标列表，每个目标为字典，包含：
                - range: 距离 (米)
                - velocity: 径向速度 (米/秒)，远离雷达为正
                - rcs: 雷达截面积 (dBsm)，可选，默认 0
            snr_db: 信噪比 (dB)
            seed: 随机数种子，用于可重现性
            
        Returns:
            SimResult: 符合契约的仿真结果
        """
        if not targets:
            raise ValueError("目标列表不能为空")

        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = np.random.default_rng()
        
        samples_per_chirp = self.samples_per_chirp
        num_chirps = self.num_chirps
        
        # 初始化基带信号 [1, num_chirps, samples_per_chirp]
        baseband = np.zeros((1, num_chirps, samples_per_chirp), dtype=np.complex128)
        
        # 时间轴
        t_fast = np.arange(samples_per_chirp) / self.fs  # 快时间（chirp 内）
        t_slow = np.arange(num_chirps) / self.prf        # 慢时间（chirp 间）
        
        # 对每个目标生成回波
        for target in targets:
            R = target['range']       # 距离 (m)
            v = target['velocity']    # 速度 (m/s)
            rcs = target.get('rcs', 0)  # RCS (dBsm)
            
            # 计算时延和多普勒频移
            tau = 2 * R / self.c  # 双程时延
            
            # 多普勒频率
            f_doppler = 2 * v * self.fc / self.c
            
            # 目标幅度（考虑 RCS）
            amplitude = 10 ** (rcs / 20.0)
            
            # 生成回波信号
            for n in range(num_chirps):
                # 考虑目标运动引起的时延变化
                R_n = R + v * t_slow[n]
                tau_n = 2 * R_n / self.c
                
                # Chirp 信号（去斜后的基带信号）
                # 差频频率：f_beat = slope * tau
                f_beat = self.chirp_slope * tau_n
                
                # 相位项包含两部分：
                # 1. 快时间维度：差频导致的相位
                # 2. 慢时间维度：多普勒导致的相位变化
                phase_fast = 2 * np.pi * f_beat * t_fast
                phase_slow = 2 * np.pi * f_doppler * t_slow[n]
                phase = phase_fast + phase_slow
                
                # 累加目标回波
                baseband[0, n, :] += amplitude * np.exp(1j * phase)
        
        # 添加噪声
        baseband = add_awgn(baseband, snr_db, rng=rng)
        
        # 构建仿真结果
        sim_result = SimResult(
            name="lfmcw",
            baseband=baseband,
            fc=self.fc,
            bandwidth=self.bandwidth,
            fs=self.fs,
            prf=self.prf,
            num_chirps=num_chirps,
            samples_per_chirp=samples_per_chirp,
            c=self.c,
            target_info={"targets": targets, "snr_db": snr_db}
        )
        
        return sim_result


# 便捷函数：创建默认的汽车雷达 LFMCW 仿真器
def create_automotive_lfmcw_simulator(**kwargs) -> LfmcwSimulator:
    """
    创建具有典型汽车雷达参数的 LFMCW 仿真器
    
    Args:
        **kwargs: 覆盖默认参数的键值对
        
    Returns:
        LfmcwSimulator: 配置好的仿真器实例
    """
    default_params = {
        'fc': 77e9,
        'bandwidth': 150e6,
        'chirp_duration': 40e-6,
        'fs': 20e6,
        'prf': 20e3,
        'num_chirps': 256,
    }
    default_params.update(kwargs)
    return LfmcwSimulator(**default_params)
