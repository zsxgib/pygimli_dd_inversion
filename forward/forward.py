# -*- coding: utf-8 -*-
"""
DD ERT 正演模块

Dipole-Dipole 阵列渗漏检测正演
"""

import logging

import numpy as np

import pygimli as pg
import pygimli.meshtools as mt
from pygimli.physics import ert

from configs.physical_params import (
    background_resistivity,
    membrane_resistivity,
    landfill_resistivity,
    leak_resistivity,
    leak_x,
    leak_y,
    leak_width,
    leak_depth,
    n_elecs,
    world_start,
    world_end,
    landfill_polygon,
)

logger = logging.getLogger(__name__)


def is_in_trapezoid(cx, cy):
    """检测是否在梯形填埋场内（独立于 marker）"""
    # 梯形顶点: D(0,0), C(100,0), B(90,-10), A(10,-10)
    # 使用射线法判断点是否在梯形内
    # 上边 y=0, 0<=x<=100
    # 下边 y=-10, 10<=x<=90
    # 左斜边 DA: x + y = 10 (从(0,0)到(10,-10))
    # 右斜边 CB: x - y = 100 (从(100,0)到(90,-10))

    if cy < -10 or cy > 0:
        return False

    if cy == 0:
        # 上边
        return 0 <= cx <= 100
    elif cy == -10:
        # 下边
        return 10 <= cx <= 90
    else:
        # 在上下边之间，检查左右斜边
        # 左斜边: x >= -y (即 x + y >= 0)
        # 右斜边: x <= 100 + y (即 x - y <= 100)
        if cy < 0:
            # 上半部分: 0 <= y < -10 不存在，cy 在 0 到 -10 之间
            # 左边界: x >= -cy (因为 y=-cy 时 x = -cy)
            # 右边界: x <= 100 + cy
            left_bound = -cy  # 当 cy=-5 时，left_bound=5
            right_bound = 100 + cy  # 当 cy=-5 时，right_bound=95
            return left_bound <= cx <= right_bound
        return False


def is_on_membrane(cx, cy):
    """检测是否在膜边界上"""
    # 底边 AB: y=-10, 10<=x<=90
    if abs(cy + 10) < 0.5 and 10 <= cx <= 90:
        return True
    # 左斜边 DA: y = -x + 0 (从D(0,0)到A(10,-10))
    dist_left = abs(cy + cx) / np.sqrt(2)
    if dist_left < 0.5 and -10 <= cy <= 0 and 0 <= cx <= 10:
        return True
    # 右斜边 CB: y = x - 100 (从C(100,0)到B(90,-10))
    dist_right = abs(cy - cx + 100) / np.sqrt(2)
    if dist_right < 0.5 and -10 <= cy <= 0 and 90 <= cx <= 100:
        return True
    return False


def create_geometry():
    """
    创建几何定义

    返回:
        geom: 合并后的几何
        world: 外边界几何
        landfill: 填埋场几何
    """
    # 创建外边界 world
    world = mt.createWorld(start=world_start, end=world_end, worldMarker=True)

    # 创建梯形填埋场 (marker=2)
    landfill = mt.createPolygon(
        landfill_polygon,
        isClosed=True,
        area=0.5,
        marker=2
    )

    # 合并几何定义
    geom = world + landfill

    logger.debug("Geometry created: world + landfill")

    return geom, world, landfill


def create_scheme():
    """
    创建 Dipole-Dipole 测量方案

    返回:
        scheme: 测量方案
        elecs: 电极位置列表
    """
    # 电极均匀分布在填埋场范围内(0到100)
    elec_start = 0.0
    elec_end = 100.0
    spacing = (elec_end - elec_start) / (n_elecs - 1)
    elecs = [pg.RVector3(elec_start + i * spacing, 0.0, 0.0) for i in range(n_elecs)]
    scheme = ert.createData(elecs=elecs, schemeName='dd')

    logger.debug("Electrode spacing: %.2f (range: %.1f to %.1f)", spacing, elec_start, elec_end)

    logger.debug("Scheme created: %d measurements, %d sensors",
                 scheme.size(), scheme.sensorCount())

    return scheme, elecs


def create_resistivity_model(mesh):
    """
    创建电阻率模型

    参数:
        mesh: 网格

    返回:
        rho: 电阻率数组
    """
    # 创建电阻率数组
    rho = np.ones(mesh.cellCount()) * background_resistivity

    # 设置电阻率 - 渗漏区域判断独立于 marker
    for i, cell in enumerate(mesh.cells()):
        center = cell.center()
        cx = center.x()
        cy = center.y()

        # 1. 判断是否在梯形填埋场内（独立于 marker）
        if is_in_trapezoid(cx, cy):
            rho[i] = landfill_resistivity

            # 膜边界
            if is_on_membrane(cx, cy):
                rho[i] = membrane_resistivity

        # 2. 渗漏点 - 椭圆形扩散（独立于 landfill marker）
        dx = cx - leak_x
        dy = leak_y - cy
        ellipse_val = (dx**2) / (leak_width**2) + (dy**2) / (leak_depth**2)
        if ellipse_val < 1.0:
            rho[i] = leak_resistivity

    logger.debug("Resistivity model created: min=%.1f, max=%.1f", rho.min(), rho.max())
    logger.debug("Membrane cells: %d, Leak cells: %d",
                 sum(rho == membrane_resistivity), sum(rho == leak_resistivity))

    return rho


def forward_simulation(mesh, scheme, rho, noise_level=1, noise_abs=1e-6, seed=1337):
    """
    正演模拟

    参数:
        mesh: 网格
        scheme: 测量方案
        rho: 电阻率模型
        noise_level: 噪声水平 (%)
        noise_abs: 绝对噪声
        seed: 随机种子

    返回:
        rhoa: 视电阻率数组
        k: 几何因子数组
        a, b, m, n: 电极索引数组
    """
    logger.debug("=== Forward Simulation ===")
    logger.debug("Method: pyGIMLi ert.simulate (Dipole-Dipole)")
    logger.debug("Noise level: %.1f%%, Noise abs: %.1e, Seed: %d", noise_level, noise_abs, seed)
    logger.debug("Mesh: %d cells", mesh.cellCount())

    data = ert.simulate(
        mesh,
        scheme=scheme,
        res=rho,
        noiseLevel=noise_level,
        noiseAbs=noise_abs,
        seed=seed,
        verbose=False
    )

    pg.info('Simulated rhoa (min/max)', min(data['rhoa']), max(data['rhoa']))

    # 过滤负值
    data.remove(data['rhoa'] < 0)
    pg.info('Filtered rhoa (min/max)', min(data['rhoa']), max(data['rhoa']))

    # 解耦返回数组
    rhoa = np.array(data['rhoa'])
    k = np.array(data['k'])
    a = np.array(data['a'])
    b = np.array(data['b'])
    m = np.array(data['m'])
    n = np.array(data['n'])

    logger.debug("Forward result: %d measurements", len(rhoa))

    return rhoa, k, a, b, m, n
