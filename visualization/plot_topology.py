# -*- coding: utf-8 -*-
"""
DD ERT 开关矩阵拓扑图
"""

import logging

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
import numpy as np

logger = logging.getLogger(__name__)

from configs.physical_params import n_elecs

plt.rcParams['axes.unicode_minus'] = False


def plot_dd_topology(selected_electrodes, filename='dd_topology.png'):
    """
    绘制 DD ERT 开关矩阵拓扑图

    参数:
        selected_electrodes: dict, 例如 {2: 0, 3: 1, 7: 2, 8: 3}
                           表示电极编号(1-21)映射到列索引(0=A, 1=B, 2=C, 3=D)
        filename: 输出文件名
    """
    fig, ax = plt.subplots(1, 1, figsize=(6, 10))

    # ========== 参数 ==========
    n_elecs = 21
    n_cols = 4
    sw_width = 1.0
    sw_height = 0.5
    matrix_left = 1

    col_labels = ['A', 'B', 'C', 'D']
    col_colors = ['red', 'red', 'blue', 'blue']

    # ========== 1. 电极 (左侧) ==========
    for i in range(n_elecs):
        y = -i * sw_height + sw_height / 2
        circle = Circle((0, y), 0.15, facecolor='gray', edgecolor='black', linewidth=1, zorder=10)
        ax.add_patch(circle)
        ax.text(-0.3, y, f'{i+1}', ha='right', va='center', fontsize=7)
        ax.annotate('', xy=(matrix_left, y), xytext=(0.2, y),
                    arrowprops=dict(arrowstyle='<->', color='gray', lw=1))

    # ========== 2. 列标签圆形 (顶部) ==========
    for j in range(n_cols):
        x = matrix_left + j * sw_width + sw_width / 2
        y_top = sw_height / 2 + sw_height * 2
        circle = Circle((x, y_top), 0.15, facecolor=col_colors[j], edgecolor='black', linewidth=1, zorder=10)
        ax.add_patch(circle)
        ax.text(x, y_top, col_labels[j], ha='center', va='center',
                fontsize=12, fontweight='bold', color='black', zorder=20)

        # 箭头
        if j < 2:
            ax.annotate('', xy=(x, y_top - 0.8), xytext=(x, y_top - 0.15),
                        arrowprops=dict(arrowstyle='->', color=col_colors[j], lw=1.5))
        else:
            ax.annotate('', xy=(x, y_top - 0.15), xytext=(x, y_top - 0.8),
                        arrowprops=dict(arrowstyle='->', color=col_colors[j], lw=1.5))

    # ========== 3. 21×4 开关矩阵 ==========
    for i in range(n_elecs):
        for j in range(n_cols):
            x = matrix_left + j * sw_width
            y = -i * sw_height

            if (i+1) in selected_electrodes and selected_electrodes[i+1] == j:
                rect = Rectangle((x, y), sw_width, sw_height,
                               facecolor=col_colors[j], edgecolor='black', linewidth=1, zorder=5)
            else:
                rect = Rectangle((x, y), sw_width, sw_height,
                               facecolor='white', edgecolor='#999999', linewidth=0.5, zorder=3)
            ax.add_patch(rect)

    # ========== 坐标 ==========
    ax.set_xlim(-1.5, matrix_left + n_cols * sw_width + 1)
    ax.set_ylim(-n_elecs * sw_height - 1, 3.5)
    ax.set_aspect('equal')
    ax.axis('off')

    plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
    logger.debug("Saved topology: %s", filename)
    plt.close()


if __name__ == '__main__':
    import os
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(script_dir)
    os.makedirs('results', exist_ok=True)

    # 示例1：电极2→A, 电极3→B, 电极7→C, 电极8→D
    selected1 = {2: 0, 3: 1, 7: 2, 8: 3}
    plot_dd_topology(selected1, 'results/dd_topology_1.png')

    # 示例2：电极1→A, 电极5→B, 电极12→C, 电极15→D
    selected2 = {1: 0, 5: 1, 12: 2, 15: 3}
    plot_dd_topology(selected2, 'results/dd_topology_2.png')

    # 示例3：电极10→A, 电极11→B, 电极18→C, 电极21→D
    selected3 = {10: 0, 11: 1, 18: 2, 21: 3}
    plot_dd_topology(selected3, 'results/dd_topology_3.png')
