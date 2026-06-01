# ️ 工具和测试脚本

本目录包含各种工具脚本和测试程序。

##  测试脚本

### MIMO 相关
- **[test_mimo_quick.py](test_mimo_quick.py)** - MIMO 功能快速测试
- **[test_multi_target_annotation.py](test_multi_target_annotation.py)** - 多目标标注测试

### 可视化相关
- **[test_title_spacing.py](test_title_spacing.py)** - 标题间距测试
- **[test_optimized_layout.py](test_optimized_layout.py)** - 布局优化测试
- **[test_fixes.py](test_fixes.py)** - Bug 修复验证测试

### 其他测试
- **[simple_test.py](simple_test.py)** - 简单功能测试

## 🔧 工具脚本

### 调试工具
- **[debug_signal_model.py](debug_signal_model.py)** - 信号模型调试工具

### 运行脚本
- **[run_examples.bat](run_examples.bat)** - Windows 批处理脚本（运行所有示例）
- **[run_examples.sh](run_examples.sh)** - Linux/Mac Shell 脚本（运行所有示例）

## 💻 使用方法

### 运行单个测试
```bash
# MIMO 快速测试
pixi run python scripts/test_mimo_quick.py

# 标题间距测试
pixi run python scripts/test_title_spacing.py
```

### 运行所有示例
```bash
# Windows
scripts\run_examples.bat

# Linux/Mac
chmod +x scripts/run_examples.sh
./scripts/run_examples.sh
```

### 调试信号模型
```bash
pixi run python scripts/debug_signal_model.py
```

##  相关链接

- [项目根目录](../) - 返回项目根目录
- [examples/](../examples/) - 示例代码
- [docs/](../docs/) - 文档
