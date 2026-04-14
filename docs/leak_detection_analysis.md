# 渗漏检测正演问题分析

## 核心问题

当前正演的膜不是边界/mask，只是电阻率参数。

**真正的问题是：`landfill` 多边形 `isClosed=True` 作为了几何边界，截断了网格。**

```python
# inversions/dd_inversion.py
landfill = mt.createPolygon(
    landfill_polygon,
    isClosed=True,  # <-- 这里截断了网格
    area=0.5,
    marker=2
)
```

## 两个项目对比

| 项目 | 膜处理 | 渗漏范围 |
|------|--------|----------|
| **pygimli_dd_inversion** | 膜是 `isClosed=True` 闭合多边形，渗漏无法穿过 | 被 landfill 边界截断 |
| **pole_dipole_leak_detection** | 膜代码注释掉，不作为几何边界 | 渗漏可向下扩散 20m |

## 坐标系对比

| 维度 | pygimli_dd_inversion | pole_dipole_leak_detection |
|------|---------------------|---------------------------|
| x | -15 到 115 | -15 到 115 |
| 垂直 | y: 0 到 -15 | z: -5 到 15 |
| 地表 | y=0 | z=10 |
| 膜底 | y=-10 | z=0 |

## 方案修正

原方案描述不准确。真正的问题不是膜边界，而是 landfill 闭合边界。

| 方案 | 原理 | 可行性 |
|------|------|--------|
| **A. 扩大 world** | 无效，landfill 边界仍会截断 | 不可行 |
| **B. 注释膜边界** | 无效，膜不是问题所在 | 不可行 |
| **C. 分区域建模** | 需要区域间正确连接 | 复杂 |
| **D. landfill 留开口** | 在膜底边留渗漏通道 | 待验证 |
| **E. 改用非闭合 landfill** | 修改 isClosed=False 或分层建模 | 待验证 |

## 结论

需要修改 `create_geometry()` 函数，让渗漏能穿过 landfill 边界向下扩散。
