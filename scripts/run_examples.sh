#!/bin/bash
# ========================================
# 雷达仿真框架 - 示例运行脚本 (Linux/Mac)
# ========================================

echo ""
echo "========================================"
echo "  汽车雷达 LFMCW 仿真框架 - 示例集"
echo "========================================"
echo ""

run_example() {
    local num=$1
    local name=$2
    echo ""
    echo "正在运行示例${num}: ${name}..."
    echo "================================"
    pixi run python examples/example${num}_*.py
    echo ""
    read -p "按回车键继续..."
}

while true; do
    echo "请选择要运行的示例:"
    echo ""
    echo "[1] 示例1: 基础使用 (最简单)"
    echo "[2] 示例2: 多目标场景"
    echo "[3] 示例3: 参数调优"
    echo "[4] 示例4: 信噪比分析"
    echo "[5] 示例5: 自定义可视化"
    echo "[6] 示例6: 批量仿真"
    echo "[A] 运行所有示例"
    echo "[Q] 退出"
    echo ""
    read -p "请输入选择 (1-6, A, Q): " choice
    
    case $choice in
        1) run_example 1 "基础使用" ;;
        2) run_example 2 "多目标场景" ;;
        3) run_example 3 "参数调优" ;;
        4) run_example 4 "信噪比分析" ;;
        5) run_example 5 "自定义可视化" ;;
        6) run_example 6 "批量仿真" ;;
        [aA]) 
            for i in 1 2 3 4 5 6; do
                run_example $i "示例$i"
            done
            echo "所有示例运行完成！"
            ;;
        [qQ]) 
            echo ""
            echo "感谢使用！再见！"
            exit 0
            ;;
        *) echo "无效选择，请重试" ;;
    esac
done
