# -*- coding: utf-8 -*-
"""
DD ERT 网格可视化脚本

绘制 Forward Mesh 和 Inverted Mesh (paraDomain)
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

# 添加项目根目录到 sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.insert(0, project_dir)
os.chdir(project_dir)

import numpy as np
import matplotlib.pyplot as plt
import pygimli as pg
import pygimli.meshtools as mt
from pygimli.physics import ert

from forward import create_geometry, create_scheme, create_resistivity_model, forward_simulation
from inversions import run_inversion
from configs.physical_params import (
    world_start, world_end, landfill_polygon,
    leak_x, leak_y
)


def draw_mesh_boundaries(ax, mesh, color='blue', linewidth=0.3):
    """
    绘制网格边界线

    参数:
        ax: matplotlib axes
        mesh: pg.Mesh
        color: 线条颜色
        linewidth: 线宽
    """
    for boundary in mesh.boundaries():
        start = boundary.node(0).pos()
        end = boundary.node(1).pos()
        ax.plot([start.x(), end.x()], [start.y(), end.y()], color=color, linewidth=linewidth)


def draw_mesh_cells(ax, mesh, color='green', linewidth=0.5):
    """
    绘制网格单元格边界线（通过遍历 cells 实现）

    参数:
        ax: matplotlib axes
        mesh: pg.Mesh
        color: 线条颜色
        linewidth: 线宽
    """
    drawn_segments = set()
    for cell in mesh.cells():
        nodes = cell.nodes()
        n_nodes = len(nodes)
        for i in range(n_nodes):
            n0 = nodes[i]
            n1 = nodes[(i + 1) % n_nodes]
            # 使用 (n0.id, n1.id) 作为键避免重复绘制
            seg_key = (min(n0.id(), n1.id()), max(n0.id(), n1.id()))
            if seg_key not in drawn_segments:
                drawn_segments.add(seg_key)
                ax.plot([n0.pos().x(), n1.pos().x()],
                        [n0.pos().y(), n1.pos().y()],
                        color=color, linewidth=linewidth)


def draw_landfill_polygon(ax, polygon, color='red', markersize=8):
    """
    绘制填埋场梯形轮廓

    参数:
        ax: matplotlib axes
        polygon: [[x,y], ...] 顶点列表
        color: 顶点颜色
        markersize: 顶点大小
    """
    # 绘制边界线
    x_coords = [p[0] for p in polygon] + [polygon[0][0]]
    y_coords = [p[1] for p in polygon] + [polygon[0][1]]
    ax.plot(x_coords, y_coords, 'r-', linewidth=1.5)

    # 标注顶点
    labels = ['D', 'C', 'B', 'A']
    for i, (x, y) in enumerate(polygon):
        ax.plot(x, y, 'ro', markersize=markersize)
        ax.text(x + 1, y + 0.5, labels[i], fontsize=12, color='red', fontweight='bold')


def plot_forward_mesh(mesh, scheme, filename='results/dd_forward_mesh.png'):
    """
    绘制正演网格图

    参数:
        mesh: 正演网格 (pg.Mesh)
        scheme: 测量方案
        filename: 输出文件名
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 5))

    # 绘制网格边界
    draw_mesh_boundaries(ax, mesh, color='blue', linewidth=0.3)

    # 绘制填埋场轮廓
    draw_landfill_polygon(ax, landfill_polygon)

    # 绘制电极位置
    for i, p in enumerate(scheme.sensors()):
        ax.plot(p.x(), p.y(), 'k.', markersize=6)
        ax.text(p.x(), p.y() + 0.3, str(i+1), fontsize=6, ha='center')

    # 设置坐标范围
    ax.set_xlim(world_start[0] - 5, world_end[0] + 5)
    ax.set_ylim(world_end[1] - 5, world_start[1] + 2)

    ax.set_title('Forward Mesh (DD Dipole-Dipole)', fontsize=14)
    ax.set_xlabel('x (m)', fontsize=12)
    ax.set_ylabel('y (m)', fontsize=12)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)

    # 添加图例说明
    ax.plot([], [], 'b-', linewidth=0.3, label='Mesh boundaries')
    ax.plot([], [], 'r-', linewidth=1.5, label='Landfill outline')
    ax.plot([], [], 'ro', markersize=8, label='Vertices')
    ax.plot([], [], 'k.', markersize=6, label='Electrodes')
    ax.legend(loc='upper right', fontsize=8)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    fig.savefig(filename, dpi=150)
    logger.debug("Saved forward mesh: %s", filename)
    plt.close()


def plot_inverted_mesh(meshPD, scheme, filename='results/dd_inverted_mesh.png'):
    """
    绘制反演网格图 (paraDomain)

    参数:
        meshPD: 参数化域网格 (pg.Mesh)
        scheme: 测量方案
        filename: 输出文件名
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 5))

    # 通过遍历 cells 绘制 paraDomain 网格
    draw_mesh_cells(ax, meshPD, color='green', linewidth=0.5)

    # 绘制填埋场轮廓
    draw_landfill_polygon(ax, landfill_polygon)

    # 绘制电极位置
    for i, p in enumerate(scheme.sensors()):
        ax.plot(p.x(), p.y(), 'k.', markersize=6)
        ax.text(p.x(), p.y() + 0.3, str(i+1), fontsize=6, ha='center')

    # 设置坐标范围 - 使用 paraDomain 的范围
    ax.set_xlim(meshPD.xmin() - 2, meshPD.xmax() + 2)
    ax.set_ylim(meshPD.ymin() - 2, meshPD.ymax() + 2)

    ax.set_title('Inverted Mesh (paraDomain)', fontsize=14)
    ax.set_xlabel('x (m)', fontsize=12)
    ax.set_ylabel('y (m)', fontsize=12)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)

    # 添加图例说明
    ax.plot([], [], 'g-', linewidth=0.5, label='paraDomain cells')
    ax.plot([], [], 'r-', linewidth=1.5, label='Landfill outline')
    ax.plot([], [], 'ro', markersize=8, label='Vertices')
    ax.plot([], [], 'k.', markersize=6, label='Electrodes')
    ax.legend(loc='upper right', fontsize=8)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    fig.savefig(filename, dpi=150)
    logger.debug("Saved inverted mesh: %s", filename)
    plt.close()


def plot_combined_mesh(mesh, meshPD, scheme, filename='results/dd_combined_mesh.png'):
    """
    绘制组合网格图 (Forward + Inverted 上下排列)

    参数:
        mesh: 正演网格 (pg.Mesh)
        meshPD: 参数化域网格 (pg.Mesh)
        scheme: 测量方案
        filename: 输出文件名
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    # 上图: Forward Mesh
    ax = axes[0]
    draw_mesh_boundaries(ax, mesh, color='blue', linewidth=0.3)
    draw_landfill_polygon(ax, landfill_polygon)
    for i, p in enumerate(scheme.sensors()):
        ax.plot(p.x(), p.y(), 'k.', markersize=6)
        ax.text(p.x(), p.y() + 0.3, str(i+1), fontsize=6, ha='center')
    ax.set_xlim(world_start[0] - 5, world_end[0] + 5)
    ax.set_ylim(world_end[1] - 5, world_start[1] + 2)
    ax.set_title('Forward Mesh (DD Dipole-Dipole)', fontsize=14)
    ax.set_xlabel('x (m)', fontsize=12)
    ax.set_ylabel('y (m)', fontsize=12)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.plot([], [], 'b-', linewidth=0.3, label='Mesh boundaries')
    ax.plot([], [], 'r-', linewidth=1.5, label='Landfill outline')
    ax.plot([], [], 'ro', markersize=8, label='Vertices')
    ax.plot([], [], 'k.', markersize=6, label='Electrodes')
    ax.legend(loc='upper right', fontsize=8)

    # 下图: Inverted Mesh (paraDomain)
    ax = axes[1]
    draw_mesh_cells(ax, meshPD, color='green', linewidth=0.5)
    draw_landfill_polygon(ax, landfill_polygon)
    for i, p in enumerate(scheme.sensors()):
        ax.plot(p.x(), p.y(), 'k.', markersize=6)
        ax.text(p.x(), p.y() + 0.3, str(i+1), fontsize=6, ha='center')
    ax.set_xlim(meshPD.xmin() - 2, meshPD.xmax() + 2)
    ax.set_ylim(meshPD.ymin() - 2, meshPD.ymax() + 2)
    ax.set_title('Inverted Mesh (paraDomain)', fontsize=14)
    ax.set_xlabel('x (m)', fontsize=12)
    ax.set_ylabel('y (m)', fontsize=12)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.plot([], [], 'g-', linewidth=0.5, label='paraDomain cells')
    ax.plot([], [], 'r-', linewidth=1.5, label='Landfill outline')
    ax.plot([], [], 'ro', markersize=8, label='Vertices')
    ax.plot([], [], 'k.', markersize=6, label='Electrodes')
    ax.legend(loc='upper right', fontsize=8)

    plt.tight_layout()

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    fig.savefig(filename, dpi=150)
    logger.debug("Saved combined mesh: %s", filename)
    plt.close()


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=" * 60)
    logger.info("DD ERT Mesh Visualization")
    logger.info("=" * 60)

    # 1. 创建几何和网格
    logger.info("[1] Creating geometry...")
    geom, world, landfill = create_geometry()

    # 2. 创建测量方案
    logger.info("[2] Creating scheme...")
    scheme, elecs = create_scheme()
    logger.info("    Electrodes: %d", len(elecs))

    # 3. 在电极位置添加节点
    for p in scheme.sensors():
        geom.createNode(p)
        geom.createNode(p - [0, 0.1])

    # 4. 创建正演网格
    logger.info("[3] Creating forward mesh...")
    mesh = mt.createMesh(geom, quality=34)
    logger.info("    Forward mesh: %d cells, %d nodes", mesh.cellCount(), mesh.nodeCount())

    # 5. 创建电阻率模型
    logger.info("[4] Creating resistivity model...")
    rho = create_resistivity_model(mesh)

    # 6. 运行正演和反演以获取 paraDomain
    logger.info("[5] Running forward simulation...")
    forward_result = forward_simulation(mesh, scheme, rho)
    rhoa, k, a, b, m, n = forward_result

    logger.info("[6] Running inversion...")
    mgr, inv = run_inversion(rhoa, k, a, b, m, n, scheme)
    meshPD = pg.Mesh(mgr.paraDomain)
    logger.info("    paraDomain: %d cells, %d nodes", meshPD.cellCount(), meshPD.nodeCount())

    # 7. 绘制网格图
    logger.info("[7] Saving mesh visualizations...")

    plot_forward_mesh(mesh, scheme, 'results/dd_forward_mesh.png')
    logger.info("    Saved: results/dd_forward_mesh.png")

    plot_inverted_mesh(meshPD, scheme, 'results/dd_inverted_mesh.png')
    logger.info("    Saved: results/dd_inverted_mesh.png")

    plot_combined_mesh(mesh, meshPD, scheme, 'results/dd_combined_mesh.png')
    logger.info("    Saved: results/dd_combined_mesh.png")

    logger.info("Done!")
