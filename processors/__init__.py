"""
信号处理/算法层 - 模块初始化
"""

from processors.lfmcw_processor import (
    process_lfmcw,
    range_fft,
    doppler_fft,
    compute_range_axis,
    compute_doppler_axis
)
from processors.mimo_processor import (
    process_mimo,
    process_mimo_tdma,
    process_mimo_ddma,
    mimo_dbf_angle_estimation
)
from processors.window_utils import get_window

# 处理器注册表
PROCESSOR_REGISTRY = {
    "lfmcw": process_lfmcw,
    "mimo": process_mimo,
    "mimo_tdma": process_mimo_tdma,
    "mimo_ddma": process_mimo_ddma,
    # 未来可以添加更多处理器：
    # "fmcw": process_fmcw,
}


def get_processor(name: str):
    """
    根据名称获取处理器函数
    
    Args:
        name: 处理器名称（如 "lfmcw", "mimo"）
        
    Returns:
        处理器函数
        
    Raises:
        ValueError: 如果处理器名称未注册
    """
    if name not in PROCESSOR_REGISTRY:
        available = ", ".join(PROCESSOR_REGISTRY.keys())
        raise ValueError(
            f"未知的处理器类型: '{name}'。可用的处理器: {available}"
        )
    
    return PROCESSOR_REGISTRY[name]
