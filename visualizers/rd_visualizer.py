"""
可视化/输出层 - 雷达仿真结果可视化

本模块提供雷达仿真结果的可视化功能，包括：
1. 距离-多普勒谱热力图
2. 距离剖面图
3. 综合展示图
"""

import sys
import os

# 添加项目根目录到 Python 路径（支持直接运行此文件）
if __name__ == "__main__":
    # 如果在 visualizers 目录下运行，需要添加上级目录
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from contracts import ProcessedResult


def wrap_velocity(velocity, max_velocity):
    """
    计算多普勒模糊后的速度（考虑周期性）
    
    Args:
        velocity: 真实速度 (m/s)
        max_velocity: 最大不模糊速度 (m/s)
        
    Returns:
        模糊后的速度 (m/s)，在 [-max_velocity, max_velocity] 范围内
    """
    # 多普勒频率是周期性的，周期为 PRF
    # 对应的速度周期为 2 * max_velocity
    velocity_range = 2 * max_velocity
    
    # 将速度映射到 [-max_velocity, max_velocity] 范围
    wrapped_v = ((velocity + max_velocity) % velocity_range) - max_velocity
    
    return wrapped_v


def plot_range_doppler(
    processed_result: ProcessedResult,
    title: str = "Range-Doppler Spectrum",
    save_path: str = None,
    show: bool = True
):
    """
    绘制距离-多普勒谱热力图
    
    Args:
        processed_result: 处理结果契约对象
        title: 图表标题
        save_path: 保存路径（可选）
        show: 是否显示图表
    """
    rd_spectrum = processed_result.range_doppler
    range_axis = processed_result.range_axis
    doppler_axis = processed_result.doppler_axis
    
    # 转换为 dB
    rd_db = 20 * np.log10(rd_spectrum + 1e-10)
    
    # 创建网格
    R, V = np.meshgrid(range_axis, doppler_axis, indexing='ij')
    
    # 绘图
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 使用 pcolormesh 替代 contourf，避免空白问题并提高性能
    # rd_spectrum 形状是 [range_bins, doppler_bins] = (250, 128)
    # pcolormesh(X, Y, C) 要求 C.shape = (len(Y)-1, len(X)-1)
    # 我们希望 X=Range, Y=Doppler，所以：
    #   X_edges = range_edges (251), Y_edges = doppler_edges (129)
    #   C 应该是 rd_db.T，形状 (128, 250)
    
    range_edges = np.zeros(len(range_axis) + 1)
    range_edges[:-1] = range_axis - (range_axis[1] - range_axis[0]) / 2
    range_edges[-1] = range_axis[-1] + (range_axis[1] - range_axis[0]) / 2
    
    doppler_edges = np.zeros(len(doppler_axis) + 1)
    doppler_edges[:-1] = doppler_axis - (doppler_axis[1] - doppler_axis[0]) / 2
    doppler_edges[-1] = doppler_axis[-1] + (doppler_axis[1] - doppler_axis[0]) / 2
    
    mesh = ax.pcolormesh(range_edges, doppler_edges, rd_db.T, shading='flat', cmap='jet')
    ax.set_xlabel('Range (m)', fontsize=12)
    ax.set_ylabel('Velocity (m/s)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # 添加颜色条
    cbar = plt.colorbar(mesh, ax=ax)
    cbar.set_label('Amplitude (dB)', fontsize=11)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


def plot_range_profile(
    processed_result: ProcessedResult,
    title: str = "Range Profile",
    save_path: str = None,
    show: bool = True
):
    """
    绘制距离剖面图
    
    Args:
        processed_result: 处理结果契约对象
        title: 图表标题
        save_path: 保存路径（可选）
        show: 是否显示图表
    """
    range_profile = processed_result.range_profile
    range_axis = processed_result.range_axis
    
    # 转换为 dB
    profile_db = 20 * np.log10(range_profile + 1e-10)
    
    # 绘图
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(range_axis, profile_db, 'b-', linewidth=1.5)
    ax.set_xlabel('Range (m)', fontsize=12)
    ax.set_ylabel('Amplitude (dB)', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, range_axis[-1]])
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


def plot_comprehensive(
    processed_result: ProcessedResult,
    target_info: dict = None,
    title: str = "LFMCW Radar Simulation Results",
    save_path: str = None,
    show: bool = True
):
    """
    绘制综合展示图（包含距离-多普勒谱和距离剖面）
    
    Args:
        processed_result: 处理结果契约对象
        target_info: 目标信息字典（用于标注真实目标位置）
        title: 总标题
        save_path: 保存路径（可选）
        show: 是否显示图表
    """
    rd_spectrum = processed_result.range_doppler
    range_profile = processed_result.range_profile
    range_axis = processed_result.range_axis
    doppler_axis = processed_result.doppler_axis
    
    # 转换为 dB
    rd_db = 20 * np.log10(rd_spectrum + 1e-10)
    profile_db = 20 * np.log10(range_profile + 1e-10)
    
    # 创建子图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # 上图：距离-多普勒谱
    # rd_spectrum 形状是 [range_bins, doppler_bins]
    # 使用 pcolormesh 避免空白问题
    
    range_edges = np.zeros(len(range_axis) + 1)
    range_edges[:-1] = range_axis - (range_axis[1] - range_axis[0]) / 2
    range_edges[-1] = range_axis[-1] + (range_axis[1] - range_axis[0]) / 2
    
    doppler_edges = np.zeros(len(doppler_axis) + 1)
    doppler_edges[:-1] = doppler_axis - (doppler_axis[1] - doppler_axis[0]) / 2
    doppler_edges[-1] = doppler_axis[-1] + (doppler_axis[1] - doppler_axis[0]) / 2
    
    mesh = ax1.pcolormesh(range_edges, doppler_edges, rd_db.T, shading='flat', cmap='jet')
    ax1.set_ylabel('Velocity (m/s)', fontsize=11)
    ax1.set_title('Range-Doppler Spectrum', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    cbar1 = plt.colorbar(mesh, ax=ax1)
    cbar1.set_label('Amplitude (dB)', fontsize=10)
    
    # 标注真实目标位置（考虑多普勒模糊）
    if target_info and 'targets' in target_info:
        max_velocity = abs(doppler_axis[-1])  # 最大不模糊速度
        
        # 定义不同目标的标记样式
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow', 'lime', 'pink']
        
        for i, target in enumerate(target_info['targets']):
            R_true = target['range']
            V_true = target['velocity']
            
            # 计算模糊后的速度
            V_wrapped = wrap_velocity(V_true, max_velocity)
            
            # 选择标记和颜色
            marker = markers[i % len(markers)]
            color = colors[i % len(colors)]
            
            # 判断是否发生模糊
            is_aliased = abs(V_true) > max_velocity
            
            # 创建标签
            if is_aliased:
                label = f'T{i+1}: R={R_true}m, V={V_true}m/s (aliased→{V_wrapped:.1f}m/s)'
            else:
                label = f'T{i+1}: R={R_true}m, V={V_true}m/s'
            
            # 绘制标记（在模糊后的位置）
            ax1.plot(R_true, V_wrapped, marker=marker, color=color, 
                    markersize=12, markeredgewidth=2, markeredgecolor='white',
                    linestyle='None', label=label)
            
            # 如果发生模糊，用虚线连接真实位置和模糊位置
            if is_aliased:
                ax1.annotate('', xy=(R_true, V_wrapped), xytext=(R_true, V_true),
                           arrowprops=dict(arrowstyle='->', color=color, 
                                         lw=1.5, linestyle='--', alpha=0.6))
        
        ax1.legend(loc='upper right', fontsize=8, framealpha=0.9, title='Targets')
    
    # 下图：距离剖面
    ax2.plot(range_axis, profile_db, 'b-', linewidth=1.5)
    ax2.set_xlabel('Range (m)', fontsize=11)
    ax2.set_ylabel('Amplitude (dB)', fontsize=11)
    ax2.set_title('Range Profile', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([0, range_axis[-1]])
    
    # 标注真实目标距离（使用与 RD 谱相同的颜色）
    if target_info and 'targets' in target_info:
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow', 'lime', 'pink']
        
        for i, target in enumerate(target_info['targets']):
            R_true = target['range']
            color = colors[i % len(colors)]
            marker = markers[i % len(markers)]
            
            ax2.axvline(x=R_true, color=color, linestyle='--', alpha=0.7, linewidth=1.5)
            ax2.plot(R_true, ax2.get_ylim()[1]*0.95, marker=marker, color=color,
                    markersize=8, markeredgewidth=1.5, markeredgecolor='white')
        
        # 添加图例
        legend_elements = [plt.Line2D([0], [0], color=colors[i % len(colors)], 
                                     linestyle='--', linewidth=1.5, alpha=0.7,
                                     label=f'T{i+1}: R={target["range"]}m')
                          for i, target in enumerate(target_info['targets'])]
        ax2.legend(handles=legend_elements, loc='upper right', fontsize=8)
    
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()
