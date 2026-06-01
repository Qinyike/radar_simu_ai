"""
示例 6: 批量仿真 - 自动化测试多个场景

这个示例展示如何批量运行多个仿真场景，用于系统验证或参数扫描。
适合工程开发和性能评估。
"""

import sys
import os
# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from simulators import LfmcwSimulator
from processors import process_lfmcw
import numpy as np
import json
from datetime import datetime

print("=" * 70)
print("示例 6: 批量仿真实验")
print("=" * 70)

# 定义多个测试场景
test_scenarios = [
    {
        "name": "高速接近",
        "targets": [{"range": 50.0, "velocity": -20.0, "rcs": 15}],
        "snr_db": 30
    },
    {
        "name": "多目标城市道路",
        "targets": [
            {"range": 30.0, "velocity": 5.0, "rcs": 18},
            {"range": 60.0, "velocity": -3.0, "rcs": 12},
            {"range": 90.0, "velocity": 0.0, "rcs": 10},
        ],
        "snr_db": 25
    },
    {
        "name": "远距离弱目标",
        "targets": [{"range": 200.0, "velocity": 4.0, "rcs": 5}],
        "snr_db": 15
    },
    {
        "name": "密集交通",
        "targets": [
            {"range": 25.0, "velocity": 8.0, "rcs": 20},
            {"range": 35.0, "velocity": 6.0, "rcs": 18},
            {"range": 45.0, "velocity": 4.0, "rcs": 16},
            {"range": 55.0, "velocity": 2.0, "rcs": 14},
        ],
        "snr_db": 28
    },
]

print(f"\n准备运行 {len(test_scenarios)} 个测试场景...\n")

# 创建仿真器（固定参数）
simulator = LfmcwSimulator(
    fc=77e9,
    bandwidth=150e6,
    chirp_duration=50e-6,
    fs=10e6,
    prf=5e3,
    num_chirps=128
)

# 批量运行
results_summary = []
start_time = datetime.now()

for i, scenario in enumerate(test_scenarios, 1):
    print(f"[{i}/{len(test_scenarios)}] 运行场景: {scenario['name']}")
    
    try:
        # 仿真
        sim_result = simulator.simulate(
            scenario['targets'], 
            snr_db=scenario['snr_db'], 
            seed=i*100  # 不同种子
        )
        
        # 处理
        processed = process_lfmcw(sim_result)
        
        # 分析检测结果
        rd_spectrum = processed.range_doppler
        range_axis = processed.range_axis
        doppler_axis = processed.doppler_axis
        
        # 找到最强目标
        max_idx = np.unravel_index(np.argmax(rd_spectrum), rd_spectrum.shape)
        detected_range = range_axis[max_idx[0]]
        detected_velocity = doppler_axis[max_idx[1]]
        detected_power = 20 * np.log10(rd_spectrum[max_idx] + 1e-10)
        
        # 计算与第一个真实目标的误差
        true_target = scenario['targets'][0]
        range_error = abs(detected_range - true_target['range'])
        velocity_error = abs(detected_velocity - true_target['velocity'])
        
        result = {
            'scenario': scenario['name'],
            'num_targets': len(scenario['targets']),
            'snr_db': scenario['snr_db'],
            'detected_range': float(detected_range),
            'detected_velocity': float(detected_velocity),
            'detected_power_db': float(detected_power),
            'range_error': float(range_error),
            'velocity_error': float(velocity_error),
            'status': 'PASS' if range_error < 2.0 else 'FAIL'
        }
        
        results_summary.append(result)
        
        print(f"      ✓ 完成 | 检测: R={detected_range:.1f}m, V={detected_velocity:.2f}m/s")
        print(f"      误差: ΔR={range_error:.2f}m, ΔV={velocity_error:.2f}m/s")
        
    except Exception as e:
        print(f"      ✗ 失败: {str(e)}")
        results_summary.append({
            'scenario': scenario['name'],
            'status': 'ERROR',
            'error': str(e)
        })

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

# 生成总结报告
print("\n" + "=" * 70)
print("批量仿真总结报告")
print("=" * 70)
print(f"执行时间: {duration:.2f} 秒")
print(f"总场景数: {len(test_scenarios)}")
print(f"成功: {sum(1 for r in results_summary if r['status'] == 'PASS')}")
print(f"失败: {sum(1 for r in results_summary if r['status'] == 'FAIL')}")
print(f"错误: {sum(1 for r in results_summary if r['status'] == 'ERROR')}")

print("\n详细结果:")
print("-" * 70)
for result in results_summary:
    status_symbol = "✓" if result['status'] == 'PASS' else ("✗" if result['status'] == 'FAIL' else "⚠")
    print(f"{status_symbol} {result['scenario']:20s} | "
          f"状态: {result['status']:5s} | "
          f"ΔR: {result.get('range_error', 'N/A'):>6}m | "
          f"ΔV: {result.get('velocity_error', 'N/A'):>6}m/s")

# 保存结果为 JSON
output_data = {
    'timestamp': datetime.now().isoformat(),
    'duration_seconds': duration,
    'total_scenarios': len(test_scenarios),
    'results': results_summary
}

os.makedirs('./output', exist_ok=True)
with open('./output/example6_batch_results.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"\n✓ 结果已保存到 ./output/example6_batch_results.json")
print("\n✓ 批量仿真完成！")
