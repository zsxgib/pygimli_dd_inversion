# -*- coding: utf-8 -*-
"""
模型可视化模块
"""

import logging

import matplotlib.pyplot as plt
import pygimli as pg

logger = logging.getLogger(__name__)


def plot_true_model(mesh, rho, scheme, filename='trapezoid_leak_true_model.png'):
    """
    绘制真实电阻率模型

    参数:
        mesh: 真实模型网格
        rho: 电阻率数组
        scheme: 测量方案
        filename: 输出文件名
    """
    # 填埋场区域: x=-5到105(width=110), y=-15到2(height=17)
    # 调整figsize以匹配区域比例，减少空白
    fig, ax = plt.subplots(1, 1, figsize=(11, 3.4))

    ax, cbar = pg.show(
        mesh,
        data=rho,
        hold=True,
        ax=ax,
        cMap="Spectral_r",
        logScale=True,
        orientation="vertical",
        cMin=10,
        cMax=500
    )
    ax.set_title(f"True model (leak at x=50, y=-5)")
    ax.set_xlim(-5, 105)
    ax.set_ylim(-15, 2)
    for p in scheme.sensors():
        ax.plot(p.x(), p.y(), 'r.', markersize=8)
    fig.savefig(filename, dpi=150)
    plt.close()

    logger.debug("Saved true model: %s", filename)


def plot_inversion_result(meshPD, inv, scheme, filename='trapezoid_leak_inversion_result.png'):
    """
    绘制反演结果

    参数:
        meshPD: 参数化域网格
        inv: 反演结果
        scheme: 测量方案
        filename: 输出文件名
    """
    fig, ax = plt.subplots(1, 1, figsize=(11, 3.4))

    ax, cbar = pg.show(
        meshPD,
        inv,
        hold=True,
        ax=ax,
        cMap="Spectral_r",
        logScale=True,
        orientation="vertical",
        cMin=10,
        cMax=500
    )
    ax.set_title("Inversion result")
    ax.set_xlim(-5, 105)
    ax.set_ylim(-15, 2)
    for p in scheme.sensors():
        ax.plot(p.x(), p.y(), 'r.', markersize=8)
    fig.savefig(filename, dpi=150)
    plt.close()

    logger.debug("Saved inversion result: %s", filename)


def plot_manager_result(mgr, inv, scheme, filename='trapezoid_leak_manager_result.png'):
    """
    绘制 ERTManager paraModel 结果

    参数:
        mgr: ERTManager
        inv: 反演结果
        scheme: 测量方案
        filename: 输出文件名
    """
    meshPD = pg.Mesh(mgr.paraDomain)
    modelPD = mgr.paraModel(inv)

    fig, ax = plt.subplots(1, 1, figsize=(11, 3.4))

    ax, cbar = pg.show(
        meshPD,
        modelPD,
        hold=True,
        ax=ax,
        cMap="Spectral_r",
        logScale=True,
        orientation="vertical",
        cMin=10,
        cMax=500
    )
    ax.set_title("ERTManager result (paraModel)")
    ax.set_xlim(-5, 105)
    ax.set_ylim(-15, 2)
    for p in scheme.sensors():
        ax.plot(p.x(), p.y(), 'r.', markersize=8)
    fig.savefig(filename, dpi=150)
    plt.close()
