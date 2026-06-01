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
from contracts import ProcessedResult, Target
from utils.axes import compute_edges
from utils.physics import wrap_velocity


def _get_target_attr(target, key, default=None):
    """兼容 Target 对象和 dict 的目标属性访问"""
    if isinstance(target, Target):
        return getattr(target, key, default)
    return target.get(key, default) if isinstance(target, dict) else getattr(target, key, default)


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
    
    # 绘图 - 使用更合适的尺寸比例
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # 使用 pcolormesh 替代 contourf，避免空白问题并提高性能
    # rd_spectrum 形状是 [range_bins, doppler_bins] = (250, 128)
    # pcolormesh(X, Y, C) 要求 C.shape = (len(Y)-1, len(X)-1)
    # 我们希望 X=Range, Y=Doppler，所以：
    #   X_edges = range_edges (251), Y_edges = doppler_edges (129)
    #   C 应该是 rd_db.T，形状 (128, 250)
    
    range_edges = compute_edges(range_axis)
    doppler_edges = compute_edges(doppler_axis)
    
    mesh = ax.pcolormesh(range_edges, doppler_edges, rd_db.T, shading='flat', cmap='jet')
    
    # 优化坐标轴标签和标题
    ax.set_xlabel('Range (m)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Velocity (m/s)', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=10)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # 优化颜色条
    cbar = plt.colorbar(mesh, ax=ax, shrink=0.8, aspect=20)
    cbar.set_label('Amplitude (dB)', fontsize=11, fontweight='bold')
    cbar.ax.tick_params(labelsize=9)
    
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
    
    # 创建子图 - 使用 GridSpec 更好地控制布局
    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(2, 1, height_ratios=[2.5, 1], hspace=0.3)
    
    ax1 = fig.add_subplot(gs[0])  # RD 谱图（占 2.5 份高度）
    ax2 = fig.add_subplot(gs[1])  # 距离剖面图（占 1 份高度）
    
    # 上图：距离-多普勒谱
    # rd_spectrum 形状是 [range_bins, doppler_bins]
    # 使用 pcolormesh 避免空白问题
    
    range_edges = compute_edges(range_axis)
    doppler_edges = compute_edges(doppler_axis)
    
    mesh = ax1.pcolormesh(range_edges, doppler_edges, rd_db.T, shading='flat', cmap='jet')
    
    # 设置坐标轴标签和标题 - 增加顶部留白避免与总标题重叠
    ax1.set_xlabel('Range (m)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Velocity (m/s)', fontsize=12, fontweight='bold')
    ax1.set_title('Range-Doppler Spectrum', fontsize=13, fontweight='bold', pad=20)
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # 优化颜色条 - 进一步减小 pad 让 colorbar 紧贴 RD 谱，调整 aspect 使其更窄
    cbar1 = plt.colorbar(mesh, ax=ax1, shrink=0.98, aspect=35, pad=0.01)
    cbar1.set_label('Amplitude (dB)', fontsize=11, fontweight='bold')
    cbar1.ax.tick_params(labelsize=9)
    
    # 标注真实目标位置（考虑多普勒模糊）
    if target_info and 'targets' in target_info:
        max_velocity = abs(doppler_axis[-1])  # 最大不模糊速度
        
        # 定义不同目标的标记样式
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow', 'lime', 'pink']
        
        for i, target in enumerate(target_info['targets']):
            R_true = _get_target_attr(target, 'range')
            V_true = _get_target_attr(target, 'velocity')
            
            # 计算模糊后的速度
            V_wrapped = wrap_velocity(V_true, max_velocity)
            
            # 选择标记和颜色
            marker = markers[i % len(markers)]
            color = colors[i % len(colors)]
            
            # 判断是否发生模糊
            is_aliased = abs(V_true) > max_velocity
            
            # 创建标签 - 图例中同时显示真实值和模糊值
            if is_aliased:
                label = f'T{i+1}: True(R={R_true}m, V={V_true}m/s) → Aliased(V={V_wrapped:.1f}m/s)'
            else:
                label = f'T{i+1}: R={R_true}m, V={V_true}m/s'
            
            # 绘制标记（在模糊后的位置，即实际检测到的位置）
            ax1.plot(R_true, V_wrapped, marker=marker, color=color, 
                    markersize=10, markeredgewidth=2, markeredgecolor='white',
                    linestyle='None', label=label)
        
        # 优化图例位置和样式
        legend = ax1.legend(loc='upper right', bbox_to_anchor=(0.98, 0.98), 
                          fontsize=8, framealpha=0.95, title='Targets',
                          title_fontsize=9)
        legend.get_frame().set_edgecolor('gray')
        legend.get_frame().set_linewidth(1)
    
    # 下图：距离剖面
    ax2.plot(range_axis, profile_db, 'b-', linewidth=2)
    ax2.set_xlabel('Range (m)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Amplitude (dB)', fontsize=12, fontweight='bold')
    ax2.set_title('Range Profile', fontsize=13, fontweight='bold', pad=10)
    ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax2.set_xlim([0, range_axis[-1]])
    
    # 标注真实目标距离（使用与 RD 谱相同的颜色）
    if target_info and 'targets' in target_info:
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow', 'lime', 'pink']
        
        for i, target in enumerate(target_info['targets']):
            R_true = _get_target_attr(target, 'range')
            color = colors[i % len(colors)]
            marker = markers[i % len(markers)]
            
            ax2.axvline(x=R_true, color=color, linestyle='--', alpha=0.7, linewidth=1.5)
            ax2.plot(R_true, ax2.get_ylim()[1]*0.95, marker=marker, color=color,
                    markersize=8, markeredgewidth=1.5, markeredgecolor='white')
        
        # 添加图例
        legend_elements = [plt.Line2D([0], [0], color=colors[i % len(colors)], 
                                     linestyle='--', linewidth=1.5, alpha=0.7,
                                     label=f'T{i+1}: R={_get_target_attr(target, "range")}m')
                          for i, target in enumerate(target_info['targets'])]
        legend = ax2.legend(handles=legend_elements, loc='upper right', 
                          fontsize=8, framealpha=0.95)
        legend.get_frame().set_edgecolor('gray')
        legend.get_frame().set_linewidth(1)
    
    # 添加总标题 - 调整位置避免与子图标题重叠
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.97)
    
    # 优化布局 - 使用 constrained_layout 替代 tight_layout 以避免警告
    try:
        fig.set_constrained_layout(True)
    except Exception:
        # 如果 constrained_layout 不可用，使用手动调整 - 进一步减小右侧留白
        plt.subplots_adjust(top=0.92, bottom=0.08, left=0.10, right=0.99, hspace=0.3)
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    if show:
        plt.show()
    else:
        plt.close()


def plot_antenna_array(
    antenna_array,
    title: str = "MIMO Antenna Array Layout",
    save_path: str = None,
    show: bool = True
):
    """
    绘制 MIMO 天线阵列布局（物理阵列 + 虚拟阵列）

    左图：物理阵列 — TX 和 RX 分开显示
    右图：虚拟阵列 — 全部虚拟通道

    坐标归一化到 λ。

    Args:
        antenna_array: MimoAntennaArray 实例
        title: 图表标题
        save_path: 保存路径
        show: 是否显示
    """
    from matplotlib.lines import Line2D

    num_tx = antenna_array.num_tx
    num_rx = antenna_array.num_rx
    lam = antenna_array.wavelength * 1e3  # mm
    tx_d = antenna_array.tx_spacing / antenna_array.wavelength   # in λ
    rx_d = antenna_array.rx_spacing / antenna_array.wavelength   # in λ
    virtual_positions = antenna_array.get_virtual_element_positions()
    virt_norm = virtual_positions / antenna_array.wavelength      # in λ

    tx_color = '#e74c3c'
    rx_color = '#3498db'
    virt_color = '#e67e22'

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # ---- 左图：物理阵列 ----
    ax = axes[0]
    for tx_idx in range(num_tx):
        ax.plot(tx_idx * tx_d, 1, 's', color=tx_color, markersize=14,
                markeredgecolor='black', markeredgewidth=1.2, zorder=3)
        ax.annotate(f'TX{tx_idx}', (tx_idx * tx_d, 1),
                    textcoords="offset points", xytext=(0, 12),
                    ha='center', fontsize=10, fontweight='bold', color=tx_color)

    for rx_idx in range(num_rx):
        ax.plot(rx_idx * rx_d, 0, 's', color=rx_color, markersize=12,
                markeredgecolor='black', markeredgewidth=1.2, zorder=3)
        ax.annotate(f'RX{rx_idx}', (rx_idx * rx_d, 0),
                    textcoords="offset points", xytext=(0, -14),
                    ha='center', fontsize=10, fontweight='bold', color=rx_color)

    # 间距标注
    if num_tx > 1:
        ax.annotate('', xy=(tx_d, 1.3), xytext=(0, 1.3),
                    arrowprops=dict(arrowstyle='<->', color=tx_color, lw=1.5))
        ax.text(tx_d / 2, 1.38, f'{tx_d:.1f}λ', ha='center', fontsize=8, color=tx_color)
    if num_rx > 1:
        ax.annotate('', xy=(rx_d, -0.3), xytext=(0, -0.3),
                    arrowprops=dict(arrowstyle='<->', color=rx_color, lw=1.5))
        ax.text(rx_d / 2, -0.45, f'{rx_d:.1f}λ', ha='center', fontsize=8, color=rx_color)

    ax.set_xlabel('Position (λ)', fontsize=11)
    ax.set_title(f'Physical Array ({num_tx} TX + {num_rx} RX)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_ylim(-0.7, 1.8)
    ax.set_yticks([])
    ax.legend(handles=[
        Line2D([0], [0], marker='s', color='w', markerfacecolor=tx_color,
               markeredgecolor='black', markersize=12, label=f'TX ({num_tx})'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor=rx_color,
               markeredgecolor='black', markersize=10, label=f'RX ({num_rx})'),
    ], fontsize=9, loc='upper right')

    # ---- 右图：虚拟阵列 ----
    ax = axes[1]
    for i, x in enumerate(virt_norm):
        ax.plot(x, 0, 'o', color=virt_color, markersize=13,
                markeredgecolor='black', markeredgewidth=1.2, zorder=3)
        ax.annotate(f'{i}', (x, 0),
                    textcoords="offset points", xytext=(0, -14),
                    ha='center', fontsize=7, color='#555')

    # 孔径标注
    aperture_lam = antenna_array.effective_aperture / antenna_array.wavelength
    ax.annotate('', xy=(virt_norm[-1], 0.3), xytext=(virt_norm[0], 0.3),
                arrowprops=dict(arrowstyle='<->', color='#2c3e50', lw=1.5))
    ax.text((virt_norm[0] + virt_norm[-1]) / 2, 0.42,
            f'Aperture = {aperture_lam:.1f}λ',
            ha='center', fontsize=9, color='#2c3e50')

    ax.set_xlabel('Position (λ)', fontsize=11)
    ax.set_title(f'Virtual Array ({len(virtual_positions)} channels)',
                 fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_ylim(-0.7, 0.8)
    ax.set_yticks([])
    ax.legend(handles=[
        Line2D([0], [0], marker='o', color='w', markerfacecolor=virt_color,
               markeredgecolor='black', markersize=11,
               label=f'Virtual ({len(virtual_positions)})'),
    ], fontsize=9, loc='upper right')

    fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


def plot_angle_spectrum(
    dbf_result: dict,
    processed_result: ProcessedResult,
    title: str = "DBF Angle Spectrum",
    save_path: str = None,
    show: bool = True
):
    """
    绘制 DBF 角度谱

    - 左：Range-Angle 热力图（对多普勒维取最大值投影）
    - 右：最强目标处的 Angle-Doppler 热力图

    Args:
        dbf_result: dbf_angle_estimation 返回的字典
        processed_result: 处理结果契约对象
        title: 图表标题
        save_path: 保存路径
        show: 是否显示
    """
    angle_spectrum = dbf_result['angle_spectrum']  # [range, doppler, angle]
    angles_deg = np.degrees(dbf_result['angles'])
    range_axis = processed_result.range_axis
    doppler_axis = processed_result.doppler_axis

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # ---- 左图：Range-Angle（对多普勒取最大值）----
    ax = axes[0]
    range_angle = np.max(angle_spectrum, axis=1)  # [range, angle]
    range_angle_db = 10 * np.log10(range_angle + 1e-10)

    extent = [angles_deg[0], angles_deg[-1], range_axis[0], range_axis[-1]]
    im = ax.imshow(range_angle_db, aspect='auto', origin='lower',
                   extent=extent, cmap='jet', interpolation='bilinear')
    ax.set_xlabel('Angle (°)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Range (m)', fontsize=12, fontweight='bold')
    ax.set_title('Range-Angle Map\n(max over Doppler)', fontsize=12, fontweight='bold')
    plt.colorbar(im, ax=ax, shrink=0.85, label='Power (dB)')

    peak_idx = np.unravel_index(np.argmax(range_angle), range_angle.shape)
    ax.axhline(y=range_axis[peak_idx[0]], color='white', linestyle='--',
               linewidth=0.8, alpha=0.7)

    # ---- 右图：Angle-Doppler（在最强距离处）----
    ax = axes[1]
    peak_range_idx = peak_idx[0]
    angle_doppler = angle_spectrum[peak_range_idx, :, :]  # [doppler, angle]
    angle_doppler_db = 10 * np.log10(angle_doppler + 1e-10)

    extent2 = [angles_deg[0], angles_deg[-1], doppler_axis[0], doppler_axis[-1]]
    im2 = ax.imshow(angle_doppler_db, aspect='auto', origin='lower',
                    extent=extent2, cmap='jet', interpolation='bilinear')
    ax.set_xlabel('Angle (°)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Velocity (m/s)', fontsize=12, fontweight='bold')
    ax.set_title(f'Angle-Doppler Map\n(at R={range_axis[peak_range_idx]:.0f}m)',
                 fontsize=12, fontweight='bold')
    plt.colorbar(im2, ax=ax, shrink=0.85, label='Power (dB)')

    fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()


def plot_mimo_comprehensive(
    processed_result: ProcessedResult,
    dbf_result: dict = None,
    antenna_array=None,
    target_info: dict = None,
    title: str = "MIMO Radar Simulation",
    save_path: str = None,
    show: bool = True
):
    """
    MIMO 综合展示图：RD 谱 + 天线阵列 + 角度谱

    Args:
        processed_result: 处理结果契约对象
        dbf_result: DBF 结果字典（可选）
        antenna_array: MimoAntennaArray 实例（可选）
        target_info: 目标信息字典
        title: 总标题
        save_path: 保存路径
        show: 是否显示
    """
    rd_spectrum = processed_result.range_doppler
    range_axis = processed_result.range_axis
    doppler_axis = processed_result.doppler_axis

    has_array = antenna_array is not None
    has_dbf = dbf_result is not None and 'angle_spectrum' in dbf_result

    if has_array and has_dbf:
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3)
        ax_rd = fig.add_subplot(gs[0, 0])
        ax_arr = fig.add_subplot(gs[0, 1])
        ax_ra = fig.add_subplot(gs[1, 0])
        ax_ad = fig.add_subplot(gs[1, 1])
    elif has_array:
        fig = plt.figure(figsize=(18, 8))
        gs = fig.add_gridspec(2, 2, height_ratios=[2, 1], hspace=0.35, wspace=0.3)
        ax_rd = fig.add_subplot(gs[0, :])
        ax_arr = fig.add_subplot(gs[1, 0])
        ax_ra = None
        ax_ad = fig.add_subplot(gs[1, 1])
        ax_ad.set_visible(False)
    else:
        fig = plt.figure(figsize=(16, 9))
        gs = fig.add_gridspec(2, 1, height_ratios=[2.5, 1], hspace=0.3)
        ax_rd = fig.add_subplot(gs[0])
        ax_arr = None
        ax_ra = None
        ax_ad = None

    # ---- RD 谱 ----
    rd_db = 20 * np.log10(rd_spectrum + 1e-10)
    range_edges = compute_edges(range_axis)
    doppler_edges = compute_edges(doppler_axis)

    mesh = ax_rd.pcolormesh(range_edges, doppler_edges, rd_db.T,
                            shading='flat', cmap='jet')
    ax_rd.set_xlabel('Range (m)', fontsize=11, fontweight='bold')
    ax_rd.set_ylabel('Velocity (m/s)', fontsize=11, fontweight='bold')
    ax_rd.set_title('Range-Doppler Spectrum', fontsize=12, fontweight='bold')
    ax_rd.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    plt.colorbar(mesh, ax=ax_rd, shrink=0.9, aspect=25, label='dB')

    if target_info and 'targets' in target_info:
        max_v = abs(doppler_axis[-1])
        markers = ['o', 's', '^', 'D', 'v']
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        for i, t in enumerate(target_info['targets']):
            v_wrapped = wrap_velocity(_get_target_attr(t, 'velocity'), max_v)
            ax_rd.plot(_get_target_attr(t, 'range'), v_wrapped, marker=markers[i % len(markers)],
                       color=colors[i % len(colors)], markersize=10,
                       markeredgewidth=2, markeredgecolor='white', linestyle='None',
                       label=f'T{i+1}')
        ax_rd.legend(fontsize=8, loc='upper right')

    # ---- 天线阵列 ----
    if ax_arr is not None and ax_arr.get_visible():
        from matplotlib.lines import Line2D
        num_tx = antenna_array.num_tx
        num_rx = antenna_array.num_rx
        tx_d = antenna_array.tx_spacing / antenna_array.wavelength
        rx_d = antenna_array.rx_spacing / antenna_array.wavelength
        virt_norm = antenna_array.get_virtual_element_positions() / antenna_array.wavelength
        tx_color = '#e74c3c'
        rx_color = '#3498db'
        virt_color = '#e67e22'

        for tx_idx in range(num_tx):
            ax_arr.plot(tx_idx * tx_d, 2, 's', color=tx_color,
                       markersize=9, markeredgecolor='black', markeredgewidth=0.8)
        for rx_idx in range(num_rx):
            ax_arr.plot(rx_idx * rx_d, 1, 's', color=rx_color,
                       markersize=8, markeredgecolor='black', markeredgewidth=0.8)
        for i, x in enumerate(virt_norm):
            ax_arr.plot(x, 0, 'o', color=virt_color,
                       markersize=7, markeredgecolor='black', markeredgewidth=0.5)
            ax_arr.annotate(f'{i}', (x, 0), textcoords="offset points",
                           xytext=(0, -9), ha='center', fontsize=5, color='#555')

        ax_arr.set_xlabel('Position (λ)', fontsize=10)
        ax_arr.set_title(f'Physical ({num_tx}TX + {num_rx}RX)  |  '
                         f'Virtual ({antenna_array.virtual_array_size}ch)',
                         fontsize=11, fontweight='bold')
        ax_arr.grid(True, alpha=0.3, linestyle='--')
        ax_arr.set_ylim(-0.6, 2.8)
        ax_arr.set_yticks([])
        ax_arr.legend(handles=[
            Line2D([0], [0], marker='s', color='w', markerfacecolor=tx_color,
                   markeredgecolor='black', markersize=8, label='TX'),
            Line2D([0], [0], marker='s', color='w', markerfacecolor=rx_color,
                   markeredgecolor='black', markersize=7, label='RX'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor=virt_color,
                   markeredgecolor='black', markersize=6, label='Virtual'),
        ], fontsize=7, loc='upper right')

    # ---- Range-Angle ----
    if ax_ra is not None:
        angles_deg = np.degrees(dbf_result['angles'])
        range_angle = np.max(dbf_result['angle_spectrum'], axis=1)
        range_angle_db = 10 * np.log10(range_angle + 1e-10)
        extent = [angles_deg[0], angles_deg[-1], range_axis[0], range_axis[-1]]
        im = ax_ra.imshow(range_angle_db, aspect='auto', origin='lower',
                          extent=extent, cmap='jet', interpolation='bilinear')
        ax_ra.set_xlabel('Angle (°)', fontsize=11, fontweight='bold')
        ax_ra.set_ylabel('Range (m)', fontsize=11, fontweight='bold')
        ax_ra.set_title('Range-Angle Map', fontsize=12, fontweight='bold')
        plt.colorbar(im, ax=ax_ra, shrink=0.85, label='dB')

    # ---- Angle-Doppler ----
    if ax_ad is not None and ax_ad.get_visible():
        angles_deg = np.degrees(dbf_result['angles'])
        ra_map = np.max(dbf_result['angle_spectrum'], axis=1)
        peak_r = np.unravel_index(np.argmax(ra_map), ra_map.shape)[0]
        ad = dbf_result['angle_spectrum'][peak_r, :, :]
        ad_db = 10 * np.log10(ad + 1e-10)
        extent2 = [angles_deg[0], angles_deg[-1], doppler_axis[0], doppler_axis[-1]]
        im2 = ax_ad.imshow(ad_db, aspect='auto', origin='lower',
                           extent=extent2, cmap='jet', interpolation='bilinear')
        ax_ad.set_xlabel('Angle (°)', fontsize=11, fontweight='bold')
        ax_ad.set_ylabel('Velocity (m/s)', fontsize=11, fontweight='bold')
        ax_ad.set_title(f'Angle-Doppler (R≈{range_axis[peak_r]:.0f}m)',
                        fontsize=12, fontweight='bold')
        plt.colorbar(im2, ax=ax_ad, shrink=0.85, label='dB')

    fig.suptitle(title, fontsize=16, fontweight='bold', y=1.01)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()
