"""
波形生成/仿真层 - PMCW 雷达仿真模块

PMCW (Phase Modulated Continuous Wave) 使用相位编码序列调制连续波：
- TX 发射相位编码信号（Barker 码、m 序列等）
- RX 通过匹配滤波（相关运算）实现距离压缩
- 多个码重复周期做 Doppler FFT 得到距离-多普勒谱

与 LFMCW 的区别：
- LFMCW: 调频连续波，差频→距离 FFT
- PMCW: 相位编码连续波，相关→距离压缩

距离分辨率: ΔR = c / (2 * B)，B ≈ 1/Tc（码片带宽）
最大不模糊距离: R_max = N * ΔR（N 为码长）
"""

import sys
import os

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional
import numpy as np
from contracts import SimResult


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
    反馈多项式采用常见的本原多项式。
    """
    length = 2 ** n_bits - 1

    # 常见本原多项式（octal 表示）
    primitive_polys = {
        2: 0o7,     # x^2 + x + 1
        3: 0o13,    # x^3 + x + 1
        4: 0o23,    # x^4 + x + 1
        5: 0o45,    # x^5 + x^2 + 1
        6: 0o103,   # x^6 + x + 1
        7: 0o211,   # x^7 + x^3 + 1
        8: 0o435,   # x^8 + x^4 + x^3 + x^2 + 1
        9: 0o1021,  # x^9 + x^4 + 1
        10: 0o2011, # x^10 + x^3 + 1
    }

    if n_bits not in primitive_polys:
        raise ValueError(f"m 序列不支持 n_bits={n_bits}，可选: {list(primitive_polys.keys())}")

    poly = primitive_polys[n_bits]

    # 提取抽头位置（从多项式中）
    taps = []
    for i in range(n_bits + 1):
        if (poly >> i) & 1:
            taps.append(i)

    # LFSR 寄存器（初始状态不能全 0）
    register = [1] * n_bits
    output = []

    for _ in range(length):
        output.append(register[-1])
        feedback = 0
        for t in taps:
            if t > 0:
                feedback ^= register[t - 1]
        register = [feedback] + register[:-1]

    # 转换为 +1/-1
    return np.array([2 * b - 1 for b in output], dtype=np.float64)


def generate_pmcw_code(code_type: str, code_length: int) -> np.ndarray:
    """
    生成 PMCW 相位编码序列

    Args:
        code_type: 码类型，'barker' 或 'mseq'
        code_length: 码长。barker: 2/3/4/5/7/11/13；mseq: 自动取 2^n-1

    Returns:
        code: BPSK 相位编码 [+1, -1, ...]
    """
    code_type = code_type.lower()
    if code_type == 'barker':
        return generate_barker_code(code_length)
    elif code_type in ('mseq', 'm-sequence', 'm_sequence'):
        # 找到满足 2^n - 1 >= code_length 的最小 n
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

    生成 PMCW 波形的基带回波数据。

    信号模型：
    - 每个脉冲由 N 个码片组成（BPSK 编码）
    - 脉冲重复间隔 PRI = N * Tc
    - 采样率 = 码片速率 = 1/Tc
    - 每个脉冲采样 N 个点（每码片 1 个采样）

    Attributes:
        fc: 载波频率 (Hz)
        chip_rate: 码片速率 (Hz)，决定带宽 B ≈ chip_rate
        code: 相位编码序列
        num_pulses: 脉冲数量（码重复次数）
        c: 光速 (m/s)
    """

    def __init__(
        self,
        fc: float = 77e9,
        chip_rate: float = 50e6,       # 50 Mchip/s → ΔR = 3 m
        code_type: str = 'mseq',
        code_length: int = 127,        # m-sequence: 127 chips → R_max = 381 m
        num_pulses: int = 128,         # 128 个脉冲
        c: float = 3e8
    ):
        self.fc = fc
        self.chip_rate = chip_rate
        self.code = generate_pmcw_code(code_type, code_length)
        self.code_length = len(self.code)
        self.num_pulses = num_pulses
        self.c = c

        # 派生参数
        self.chip_duration = 1.0 / chip_rate
        self.pri = self.code_length * self.chip_duration   # 脉冲重复间隔
        self.prf = 1.0 / self.pri                          # 脉冲重复频率
        self.bandwidth = chip_rate                          # 等效带宽
        self.samples_per_chirp = self.code_length           # 每脉冲采样数（兼容契约）

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
            np.random.seed(seed)

        N = self.code_length
        P = self.num_pulses
        code = self.code

        # 基带信号 [1, num_pulses, code_length]
        # 每个采样点对应一个码片
        baseband = np.zeros((1, P, N), dtype=np.complex128)

        t_chip = np.arange(N) * self.chip_duration  # 快时间（脉冲内）
        t_pulse = np.arange(P) * self.pri            # 慢时间（脉冲间）

        for target in targets:
            R = target['range']
            v = target['velocity']
            rcs = target.get('rcs', 0)

            amplitude = 10 ** (rcs / 20.0)

            # 时延（码片数，支持分数延迟通过相位插值）
            tau = 2 * R / self.c
            delay_chips = tau / self.chip_duration

            # 多普勒频率
            fd = 2 * v * self.fc / self.c

            for n in range(P):
                # 当前脉冲时刻目标距离
                R_n = R + v * t_pulse[n]
                tau_n = 2 * R_n / self.c
                delay_n = tau_n / self.chip_duration

                # 接收信号 = 发射码循环移位 delay_n 个码片
                # 使用 np.roll 进行整数移位（分数部分通过相位补偿）
                int_delay = int(np.floor(delay_n))
                frac_delay = delay_n - int_delay

                # 循环移位码
                shifted_code = np.roll(code, int_delay)

                # 分数延迟的相位补偿（线性相位近似）
                if abs(frac_delay) > 1e-10:
                    phase_correction = np.exp(-1j * 2 * np.pi * frac_delay *
                                              np.arange(N) / N)
                    shifted_code = shifted_code * phase_correction

                # 多普勒相位
                doppler_phase = np.exp(1j * 2 * np.pi * fd * t_pulse[n])

                # 回波信号
                baseband[0, n, :] += amplitude * shifted_code * doppler_phase

        # 添加噪声
        signal_power = np.mean(np.abs(baseband) ** 2)
        if signal_power < 1e-30:
            signal_power = 1.0
        noise_power = signal_power / (10 ** (snr_db / 10.0))
        noise = np.sqrt(noise_power / 2) * (
            np.random.randn(*baseband.shape) +
            1j * np.random.randn(*baseband.shape)
        )
        baseband += noise

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
    """创建典型汽车雷达参数的 PMCW 仿真器"""
    defaults = {
        'fc': 77e9,
        'chip_rate': 50e6,
        'code_type': 'mseq',
        'code_length': 127,
        'num_pulses': 128,
    }
    defaults.update(kwargs)
    return PmcwSimulator(**defaults)


if __name__ == "__main__":
    print("=" * 60)
    print("PMCW 雷达仿真器测试")
    print("=" * 60)

    sim = PmcwSimulator(
        fc=77e9, chip_rate=50e6,
        code_type='barker', code_length=13,
        num_pulses=64
    )
    print(f"  码长: {sim.code_length}")
    print(f"  码片速率: {sim.chip_rate/1e6:.0f} Mchip/s")
    print(f"  带宽: {sim.bandwidth/1e6:.0f} MHz")
    print(f"  距离分辨率: {sim.c/(2*sim.bandwidth):.2f} m")
    print(f"  最大不模糊距离: {sim.code_length * sim.c/(2*sim.bandwidth):.1f} m")
    print(f"  PRF: {sim.prf:.0f} Hz")
    print(f"  最大不模糊速度: ±{sim.c*sim.prf/(4*sim.fc):.2f} m/s")

    targets = [
        {"range": 30.0, "velocity": 2.0, "rcs": 10},
        {"range": 80.0, "velocity": -1.5, "rcs": 5},
    ]
    result = sim.simulate(targets, snr_db=25.0, seed=42)
    print(f"\n  仿真结果: {result.name}")
    print(f"  基带数据形状: {result.baseband.shape}")
    print(f"  测试完成 ✓")
