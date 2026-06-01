"""
波形生成/仿真层 - 模块初始化

注册所有可用的仿真器模块
"""

from simulators.lfmcw_simulator import LfmcwSimulator, create_automotive_lfmcw_simulator
from simulators.mimo_simulator import (
    MimoLfmcwSimulator,
    dbf_angle_estimation
)
from simulators.pmcw_simulator import PmcwSimulator, create_automotive_pmcw_simulator
from contracts import MimoAntennaArray

# 仿真器注册表
SIMULATOR_REGISTRY = {
    "lfmcw": create_automotive_lfmcw_simulator,
    "pmcw": create_automotive_pmcw_simulator,
    "mimo_tdma": lambda **kwargs: MimoLfmcwSimulator(waveform_mode='tdma', **kwargs),
    "mimo_ddma": lambda **kwargs: MimoLfmcwSimulator(waveform_mode='ddma', **kwargs),
}


def get_simulator(name: str, **kwargs):
    """
    根据名称获取仿真器实例
    
    Args:
        name: 仿真器名称（如 "lfmcw", "mimo_tdma", "mimo_ddma"）
        **kwargs: 传递给仿真器构造函数的参数
        
    Returns:
        仿真器实例
        
    Raises:
        ValueError: 如果仿真器名称未注册
    """
    if name not in SIMULATOR_REGISTRY:
        available = ", ".join(SIMULATOR_REGISTRY.keys())
        raise ValueError(
            f"未知的仿真器类型: '{name}'。可用的仿真器: {available}"
        )
    
    factory_func = SIMULATOR_REGISTRY[name]
    return factory_func(**kwargs)
