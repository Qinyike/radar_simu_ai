"""
快速测试 MIMO 功能修复
"""

import sys
import os
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import numpy as np
from contracts import MimoAntennaArray
from simulators.mimo_simulator import MimoLfmcwSimulator
from processors.mimo_processor import process_mimo

print("=" * 70)
print("MIMO 功能快速测试")
print("=" * 70)

# 测试 1: 创建天线阵列
print("\n[测试 1] 创建 4T4R 天线阵列...")
try:
    antenna_array = MimoAntennaArray(num_tx=4, num_rx=4, fc=77e9)
    print(f"  ✓ 成功")
    print(f"    - 虚拟阵列大小: {antenna_array.virtual_array_size}")
    print(f"    - 有效孔径: {antenna_array.effective_aperture:.4f} m")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    sys.exit(1)

# 测试 2: 创建 MIMO 仿真器
print("\n[测试 2] 创建 MIMO 仿真器（TDMA）...")
try:
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
    print(f"  ✓ 成功")
    print(f"    - 波形模式: {mimo_sim.waveform_mode}")
    print(f"    - 最大不模糊速度: ±{mimo_sim.max_unambiguous_velocity:.2f} m/s")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    sys.exit(1)

# 测试 3: 运行仿真
print("\n[测试 3] 运行 MIMO 仿真...")
targets = [
    {"range": 50.0, "velocity": 3.0, "angle": np.radians(10), "rcs": 15},
    {"range": 100.0, "velocity": -2.0, "angle": np.radians(-15), "rcs": 10},
]

try:
    sim_result = mimo_sim.simulate(targets, snr_db=25.0, seed=42)
    print(f"  ✓ 成功")
    print(f"    - SimResult.name: {sim_result.name}")
    print(f"    - baseband shape: {sim_result.baseband.shape}")
    print(f"    - fc: {sim_result.fc/1e9:.1f} GHz")
    print(f"    - fs: {sim_result.fs/1e6:.1f} MHz")
    print(f"    - prf: {sim_result.prf/1e3:.1f} kHz")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 4: 处理数据
print("\n[测试 4] 处理 MIMO 数据...")
try:
    processed = process_mimo(sim_result)
    print(f"  ✓ 成功")
    print(f"    - RD 谱形状: {processed.range_doppler.shape}")
    print(f"    - 距离轴范围: [{processed.range_axis[0]:.1f}, {processed.range_axis[-1]:.1f}] m")
    print(f"    - 多普勒轴范围: [{processed.doppler_axis[0]:.2f}, {processed.doppler_axis[-1]:.2f}] m/s")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ 所有测试通过！")
print("=" * 70)
