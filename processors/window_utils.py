"""
窗函数工具模块

提供统一的窗函数接口，支持多种窗函数类型，用于距离 FFT、多普勒 FFT 和 DBF 角度维加窗。

窗函数特性对比：
  名称         主瓣宽度   最高旁瓣   适用场景
  ─────────────────────────────────────────────────
  hamming      中等       -43 dB    通用，距离/多普勒
  hanning      较宽       -31 dB    通用
  blackman     宽         -58 dB    低旁瓣需求
  taylor       可调       -35 dB    雷达标准，旁瓣可控
  kaiser       可调       可调      灵活配置
  none         最窄       -13 dB    仅测试用
"""

import numpy as np


def _kaiser(N: int, beta: float) -> np.ndarray:
    """Kaiser 窗（惰性导入 scipy）"""
    try:
        from scipy.signal.windows import kaiser as _scipy_kaiser
    except ImportError:
        raise ImportError(
            "kaiser 窗需要 scipy 库。请安装: pip install scipy，"
            "或使用 'taylor' 窗作为替代。"
        )
    return _scipy_kaiser(N, beta=beta)


def _taylor(N: int, nbar: int = 4, sll: float = -35) -> np.ndarray:
    """
    Taylor 窗的手动实现（规避 scipy 版本 bug）

    Args:
        N: 窗长度
        nbar: 旁瓣数量（通常 4~6）
        sll: 最高旁瓣电平 (dB)，负值，如 -35

    Returns:
        Taylor 窗数组，长度 N
    """
    if N == 1:
        return np.ones(1)

    nbar = max(1, min(nbar, N // 2))

    B = 10.0 ** (abs(sll) / 20.0)
    A = np.arccosh(B) / np.pi

    sigma2 = nbar ** 2 / (A ** 2 + (nbar - 0.5) ** 2)

    m = np.arange(N)
    x = (m - (N - 1) / 2.0) * np.sqrt(sigma2) / (N / 2.0)

    w = np.ones(N, dtype=np.float64)
    for k in range(1, nbar):
        Fm = 0.0
        for s in range(1, nbar):
            num = 1.0 - (k ** 2) / (sigma2 * (A ** 2 + (s - 0.5) ** 2))
            den = 1.0 - (k ** 2) / (s ** 2)
            if abs(den) < 1e-12:
                continue
            Fm += num / den
        Fm *= (-1.0) ** (k + 1)
        w += Fm * np.cos(2.0 * np.pi * k * m / N)

    # 归一化到中心值为 1
    w /= w[N // 2] if N % 2 == 1 else max(w[N // 2 - 1], w[N // 2])
    w = np.clip(w, 0, None)

    return w


def get_window(name: str, N: int, **kwargs) -> np.ndarray:
    """
    生成指定类型的窗函数

    Args:
        name: 窗函数类型，支持 'hamming', 'hanning', 'blackman', 'taylor', 'kaiser', 'none'
        N: 窗长度（采样点数）
        **kwargs: 传递给具体窗函数的参数
            - taylor: nbar (旁瓣数量, 默认 4), sll (旁瓣电平 dB, 默认 -35)
            - kaiser: beta (形状参数, 默认 8.6)

    Returns:
        窗函数数组，长度 N
    """
    name = name.lower()

    if name == 'hamming':
        return np.hamming(N)
    elif name == 'hanning':
        return np.hanning(N)
    elif name == 'blackman':
        return np.blackman(N)
    elif name == 'taylor':
        nbar = kwargs.get('nbar', 4)
        sll = kwargs.get('sll', -35)
        return _taylor(N, nbar=nbar, sll=sll)
    elif name == 'kaiser':
        beta = kwargs.get('beta', 8.6)
        return _kaiser(N, beta=beta)
    elif name in ('none', 'rect', 'rectangular'):
        return np.ones(N)
    else:
        raise ValueError(f"不支持的窗函数类型: '{name}'。"
                         f"可选: hamming, hanning, blackman, taylor, kaiser, none")
