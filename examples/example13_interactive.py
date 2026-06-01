"""
示例 13: 交互式可视化

演示交互式距离-多普勒谱：
- 鼠标悬停：左上角实时显示 (距离, 速度, 功率)
- 鼠标点击：选中点白色十字高亮 + 详情气泡
- ESC 键：清除选中
- 工具栏：缩放 / 平移 / 重置 / 保存图片
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from simulators import get_simulator
from processors import get_processor
from visualizers.interactive import plot_rd_interactive

print("=" * 70)
print("示例 13: 交互式距离-多普勒谱")
print("=" * 70)

# 仿真
sim = get_simulator("lfmcw")
targets = [
    {"range": 40.0, "velocity": 1.5, "rcs": 10},
    {"range": 100.0, "velocity": -3.0, "rcs": 7},
    {"range": 180.0, "velocity": 0.5, "rcs": 4},
]
sim_result = sim.simulate(targets=targets, snr_db=25.0, seed=42)
processed = get_processor("lfmcw")(sim_result)

target_info = {
    'targets': [{"range": t['range'], "velocity": t['velocity'], "rcs": t['rcs']}
                for t in targets]
}

print("\n操作说明:")
print("  - 鼠标移动：左上角显示坐标 (Range, Velocity, Power)")
print("  - 鼠标点击：选中点高亮 + 详情气泡")
print("  - ESC 键：清除选中")
print("  - 工具栏：缩放/平移/重置/保存")
print("\n打开交互窗口...\n")

plot_rd_interactive(
    processed,
    target_info=target_info,
    title="Interactive LFMCW Range-Doppler Spectrum\n(Click to inspect, ESC to clear)",
    save_path="./output/example13_interactive.png",
    show=True
)
