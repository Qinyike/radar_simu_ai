"""
单元测试 - 验证架构契约和模块接口

本模块包含：
1. 契约测试：验证数据结构完整性
2. 模块接口测试：验证各模块输入输出符合契约
3. 物理验证测试：验证仿真结果的物理正确性
"""

import sys
import os
import numpy as np

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contracts import SimResult, ProcessedResult
from simulators import get_simulator
from processors import get_processor


def test_sim_result_contract():
    """测试 SimResult 契约"""
    print("测试 1: SimResult 契约验证...")
    
    # 创建有效的 SimResult
    baseband = np.random.randn(1, 128, 256) + 1j * np.random.randn(1, 128, 256)
    
    sim_result = SimResult(
        name="test",
        baseband=baseband,
        fc=77e9,
        bandwidth=150e6,
        fs=10e6,
        prf=5e3,
        num_chirps=128,
        samples_per_chirp=256
    )
    
    # 验证字段存在
    assert hasattr(sim_result, 'name')
    assert hasattr(sim_result, 'baseband')
    assert hasattr(sim_result, 'fc')
    assert hasattr(sim_result, 'bandwidth')
    assert hasattr(sim_result, 'fs')
    assert hasattr(sim_result, 'prf')
    assert hasattr(sim_result, 'num_chirps')
    assert hasattr(sim_result, 'samples_per_chirp')
    
    # 验证数据类型
    assert isinstance(sim_result.baseband, np.ndarray)
    assert sim_result.baseband.dtype == np.complex128
    
    # 验证形状
    assert sim_result.baseband.shape == (1, 128, 256)
    
    print("  ✓ SimResult 契约测试通过")


def test_processed_result_contract():
    """测试 ProcessedResult 契约"""
    print("测试 2: ProcessedResult 契约验证...")
    
    # 创建有效的 ProcessedResult
    processed_result = ProcessedResult(
        name="test_processed",
        range_profile=np.random.randn(128),
        range_doppler=np.random.randn(128, 128),
        range_axis=np.linspace(0, 200, 128),
        doppler_axis=np.linspace(-50, 50, 128)
    )
    
    # 验证字段存在
    assert hasattr(processed_result, 'name')
    assert hasattr(processed_result, 'range_profile')
    assert hasattr(processed_result, 'range_doppler')
    assert hasattr(processed_result, 'range_axis')
    assert hasattr(processed_result, 'doppler_axis')
    
    # 验证维度一致性
    assert processed_result.range_doppler.shape[0] == len(processed_result.range_axis)
    assert processed_result.range_doppler.shape[1] == len(processed_result.doppler_axis)
    
    print("  ✓ ProcessedResult 契约测试通过")


def test_lfmcw_simulator_interface():
    """测试 LFMCW 仿真器接口"""
    print("测试 3: LFMCW 仿真器接口测试...")
    
    # 获取仿真器
    simulator = get_simulator("lfmcw")
    
    # 定义目标场景
    targets = [
        {"range": 50.0, "velocity": 20.0, "rcs": 10},
        {"range": 100.0, "velocity": -10.0, "rcs": 5},
    ]
    
    # 执行仿真
    sim_result = simulator.simulate(targets=targets, snr_db=20.0, seed=42)
    
    # 验证返回类型
    assert isinstance(sim_result, SimResult)
    
    # 验证波形标识
    assert sim_result.name == "lfmcw"
    
    # 验证数据形状
    assert sim_result.baseband.shape[0] == 1
    assert sim_result.baseband.shape[1] == simulator.num_chirps
    assert sim_result.baseband.shape[2] == simulator.samples_per_chirp
    
    print("  ✓ LFMCW 仿真器接口测试通过")


def test_lfmcw_processor_interface():
    """测试 LFMCW 处理器接口"""
    print("测试 4: LFMCW 处理器接口测试...")
    
    # 先仿真
    simulator = get_simulator("lfmcw")
    targets = [{"range": 50.0, "velocity": 20.0, "rcs": 10}]
    sim_result = simulator.simulate(targets=targets, snr_db=20.0, seed=42)
    
    # 获取处理器
    processor = get_processor("lfmcw")
    
    # 执行处理
    processed_result = processor(sim_result)
    
    # 验证返回类型
    assert isinstance(processed_result, ProcessedResult)
    
    # 验证数据完整性
    assert len(processed_result.range_profile) > 0
    assert processed_result.range_doppler.ndim == 2
    assert len(processed_result.range_axis) > 0
    assert len(processed_result.doppler_axis) > 0
    
    print("  ✓ LFMCW 处理器接口测试通过")


def test_physical_validation():
    """物理验证测试：验证检测结果与真实目标一致"""
    print("测试 5: 物理验证测试...")
    
    # 配置已知目标（速度要在不模糊范围内）
    # 最大不模糊速度: v_max = c * PRF / (4 * fc) = 3e8 * 5e3 / (4 * 77e9) ≈ 4.87 m/s
    true_targets = [
        {"range": 50.0, "velocity": 3.0, "rcs": 15},  # 强目标，低速
        {"range": 100.0, "velocity": -2.0, "rcs": 5},
    ]
    
    # 仿真
    simulator = get_simulator("lfmcw")
    sim_result = simulator.simulate(targets=true_targets, snr_db=30.0, seed=42)
    
    # 处理
    processor = get_processor("lfmcw")
    processed_result = processor(sim_result)
    
    # 找到最强目标
    rd_spectrum = processed_result.range_doppler
    range_axis = processed_result.range_axis
    doppler_axis = processed_result.doppler_axis
    
    max_idx = np.unravel_index(np.argmax(rd_spectrum), rd_spectrum.shape)
    detected_range = range_axis[max_idx[0]]  # 第一维是 range
    detected_velocity = doppler_axis[max_idx[1]]  # 第二维是 doppler
    
    # 验证检测精度
    range_error = abs(detected_range - true_targets[0]['range'])
    velocity_error = abs(detected_velocity - true_targets[0]['velocity'])
    
    # 计算分辨率 (用于打印和验证)
    range_resolution = range_axis[1] - range_axis[0]
    velocity_resolution = doppler_axis[1] - doppler_axis[0]

    print(f"  真实目标: R={true_targets[0]['range']}m, V={true_targets[0]['velocity']}m/s")
    print(f"  检测结果: R={detected_range:.2f}m, V={detected_velocity:.2f}m/s")
    print(f"  距离误差: {range_error:.2f}m, 速度误差: {velocity_error:.2f}m/s")
    print(f"  距离分辨率: {range_resolution:.2f}m, 速度分辨率: {velocity_resolution:.2f}m/s")
    print(f"  检测索引: range_idx={max_idx[1]}, doppler_idx={max_idx[0]}")
    print(f"  RD谱最大值位置: {max_idx}, 值={rd_spectrum[max_idx]:.2f}")
    
    # 允许一定误差（取决于分辨率）
    assert range_error < 2 * range_resolution, f"距离误差过大: {range_error:.2f}m"
    assert velocity_error < 2 * velocity_resolution, f"速度误差过大: {velocity_error:.2f}m/s"
    
    print("  ✓ 物理验证测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("运行雷达仿真框架测试套件")
    print("=" * 70)
    print()
    
    try:
        test_sim_result_contract()
        test_processed_result_contract()
        test_lfmcw_simulator_interface()
        test_lfmcw_processor_interface()
        test_physical_validation()
        
        print("\n" + "=" * 70)
        print("✓ 所有测试通过！")
        print("=" * 70)
        return True
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
