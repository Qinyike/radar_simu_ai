"""
噪声工具函数
"""

import numpy as np


def add_awgn(signal: np.ndarray, snr_db: float, rng: np.random.Generator = None) -> np.ndarray:
    """
    给信号添加高斯白噪声 (AWGN)

    Args:
        signal: 输入信号（复数 ndarray）
        snr_db: 信噪比 (dB)
        rng: numpy 随机数生成器（None 则使用默认）

    Returns:
        添加噪声后的信号
    """
    if rng is None:
        rng = np.random.default_rng()

    signal_power = np.mean(np.abs(signal) ** 2)
    if signal_power < 1e-30:
        signal_power = 1.0

    noise_power = signal_power / (10 ** (snr_db / 10.0))
    noise = np.sqrt(noise_power / 2) * (
        rng.standard_normal(signal.shape) +
        1j * rng.standard_normal(signal.shape)
    )
    return signal + noise
