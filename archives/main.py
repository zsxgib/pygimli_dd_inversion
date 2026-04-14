# -*- coding: utf-8 -*-
"""
梯形填埋场渗漏检测 ERT 反演 - 主程序
==============================

使用模块化结构：
- configs: 物理参数配置
- inversions: DD 反演逻辑
- visualization: 可视化函数
"""

import os
from datetime import datetime
import logging

import numpy as np

# 配置日志
script_dir = os.path.dirname(os.path.abspath(__file__))
today = datetime.now().strftime('%Y%m%d')
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_dir = os.path.join(script_dir, 'logs', today)
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'dd_f_pygimli_i_ertmanager_{timestamp}.log')

# 设置root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.handlers = []  # Clear any existing handlers

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
root_logger.addHandler(stream_handler)

file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)

# 设置输出目录
os.chdir(script_dir)

import pygimli as pg
from forward import create_geometry, create_scheme, create_resistivity_model, forward_simulation
from inversions import run_inversion, analyze_leak_location
from visualization import plot_true_model, plot_inversion_result, plot_manager_result

from configs.physical_params import (leak_x, leak_y, leak_width, leak_depth,
                                     background_resistivity, membrane_resistivity,
                                     landfill_resistivity, leak_resistivity)


def main():
    """主程序"""
    logger.info("=" * 60)
    logger.info("DD ERT Inversion for Trapezoidal Landfill Leak Detection")
    logger.info("=" * 60)

    # 1. 创建几何
    logger.debug("[1] Creating geometry...")
    geom, world, landfill = create_geometry()

    # 2. 创建测量方案
    logger.debug("[2] Creating scheme...")
    scheme, elecs = create_scheme()
    logger.debug("Scheme: %d measurements, %d electrodes (Dipole-Dipole)", scheme.size(), scheme.sensorCount())
    logger.debug("Array type: Dipole-Dipole (DD)")
    logger.debug("n_elecs: %d, electrode spacing: calculated", len(elecs))

    # 3. 在电极位置添加节点以加密网格
    for p in scheme.sensors():
        geom.createNode(p)
        geom.createNode(p - [0, 0.1])

    # 4. 创建网格
    logger.debug("[3] Creating mesh...")
    import pygimli.meshtools as mt
    mesh = mt.createMesh(geom, quality=34)
    logger.debug("Mesh: %d cells, %d nodes", mesh.cellCount(), mesh.nodeCount())

    # 5. 创建电阻率模型
    logger.debug("[4] Creating resistivity model...")
    rho = create_resistivity_model(mesh)
    logger.debug("Resistivity model: background=%.1f, membrane=%.1f, landfill=%.1f, leak=%.1f",
                 background_resistivity, membrane_resistivity, landfill_resistivity, leak_resistivity)
    logger.debug("Leak location: x=%.1f, y=%.1f, width=%.1f, depth=%.1f",
                 leak_x, leak_y, leak_width, leak_depth)

    # 6. 正演模拟
    logger.debug("[5] Running forward simulation...")
    rhoa, k, a, b, m, n = forward_simulation(mesh, scheme, rho)

    # 7. 运行反演
    logger.debug("[6] Running inversion...")
    mgr, inv = run_inversion(rhoa, k, a, b, m, n, scheme)

    # 8. 保存正演结果到 results/
    logger.debug("[7] Saving forward results to results/...")
    os.makedirs('results', exist_ok=True)
    np.savez('results/forward_result.npz', rhoa=rhoa, k=k, a=a, b=b, m=m, n=n)
    logger.debug("Saved: results/forward_result.npz")

    # 9. 可视化结果到 results/
    logger.debug("[8] Saving visualizations to results/...")
    plot_true_model(mesh, rho, scheme, 'results/trapezoid_leak_true_model.png')
    logger.debug("Saved: results/trapezoid_leak_true_model.png")

    meshPD = pg.Mesh(mgr.paraDomain)
    plot_inversion_result(meshPD, inv, scheme, 'results/trapezoid_leak_inversion_result.png')
    logger.debug("Saved: results/trapezoid_leak_inversion_result.png")

    plot_manager_result(mgr, inv, scheme, 'results/trapezoid_leak_manager_result.png')
    logger.debug("Saved: results/trapezoid_leak_manager_result.png")

    # 10. 分析渗漏位置
    logger.debug("[9] Analyzing leak location...")
    leak_x_est, leak_y_est = analyze_leak_location(mgr, inv)
    logger.info("=== Leak Location Analysis ===")
    logger.info("True leak: x=%.1f, y=%.1f", leak_x, leak_y)
    logger.info("Estimated leak: x=%.2f, y=%.2f", leak_x_est, leak_y_est)
    logger.debug("ParaDomain y range: %.2f to %.2f", mgr.paraDomain.ymin(), mgr.paraDomain.ymax())

    logger.info("Done!")


if __name__ == '__main__':
    main()
