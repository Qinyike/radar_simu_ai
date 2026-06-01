"""
示例 1: 基础使用 - 最简单的雷达仿真

这个示例展示如何快速运行一个基本的 LFMCW 雷达仿真。
适合初学者了解框架的基本用法。
"""

import sys
import os
# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from main import run_simulation

print("=" * 70)
print("示例 1: 基础 LFMCW 雷达仿真")
print("=" * 70)

# 定义目标场景
targets = [
    {"range": 50.0, "velocity": 3.0, "rcs": 15},   # 50米处的目标，速度 3 m/s
]

# 运行仿真
print("\n正在运行仿真...")
sim_result, processed_result = run_simulation(
    waveform_type="lfmcw",
    targets=targets,
    snr_db=25.0,      # 信噪比 25 dB
    seed=42,          # 随机种子（保证可重复性）
    visualize=True,   # 显示图表
    save_plots=True,  # 保存图片
    output_dir="./output/example1"
)

print("\n✓ 仿真完成！")
print(f"  - 检测到 {len(processed_result.range_axis)} 个距离 bin")
print(f"  - 检测到 {len(processed_result.doppler_axis)} 个多普勒 bin")
print(f"  - 图表已保存到 ./output/example1/")
