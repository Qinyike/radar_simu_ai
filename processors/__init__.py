"""
信号处理/算法层 - 模块初始化
"""

from processors.lfmcw_processor import (
    process_lfmcw,
    range_fft,
    doppler_fft
)
from processors.mimo_processor import (
    process_mimo,
    process_mimo_tdma,
    process_mimo_ddma,
    mimo_dbf_angle_estimation
)
from processors.pmcw_processor import process_pmcw
from processors.window_utils import get_window

# 处理器注册表
PROCESSOR_REGISTRY = {
    "lfmcw": process_lfmcw,
    "pmcw": process_pmcw,
    "mimo": process_mimo,
    "mimo_tdma": process_mimo_tdma,
    "mimo_ddma": process_mimo_ddma,
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
