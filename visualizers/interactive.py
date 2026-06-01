"""
交互式可视化模块

提供可交互的距离-多普勒谱：
- 鼠标悬停：实时显示 (距离, 速度, 功率) 坐标
- 鼠标点击：选中点高亮 + 详情面板
- 目标标记：点击目标弹出详细信息
- 十字光标：辅助精确定位
- 缩放/平移：matplotlib 内置工具栏

使用方式：
    plot_rd_interactive(processed_result, target_info=...)

注意：需要 matplotlib 支持交互的后端（TkAgg/Qt5Agg），
      在 PyCharm/VS Code 中可能需要额外配置。
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from contracts import ProcessedResult, Target
from utils.axes import compute_edges
from utils.physics import wrap_velocity


def _get_target_attr(target, key, default=None):
    if isinstance(target, Target):
        return getattr(target, key, default)
    return target.get(key, default) if isinstance(target, dict) else getattr(target, key, default)


class InteractiveRDPlot:
    """
    交互式距离-多普勒谱

    功能：
    - 悬停显示坐标 (Range, Velocity, Power)
    - 点击选中点，高亮显示 + 文本框
    - 十字光标
    - 可选目标标记（点击显示详情）
    """

    def __init__(
        self,
        processed_result: ProcessedResult,
        target_info: dict = None,
        title: str = "Interactive Range-Doppler Spectrum"
    ):
        self.pr = processed_result
        self.rd = processed_result.range_doppler       # [range, doppler]
        self.rd_db = 20 * np.log10(self.rd + 1e-10)
        self.range_axis = processed_result.range_axis
        self.doppler_axis = processed_result.doppler_axis
        self.target_info = target_info
        self.title = title

        # 选中点状态
        self.selected_point = None
        self.selected_marker = None
        self.selected_text = None

        self._build_figure()

    def _build_figure(self):
        """构建图形"""
        self.fig, self.ax = plt.subplots(figsize=(14, 8))

        # 计算边缘
        r_edges = compute_edges(self.range_axis)
        d_edges = compute_edges(self.doppler_axis)

        # 绘制 RD 谱
        self.mesh = self.ax.pcolormesh(
            r_edges, d_edges, self.rd_db.T,
            shading='flat', cmap='jet'
        )
        self.ax.set_xlabel('Range (m)', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('Velocity (m/s)', fontsize=12, fontweight='bold')
        self.ax.set_title(self.title, fontsize=14, fontweight='bold')

        # 颜色条
        cbar = plt.colorbar(self.mesh, ax=self.ax, shrink=0.85, aspect=25)
        cbar.set_label('Power (dB)', fontsize=11, fontweight='bold')

        # 十字光标
        self.cursor = Cursor(self.ax, useblit=True, color='white',
                             linewidth=0.8, linestyle='--')

        # 坐标显示文本框（左上角）
        self.coord_text = self.ax.text(
            0.02, 0.98, '', transform=self.ax.transAxes,
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='black',
                      alpha=0.75, edgecolor='white'),
            color='white', family='monospace'
        )

        # 选中点标注
        self.anno_text = self.ax.annotate(
            '', xy=(0, 0), xytext=(15, 15),
            textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#2ecc71',
                      alpha=0.9, edgecolor='black'),
            fontsize=9, color='white', family='monospace',
            arrowprops=dict(arrowstyle='->', color='white', lw=1.2),
            visible=False
        )

        # 绘制目标标记
        self._draw_targets()

        # 绑定事件
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_move)
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)
        self.fig.canvas.mpl_connect('key_press_event', self._on_key)

        plt.tight_layout()

    def _draw_targets(self):
        """绘制目标标记"""
        if not self.target_info or 'targets' not in self.target_info:
            return

        max_v = abs(self.doppler_axis[-1])
        markers = ['o', 's', '^', 'D', 'v']
        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']

        for i, t in enumerate(self.target_info['targets']):
            R = _get_target_attr(t, 'range')
            V = _get_target_attr(t, 'velocity', 0)
            # 多普勒模糊
            V_wrapped = wrap_velocity(V, max_v)
            m = markers[i % len(markers)]
            c = colors[i % len(colors)]
            self.ax.plot(R, V_wrapped, marker=m, color=c,
                         markersize=12, markeredgewidth=2,
                         markeredgecolor='white', linestyle='None',
                         label=f'T{i+1}: R={R}m, V={V}m/s')

        self.ax.legend(fontsize=9, loc='upper right',
                       framealpha=0.9, edgecolor='gray')

    def _on_move(self, event):
        """鼠标移动：实时显示坐标"""
        if event.inaxes != self.ax:
            self.coord_text.set_text('')
            self.fig.canvas.draw_idle()
            return

        r = event.xdata
        v = event.ydata

        # 查找最近的 RD 谱值
        r_idx = np.argmin(np.abs(self.range_axis - r))
        d_idx = np.argmin(np.abs(self.doppler_axis - v))
        r_actual = self.range_axis[r_idx]
        v_actual = self.doppler_axis[d_idx]
        power = self.rd_db[r_idx, d_idx]

        self.coord_text.set_text(
            f'Range: {r_actual:7.1f} m\n'
            f'Velocity: {v_actual:+7.2f} m/s\n'
            f'Power: {power:7.1f} dB'
        )
        self.fig.canvas.draw_idle()

    def _on_click(self, event):
        """鼠标点击：选中点"""
        if event.inaxes != self.ax:
            return

        r = event.xdata
        v = event.ydata

        r_idx = np.argmin(np.abs(self.range_axis - r))
        d_idx = np.argmin(np.abs(self.doppler_axis - v))
        r_actual = self.range_axis[r_idx]
        v_actual = self.doppler_axis[d_idx]
        power = self.rd_db[r_idx, d_idx]
        power_linear = self.rd[r_idx, d_idx]

        # 删除旧的选中标记
        if self.selected_marker is not None:
            self.selected_marker.remove()

        # 画新的选中点
        self.selected_marker, = self.ax.plot(
            r_actual, v_actual, 'w+', markersize=18,
            markeredgewidth=2.5, zorder=10
        )

        # 更新标注
        self.anno_text.set_text(
            f'R={r_actual:.1f}m\n'
            f'V={v_actual:+.2f}m/s\n'
            f'P={power:.1f}dB'
        )
        self.anno_text.xy = (r_actual, v_actual)
        self.anno_text.set_visible(True)

        self.selected_point = (r_actual, v_actual, power, power_linear)
        self.fig.canvas.draw_idle()

    def _on_key(self, event):
        """按键事件"""
        if event.key == 'escape':
            # ESC 清除选中
            if self.selected_marker is not None:
                self.selected_marker.remove()
                self.selected_marker = None
            self.anno_text.set_visible(False)
        self.selected_point = None
        self.fig.canvas.draw_idle()

    def show(self):
        plt.show()


def plot_rd_interactive(
    processed_result: ProcessedResult,
    target_info: dict = None,
    title: str = "Interactive Range-Doppler Spectrum",
    save_path: str = None,
    show: bool = True
):
    """
    交互式距离-多普勒谱

    操作：
    - 鼠标移动：左上角显示 (距离, 速度, 功率)
    - 鼠标点击：选中点高亮 + 标注
    - ESC 键：清除选中
    - 工具栏：缩放/平移/保存

    Args:
        processed_result: 处理结果
        target_info: 目标信息字典
        title: 标题
        save_path: 保存路径
        show: 是否显示
    """
    plot = InteractiveRDPlot(processed_result, target_info, title)

    if save_path:
        plot.fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")

    if show:
        plot.show()


def plot_comparison_interactive(
    clean: ProcessedResult,
    processed: ProcessedResult,
    target_info: dict = None,
    clean_label: str = "Clean",
    processed_label: str = "Processed",
    title: str = "RD Spectrum Comparison",
    save_path: str = None,
    show: bool = True
):
    """
    交互式双面板对比图

    左：干净信号 RD 谱
    右：处理后/受干扰 RD 谱
    鼠标在任一面板移动，另一面板同步显示十字光标

    Args:
        clean: 干净信号处理结果
        processed: 处理后/受干扰信号处理结果
        target_info: 目标信息
        clean_label: 左面板标签
        processed_label: 右面板标签
        title: 总标题
        save_path: 保存路径
        show: 是否显示
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

    rd1_db = 20 * np.log10(clean.range_doppler + 1e-10)
    rd2_db = 20 * np.log10(processed.range_doppler + 1e-10)

    r_ax = clean.range_axis
    d_ax = clean.doppler_axis
    r_edges = compute_edges(r_ax)
    d_edges = compute_edges(d_ax)

    mesh1 = ax1.pcolormesh(r_edges, d_edges, rd1_db.T, shading='flat', cmap='jet')
    mesh2 = ax2.pcolormesh(r_edges, d_edges, rd2_db.T, shading='flat', cmap='jet')

    for ax, label, mesh in [(ax1, clean_label, mesh1), (ax2, processed_label, mesh2)]:
        ax.set_xlabel('Range (m)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Velocity (m/s)', fontsize=11, fontweight='bold')
        ax.set_title(label, fontsize=12, fontweight='bold')
        plt.colorbar(mesh, ax=ax, shrink=0.85, label='dB')

    # 坐标文本
    coord1 = ax1.text(0.02, 0.98, '', transform=ax1.transAxes,
                       fontsize=9, va='top', family='monospace',
                       bbox=dict(boxstyle='round', facecolor='black', alpha=0.75),
                       color='white')
    coord2 = ax2.text(0.02, 0.98, '', transform=ax2.transAxes,
                       fontsize=9, va='top', family='monospace',
                       bbox=dict(boxstyle='round', facecolor='black', alpha=0.75),
                       color='white')

    # 十字光标线
    hline1 = ax1.axhline(color='white', lw=0.5, ls='--', visible=False)
    vline1 = ax1.axvline(color='white', lw=0.5, ls='--', visible=False)
    hline2 = ax2.axhline(color='white', lw=0.5, ls='--', visible=False)
    vline2 = ax2.axvline(color='white', lw=0.5, ls='--', visible=False)

    def update_coords(ax_src, coord_text, r, v, rd_db_src):
        r_idx = np.argmin(np.abs(r_ax - r))
        d_idx = np.argmin(np.abs(d_ax - v))
        power = rd_db_src[r_idx, d_idx]
        coord_text.set_text(f'R={r_ax[r_idx]:.1f}m\nV={d_ax[d_idx]:+.2f}m/s\nP={power:.1f}dB')

    def on_move(event):
        for ax_src, coord, rd_db, hl, vl in [
            (ax1, coord1, rd1_db, hline1, vline1),
            (ax2, coord2, rd2_db, hline2, vline2)
        ]:
            if event.inaxes == ax_src:
                r, v = event.xdata, event.ydata
                update_coords(ax_src, coord, r, v, rd_db)
                hl.set_ydata([v, v])
                hl.set_visible(True)
                vl.set_xdata([r, r])
                vl.set_visible(True)
            else:
                coord.set_text('')
                hl.set_visible(False)
                vl.set_visible(False)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect('motion_notify_event', on_move)

    # 目标标记
    if target_info and 'targets' in target_info:
        max_v = abs(d_ax[-1])
        for i, t in enumerate(target_info['targets']):
            v_wrapped = wrap_velocity(_get_target_attr(t, 'velocity'), max_v)
            for ax in [ax1, ax2]:
                ax.plot(_get_target_attr(t, 'range'), v_wrapped, 'w+', markersize=12,
                        markeredgewidth=2)

    fig.suptitle(title, fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")

    if show:
        plt.show()
    else:
        plt.close()
