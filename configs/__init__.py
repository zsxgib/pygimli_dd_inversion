# -*- coding: utf-8 -*-
"""
配置模块
"""

from .physical_params import (
    background_resistivity,
    membrane_resistivity,
    landfill_resistivity,
    leak_resistivity,
    leak_x,
    leak_y,
    leak_width,
    leak_depth,
    n_elecs,
)

__all__ = [
    'background_resistivity',
    'membrane_resistivity',
    'landfill_resistivity',
    'leak_resistivity',
    'leak_x',
    'leak_y',
    'leak_width',
    'leak_depth',
    'n_elecs',
]
