# -*- coding: utf-8 -*-
"""
DD ERT 反演模块

Dipole-Dipole 阵列渗漏检测反演
"""

import logging

import numpy as np

import pygimli as pg
from pygimli.physics import ert

logger = logging.getLogger(__name__)


def run_inversion(rhoa, k, a, b, m, n, scheme, lam=20, z_weight=0.3, max_iter=50):
    """
    运行反演

    参数:
        rhoa: 视电阻率数组
        k: 几何因子数组
        a, b, m, n: 电极索引数组
        scheme: 测量方案（用于重建传感器位置）
        lam: 正则化参数
        z_weight: z方向权重
        max_iter: 最大迭代次数

    返回:
        mgr: ERTManager
        inv: 反演结果
    """
    logger.debug("=== Inversion ===")
    logger.debug("Method: pyGIMLi ERTManager.invert")
    logger.debug("paraDepth: 20, paraMaxCellSize: 1")
    logger.debug("startModel: 500.0, lam: %d, zWeight: %.1f, maxIter: %d", lam, z_weight, max_iter)

    # 重建 DataContainerERT
    data = pg.DataContainerERT()
    # 从scheme复制传感器位置
    for p in scheme.sensors():
        data.createSensor(p)
    # 设置测量数据
    n_data = len(rhoa)
    data.resize(n_data)
    data.set('a', pg.Vector(a))
    data.set('b', pg.Vector(b))
    data.set('m', pg.Vector(m))
    data.set('n', pg.Vector(n))
    data.set('rhoa', pg.Vector(rhoa))
    data.set('k', pg.Vector(k))
    data.set('valid', pg.Vector(n_data, 1.0))
    # 设置误差（相对误差）
    data.set('err', pg.Vector(n_data, 0.01))  # 1% 相对误差

    mgr = ert.ERTManager(data, verbose=False)
    mgr.createMesh(data, paraDepth=20, paraMaxCellSize=1)
    inv = mgr.invert(
        data=data,
        startModel=500.0,
        lam=lam,
        zWeight=z_weight,
        maxIter=max_iter,
        verbose=False
    )

    pg.info('Inversion stopped with chi² = {0:.3}'.format(mgr.fw.chi2()))

    return mgr, inv


def analyze_leak_location(mgr, inv):
    """
    分析渗漏位置

    参数:
        mgr: ERTManager
        inv: 反演结果

    返回:
        leak_x_est: 估计的渗漏x坐标
        leak_y_est: 估计的渗漏y坐标
    """
    modelPD = mgr.paraModel(inv)
    min_idx = np.argmin(modelPD)
    min_cell = mgr.paraDomain.cell(min_idx)
    leak_x_est = min_cell.center().x()
    leak_y_est = min_cell.center().y()

    logger.debug("Leak location estimated: x=%.2f, y=%.2f", leak_x_est, leak_y_est)

    return leak_x_est, leak_y_est
