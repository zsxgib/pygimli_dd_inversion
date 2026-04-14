# -*- coding: utf-8 -*-
"""
反演主程序

从正演结果文件读取数据，运行反演
"""

import os
import sys
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
log_file = os.path.join(log_dir, f'dd_inversion_{timestamp}.log')

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

import pygimli as pg
from inversions import run_inversion, analyze_leak_location
from visualization import plot_inversion_result, plot_manager_result
from configs.physical_params import leak_x, leak_y


def load_forward_data(forward_file):
    """加载正演结果（JSON格式）"""
    with open(forward_file, 'r') as f:
        data = json.load(f)

    # 转换为 numpy 数组
    measurements = data['measurements']
    n = len(measurements)
    return {
        'rhoa': np.array([m['rhoa'] for m in measurements]),
        'k': np.array([m['k'] for m in measurements]),
        'a': np.array([m['a'] for m in measurements], dtype=int),
        'b': np.array([m['b'] for m in measurements], dtype=int),
        'm': np.array([m['m'] for m in measurements], dtype=int),
        'n': np.array([m['n'] for m in measurements], dtype=int),
    }


def load_electrodes(elec_file):
    """加载电极位置"""
    elecs = []
    with open(elec_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            idx, x, y, z = int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
            elecs.append(pg.RVector3(x, y, z))
    return elecs


def main():
    """反演主程序"""
    logger.info("=" * 60)
    logger.info("DD ERT Inversion")
    logger.info("=" * 60)

    # 检查命令行参数
    if len(sys.argv) < 2:
        # 查找最新的正演结果（优先 JSON）
        results_dir = 'results/data'
        forward_files = [f for f in os.listdir(results_dir) if f.startswith('forward_') and f.endswith('.json') and 'result' not in f]
        if not forward_files:
            logger.error("No forward result files found. Run main_forward.py first.")
            return
        forward_files.sort()
        forward_file = os.path.join(results_dir, forward_files[-1])
        logger.info("No input file specified, using latest: %s", forward_file)
    else:
        forward_file = sys.argv[1]
        if not os.path.exists(forward_file):
            logger.error("File not found: %s", forward_file)
            return

    # 提取 timestamp
    basename = os.path.basename(forward_file)
    timestamp_str = basename.replace('forward_', '').replace('.json', '')

    # 加载电极位置文件
    elec_file = f'results/data/electrodes_{timestamp_str}.txt'
    if not os.path.exists(elec_file):
        logger.error("Electrode file not found: %s", elec_file)
        return

    # 1. 加载数据
    logger.debug("[1] Loading forward data from: %s", forward_file)
    forward_data = load_forward_data(forward_file)
    rhoa = forward_data['rhoa']
    k = forward_data['k']
    a = forward_data['a']
    b = forward_data['b']
    m = forward_data['m']
    n = forward_data['n']
    logger.debug("Loaded %d measurements", len(rhoa))

    # 2. 重建测量方案
    logger.debug("[2] Reconstructing scheme from electrodes...")
    elecs = load_electrodes(elec_file)
    from pygimli.physics import ert
    scheme = ert.createData(elecs=elecs, schemeName='dd')
    logger.debug("Scheme: %d measurements, %d electrodes", scheme.size(), scheme.sensorCount())

    # 3. 运行反演
    logger.debug("[3] Running inversion...")
    mgr, inv = run_inversion(rhoa, k, a, b, m, n, scheme)

    # 4. 保存反演结果可视化
    logger.debug("[4] Saving inversion visualizations...")
    meshPD = pg.Mesh(mgr.paraDomain)

    plot_inversion_result(meshPD, inv, scheme, f'results/image/inversion_result_{timestamp_str}.png')
    logger.info("Saved: results/image/inversion_result_%s.png", timestamp_str)

    plot_manager_result(mgr, inv, scheme, f'results/image/inversion_manager_result_{timestamp_str}.png')
    logger.info("Saved: results/image/inversion_manager_result_%s.png", timestamp_str)

    # 5. 分析渗漏位置
    logger.debug("[5] Analyzing leak location...")
    leak_x_est, leak_y_est = analyze_leak_location(mgr, inv)
    logger.info("=== Leak Location Analysis ===")
    logger.info("True leak: x=%.1f, y=%.1f", leak_x, leak_y)
    logger.info("Estimated leak: x=%.2f, y=%.2f", leak_x_est, leak_y_est)
    logger.debug("ParaDomain y range: %.2f to %.2f", mgr.paraDomain.ymin(), mgr.paraDomain.ymax())

    logger.info("Inversion completed!")
    logger.info("Output files:")
    logger.info("  - results/image/inversion_result_%s.png", timestamp_str)
    logger.info("  - results/image/inversion_manager_result_%s.png", timestamp_str)


if __name__ == '__main__':
    main()
