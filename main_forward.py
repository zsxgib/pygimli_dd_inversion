# -*- coding: utf-8 -*-
"""
正演主程序

运行正演模拟，保存结果到文件
"""

import os
import json
from datetime import datetime
import logging

import numpy as np

# 配置日志
script_dir = os.path.dirname(os.path.abspath(__file__))
today = datetime.now().strftime('%Y%m%d')
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_dir = os.path.join(script_dir, 'logs', today)
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'dd_forward_{timestamp}.log')

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.handlers = []

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
root_logger.addHandler(stream_handler)

file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)

os.chdir(script_dir)

from forward import create_geometry, create_scheme, create_resistivity_model, forward_simulation
from visualization import plot_true_model
from configs.physical_params import (
    leak_x, leak_y, leak_width, leak_depth,
    background_resistivity, membrane_resistivity,
    landfill_resistivity, leak_resistivity,
    world_start, world_end, landfill_polygon
)


def main():
    """正演主程序"""
    logger.info("=" * 60)
    logger.info("DD ERT Forward Simulation")
    logger.info("=" * 60)

    # 1. 创建几何
    logger.debug("[1] Creating geometry...")
    geom, world, landfill = create_geometry()

    # 2. 创建测量方案
    logger.debug("[2] Creating scheme...")
    scheme, elecs = create_scheme()
    logger.debug("Scheme: %d measurements, %d electrodes (Dipole-Dipole)", scheme.size(), scheme.sensorCount())

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

    # 7. 保存正演结果
    logger.debug("[6] Saving forward results...")
    os.makedirs('results/data', exist_ok=True)
    os.makedirs('results/image', exist_ok=True)
    forward_data = {
        'rhoa': rhoa,
        'k': k,
        'a': a,
        'b': b,
        'm': m,
        'n': n,
        'leak_x': leak_x,
        'leak_y': leak_y,
        'leak_width': leak_width,
        'leak_depth': leak_depth,
    }
    forward_file = f'results/data/forward_{timestamp}.npz'
    np.savez(forward_file, **forward_data)
    logger.info("Saved forward data: %s", forward_file)

    # 保存 JSON 版本（可读格式）
    measurements = []
    for i in range(len(rhoa)):
        measurements.append({
            'id': i,
            'timestamp': timestamp,
            'a': int(a[i]),
            'b': int(b[i]),
            'm': int(m[i]),
            'n': int(n[i]),
            'rhoa': round(rhoa[i], 4),
            'k': round(k[i], 4)
        })

    forward_json = {
        'metadata': {
            'n_elecs': len(elecs),
            'n_measurements': len(rhoa),
            'array_type': 'DD',
            'leak_x': float(leak_x),
            'leak_y': float(leak_y),
            'leak_width': float(leak_width),
            'leak_depth': float(leak_depth),
            'electrode_spacing': round((100.0) / (len(elecs) - 1), 4),
        },
        'measurements': measurements
    }
    json_file = f'results/data/forward_{timestamp}.json'
    with open(json_file, 'w') as f:
        json.dump(forward_json, f, indent=2)
    logger.info("Saved forward data (JSON): %s", json_file)

    # 8. 保存电极位置
    elec_file = f'results/data/electrodes_{timestamp}.txt'
    with open(elec_file, 'w') as f:
        for i, p in enumerate(elecs):
            f.write(f"{i} {p.x()} {p.y()} {p.z()}\n")
    logger.info("Saved electrode positions: %s", elec_file)

    # 9. 保存真实模型可视化
    logger.debug("[7] Saving true model visualization...")
    plot_true_model(mesh, rho, scheme, f'results/image/forward_true_model_{timestamp}.png')
    logger.info("Saved: results/image/forward_true_model_%s.png", timestamp)

    logger.info("Forward simulation completed!")
    logger.info("Output files:")
    logger.info("  - %s", forward_file)
    logger.info("  - %s", json_file)
    logger.info("  - %s", elec_file)
    logger.info("  - results/image/forward_true_model_%s.png", timestamp)


if __name__ == '__main__':
    main()
