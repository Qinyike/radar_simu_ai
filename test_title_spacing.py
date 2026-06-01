"""
测试标题间距优化
"""

import sys
import os
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from simulators import LfmcwSimulator
from processors import process_lfmcw
from visualizers.rd_visualizer import plot_comprehensive

print("=" * 70)
print("测试：标题间距优化")
print("=" * 70)

# 创建仿真器
simulator = LfmcwSimulator(
    fc=77e9,
    bandwidth=150e6,
    chirp_duration=50e-6,
    fs=10e6,
    prf=5e3,
    num_chirps=128
)

# 定义多目标场景
targets = [
    {"range": 50.0, "velocity": 20.0, "rcs": 15},   # 会模糊
    {"range": 100.0, "velocity": -10.0, "rcs": 10}, # 会模糊
    {"range": 150.0, "velocity": 0.0, "rcs": 8},    # 不模糊
]

print(f"\n目标配置:")
for i, t in enumerate(targets, 1):
    print(f"  T{i}: R={t['range']}m, V={t['velocity']}m/s")

# 运行仿真
print("\n正在运行仿真...")
sim_result = simulator.simulate(targets, snr_db=25.0, seed=42)
processed = process_lfmcw(sim_result)
print("✓ 仿真完成")

# 生成可视化
print("\n生成优化后的可视化图表...")
target_info = {'targets': targets}

plot_comprehensive(
    processed,
    target_info=target_info,
    title="LFMCW Automotive Radar Simulation\n(Optimized Title Spacing)",
    save_path="./output/test_title_spacing.png",
    show=False
)

print("✓ 图表已保存到 ./output/test_title_spacing.png")
print("\n改进内容:")
print("  1. ✓ RD 谱图标题顶部留白增加 (pad=20)")
print("  2. ✓ 总标题位置调整 (y=0.97)")
print("  3. ✓ 布局参数优化 (top=0.92)")
print("  4. ✓ 标题之间不再重叠")
print("\n请查看生成的图片验证效果！")
