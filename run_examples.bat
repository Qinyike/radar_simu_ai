@echo off
REM ========================================
REM 雷达仿真框架 - 示例运行脚本 (Windows)
REM ========================================

echo.
echo ========================================
echo   汽车雷达 LFMCW 仿真框架 - 示例集
echo ========================================
echo.

:menu
echo 请选择要运行的示例:
echo.
echo [1] 示例1: 基础使用 (最简单)
echo [2] 示例2: 多目标场景
echo [3] 示例3: 参数调优
echo [4] 示例4: 信噪比分析
echo [5] 示例5: 自定义可视化
echo [6] 示例6: 批量仿真
echo [A] 运行所有示例
echo [Q] 退出
echo.
set /p choice=请输入选择 (1-6, A, Q): 

if /i "%choice%"=="1" goto example1
if /i "%choice%"=="2" goto example2
if /i "%choice%"=="3" goto example3
if /i "%choice%"=="4" goto example4
if /i "%choice%"=="5" goto example5
if /i "%choice%"=="6" goto example6
if /i "%choice%"=="A" goto all
if /i "%choice%"=="Q" goto end
goto menu

:example1
echo.
echo 正在运行示例1: 基础使用...
pixi run python examples/example1_basic.py
pause
goto menu

:example2
echo.
echo 正在运行示例2: 多目标场景...
pixi run python examples/example2_multi_target.py
pause
goto menu

:example3
echo.
echo 正在运行示例3: 参数调优...
pixi run python examples/example3_parameter_tuning.py
pause
goto menu

:example4
echo.
echo 正在运行示例4: 信噪比分析...
pixi run python examples/example4_snr_analysis.py
pause
goto menu

:example5
echo.
echo 正在运行示例5: 自定义可视化...
pixi run python examples/example5_custom_visualization.py
pause
goto menu

:example6
echo.
echo 正在运行示例6: 批量仿真...
pixi run python examples/example6_batch_simulation.py
pause
goto menu

:all
echo.
echo 正在运行所有示例...
echo.
for %%i in (1 2 3 4 5 6) do (
    echo ================================
    echo 运行示例 %%i
    echo ================================
    call :example%%i
)
echo.
echo 所有示例运行完成！
pause
goto menu

:end
echo.
echo 感谢使用！再见！
exit /b 0
