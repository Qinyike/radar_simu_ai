"""
波形生成/仿真层 - PMCW 雷达仿真模块

PMCW (Phase Modulated Continuous Wave) 使用相位编码序列调制连续波：
- TX 发射相位编码信号（Barker 码、m 序列等）
- RX 通过匹配滤波（相关运算）实现距离压缩
- 多个码重复周期做 Doppler FFT 得到距离-多普勒谱

真实汽车 PMCW 雷达典型参数：
- 码片速率: 100~500 Mchip/s（决定带宽和距离分辨率）
- 码长: 511~4095（m 序列或 Gold 码）
- PRI: 20~100 μs（含保护间隔，独立于码长控制 PRF）
- PRF: 10~50 kHz（由 PRI 决定，与码长无关）

距离分辨率: ΔR = c / (2 * chip_rate)
最大不模糊距离: R_max = N * ΔR（N 为码长）
最大不模糊速度: v_max = c * PRF / (4 * fc)
"""

import sys
import os

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
import numpy as np
from contracts import SimResult
from utils.noise import add_awgn


def generate_barker_code(length: int) -> np.ndarray:
    """生成 Barker 码（BPSK: +1/-1）"""
    codes = {
        2:  [1, -1],
        3:  [1, 1, -1],
        4:  [1, 1, -1, 1],
        5:  [1, 1, 1, -1, 1],
        7:  [1, 1, 1, -1, -1, 1, -1],
        11: [1, 1, 1, -1, -1, -1, 1, -1, -1, 1, -1],
        13: [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1],
    }
    if length not in codes:
        raise ValueError(f"Barker 码不支持长度 {length}，可选: {list(codes.keys())}")
    return np.array(codes[length], dtype=np.float64)


def generate_msequence(n_bits: int) -> np.ndarray:
    """
    生成 m 序列（最大长度序列），长度 = 2^n_bits - 1

    使用 LFSR（线性反馈移位寄存器）实现。
    """
    length = 2 ** n_bits - 1

    primitive_polys = {
        2: 0o7, 3: 0o13, 4: 0o23, 5: 0o45, 6: 0o103,
        7: 0o211, 8: 0o435, 9: 0o1021, 10: 0o2011,
    }

    if n_bits not in primitive_polys:
        raise ValueError(f"m 序列不支持 n_bits={n_bits}，可选: {list(primitive_polys.keys())}")

    poly = primitive_polys[n_bits]
    taps = [i for i in range(n_bits + 1) if (poly >> i) & 1]

    register = [1] * n_bits
    output = []
    for _ in range(length):
        output.append(register[-1])
        feedback = 0
        for t in taps:
            if t > 0:
                feedback ^= register[t - 1]
        register = [feedback] + register[:-1]

    return np.array([2 * b - 1 for b in output], dtype=np.float64)


def generate_pmcw_code(code_type: str, code_length: int) -> np.ndarray:
    """
    生成 PMCW 相位编码序列

    Args:
        code_type: 'barker' 或 'mseq'
        code_length: 码长

    Returns:
        BPSK 相位编码 [+1, -1, ...]
    """
    code_type = code_type.lower()
    if code_type == 'barker':
        return generate_barker_code(code_length)
    elif code_type in ('mseq', 'm-sequence', 'm_sequence'):
        n = 2
        while 2 ** n - 1 < code_length:
            n += 1
        code = generate_msequence(n)
        return code[:code_length]
    else:
        raise ValueError(f"不支持的码类型: '{code_type}'，可选: 'barker', 'mseq'")


class PmcwSimulator:
    """
    PMCW 雷达仿真器

    真实汽车 PMCW 雷达信号模型：
    - 每个 PRI 由【活跃码持续时间 + 保护间隔】组成
    - 活跃码: N 个 BPSK 码片，采样率 = chip_rate
    - 保护间隔: 纯静默，不发射/不采样
    - PRF = 1/PRI，与码长和码片速率独立可控

    典型参数（77 GHz 车载 PMCW）：
    - chip_rate = 250 Mchip/s → ΔR = 0.6 m
    - code_length = 1023 (m-sequence n=10) → R_max = 614 m
    - code_duration = 4.09 μs
    - PRI = 50 μs → PRF = 20 kHz → v_max = ±19.5 m/s
    - guard_interval = 45.91 μs
    """

    def __init__(
        self,
        fc: float = 77e9,
        chip_rate: float = 250e6,
        code_type: str = 'mseq',
        code_length: int = 1023,
        pri: float = 50e-6,
        num_pulses: int = 256,
        c: float = 3e8
    ):
        self.fc = fc
        self.chip_rate = chip_rate
        self.code = generate_pmcw_code(code_type, code_length)
        self.code_length = len(self.code)
        self.pri = pri
        self.num_pulses = num_pulses
        self.c = c

        self.chip_duration = 1.0 / chip_rate
        self.code_duration = self.code_length * self.chip_duration
        self.prf = 1.0 / pri
        self.bandwidth = chip_rate
        self.samples_per_chirp = self.code_length

        if self.code_duration >= pri:
            raise ValueError(
                f"码持续时间 ({self.code_duration*1e6:.2f} μs) "
                f">= PRI ({pri*1e6:.1f} μs)，请增大 PRI 或减小码长/码片速率"
            )
        self.guard_interval = pri - self.code_duration

    def simulate(
        self,
        targets: list[dict],
        snr_db: float = 20.0,
        seed: Optional[int] = None
    ) -> SimResult:
        """
        执行 PMCW 雷达仿真

        Args:
            targets: 目标列表，每个目标含 range/velocity/rcs
            snr_db: 信噪比 (dB)
            seed: 随机种子

        Returns:
            SimResult: 仿真结果
        """
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = np.random.default_rng()

        N = self.code_length
        P = self.num_pulses
        code = self.code
        Tc = self.chip_duration

        baseband = np.zeros((1, P, N), dtype=np.complex128)
        t_pulse = np.arange(P) * self.pri

        for target in targets:
            R = target['range']
            v = target['velocity']
            rcs = target.get('rcs', 0)
            amplitude = 10 ** (rcs / 20.0)
            fd = 2 * v * self.fc / self.c

            for n in range(P):
                R_n = R + v * t_pulse[n]
                tau_n = 2 * R_n / self.c
                delay_n = tau_n / Tc

                int_delay = int(np.floor(delay_n))
                frac_delay = delay_n - int_delay

                shifted_code = np.roll(code, int_delay)

                if abs(frac_delay) > 1e-10:
                    phase_correction = np.exp(
                        -1j * 2 * np.pi * frac_delay * np.arange(N) / N
                    )
                    shifted_code = shifted_code * phase_correction

                doppler_phase = np.exp(1j * 2 * np.pi * fd * t_pulse[n])
                baseband[0, n, :] += amplitude * shifted_code * doppler_phase

        # 添加噪声
        baseband = add_awgn(baseband, snr_db, rng=rng)

        return SimResult(
            name="pmcw",
            baseband=baseband,
            fc=self.fc,
            bandwidth=self.bandwidth,
            fs=self.chip_rate,
            prf=self.prf,
            num_chirps=P,
            samples_per_chirp=N,
            c=self.c,
            target_info={
                "targets": targets,
                "snr_db": snr_db,
                "code_type": "pmcw",
                "code_length": N,
                "code": code.tolist(),
            }
        )


def create_automotive_pmcw_simulator(**kwargs) -> PmcwSimulator:
    """
    创建典型汽车雷达 PMCW 仿真器

    默认参数（对标 real-world 77 GHz PMCW 车载雷达）：
    - 码片速率 250 Mchip/s → ΔR = 0.6 m
    - m 序列 1023 chips → R_max = 614 m
    - PRI = 50 μs → PRF = 20 kHz → v_max = ±19.5 m/s (±70 km/h)
    """
    defaults = {
        'fc': 77e9,
        'chip_rate': 250e6,
        'code_type': 'mseq',
        'code_length': 1023,
        'pri': 50e-6,
        'num_pulses': 256,
    }
    defaults.update(kwargs)
    return PmcwSimulator(**defaults)


if __name__ == "__main__":
    print("=" * 60)
    print("PMCW 雷达仿真器测试")
    print("=" * 60)

    sim = create_automotive_pmcw_simulator()
    c = sim.c
    print(f"  载波频率: {sim.fc/1e9:.0f} GHz")
    print(f"  码片速率: {sim.chip_rate/1e6:.0f} Mchip/s")
    print(f"  码型: m-sequence, 码长 {sim.code_length}")
    print(f"  码持续时间: {sim.code_duration*1e6:.2f} μs")
    print(f"  保护间隔: {sim.guard_interval*1e6:.2f} μs")
    print(f"  PRI: {sim.pri*1e6:.1f} μs")
    print(f"  PRF: {sim.prf/1e3:.1f} kHz")
    print(f"  带宽: {sim.bandwidth/1e6:.0f} MHz")
    print(f"  距离分辨率: {c/(2*sim.bandwidth):.2f} m")
    print(f"  最大不模糊距离: {sim.code_length * c/(2*sim.bandwidth):.1f} m")
    print(f"  最大不模糊速度: ±{c*sim.prf/(4*sim.fc):.2f} m/s")
    print(f"  脉冲数: {sim.num_pulses}")

    targets = [
        {"range": 40.0, "velocity": 1.5, "rcs": 10},
        {"range": 150.0, "velocity": -3.0, "rcs": 5},
    ]
    result = sim.simulate(targets, snr_db=25.0, seed=42)
    print(f"\n  基带数据形状: {result.baseband.shape}")
    print(f"  测试完成 ✓")
