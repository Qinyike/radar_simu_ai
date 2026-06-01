"""
文件结构重构脚本

将文档移动到 docs/ 目录
将测试和工具脚本移动到 scripts/ 目录
"""

import os
import shutil
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent

# 定义需要移动的文档
docs_to_move = [
    'README.md',
    'QUICKSTART.md',
    'TUTORIAL.md',
    'MIMO_GUIDE.md',
    'VISUALIZATION_IMPROVEMENTS.md',
    'VISUALIZATION_OPTIMIZATION.md',
    'TITLE_SPACING_OPTIMIZATION.md',
    'BUGFIX_SUMMARY.md',
    'EXAMPLES_SUMMARY.md',
    'PROJECT_SUMMARY.md',
    'QUICK_REFERENCE.md'
]

# 定义需要移动的脚本
scripts_to_move = [
    'test_mimo_quick.py',
    'test_multi_target_annotation.py',
    'test_title_spacing.py',
    'simple_test.py',
    'debug_signal_model.py',
    'run_examples.bat',
    'run_examples.sh',
    'test_fixes.py',
    'test_optimized_layout.py'
]

def create_directories():
    """创建必要的目录"""
    print("创建目录...")
    (project_root / 'docs').mkdir(exist_ok=True)
    (project_root / 'scripts').mkdir(exist_ok=True)
    print("✓ 目录创建完成")

def move_files(file_list, dest_dir):
    """移动文件列表到目标目录"""
    moved_count = 0
    for filename in file_list:
        src = project_root / filename
        if src.exists():
            dest = project_root / dest_dir / filename
            try:
                shutil.move(str(src), str(dest))
                print(f"  ✓ {filename} -> {dest_dir}/")
                moved_count += 1
            except Exception as e:
                print(f"  ✗ {filename}: {e}")
        else:
            print(f"  ⊘ {filename} (不存在)")
    
    return moved_count

def main():
    print("=" * 70)
    print("文件结构重构")
    print("=" * 70)
    
    # 创建目录
    create_directories()
    
    # 移动文档
    print("\n移动文档到 docs/...")
    docs_moved = move_files(docs_to_move, 'docs')
    print(f"  共移动 {docs_moved}/{len(docs_to_move)} 个文档")
    
    # 移动脚本
    print("\n移动脚本到 scripts/...")
    scripts_moved = move_files(scripts_to_move, 'scripts')
    print(f"  共移动 {scripts_moved}/{len(scripts_to_move)} 个脚本")
    
    # 总结
    print("\n" + "=" * 70)
    print("重构完成！")
    print("=" * 70)
    print(f"\n新的文件结构:")
    print(f"  radar_simu_ai/")
    print(f"    ├── docs/                    ({docs_moved} 个文档)")
    print(f"    ├── scripts/                 ({scripts_moved} 个脚本)")
    print(f"    ├── simulators/              (仿真器模块)")
    print(f"    ├── processors/              (处理器模块)")
    print(f"    ├── visualizers/             (可视化工具)")
    print(f"    ├── examples/                (示例代码)")
    print(f"    ├── tests/                   (单元测试)")
    print(f"    ├── contracts.py             (数据契约)")
    print(f"    ├── main.py                  (主程序)")
    print(f"    ├── base_rule.md             (基础规则)")
    print(f"    ├── pixi.toml                (Pixi 配置)")
    print(f"    └── output/                  (输出目录)")
    
    print(f"\n✓ 所有文件已整理完毕！")

if __name__ == '__main__':
    main()
