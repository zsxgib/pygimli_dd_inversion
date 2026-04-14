# -*- coding: utf-8 -*-
"""
物理参数配置
"""

# ========== 电阻率参数 ==========
background_resistivity = 100.0  # 背景电阻率 (Ohm·m)
membrane_resistivity = 500.0    # 膜电阻
landfill_resistivity = 200.0    # landfill基础电阻
leak_resistivity = 10.0         # 渗漏低电阻

# ========== 渗漏参数 ==========
leak_x = 30.0                   # 渗漏点x (pyGIMLi坐标)
leak_y = -10.0                  # 渗漏点y (pyGIMLi坐标，0=地表，-10=膜底)
leak_width = 5.0                # 渗漏宽度
leak_depth = 2.0                # 渗漏深度

# ========== 电极参数 ==========
n_elecs = 41                    # 电极数量

# ========== 网格参数 ==========
world_start = [-15, 0]
world_end = [115, -15]

# ========== 梯形填埋场几何 ==========
# 梯形顶点: D(0,0), C(100,0), B(90,-10), A(10,-10)
landfill_polygon = [[0.0, 0.0], [100.0, 0.0], [90.0, -10.0], [10.0, -10.0]]
