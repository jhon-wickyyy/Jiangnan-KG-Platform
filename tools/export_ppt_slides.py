# -*- coding: utf-8 -*-
"""把 PPTX 每页导出为 PNG（PowerPoint COM），供视觉复核。

用法：python tools/export_ppt_slides.py [pptx路径] [输出目录] [宽度px]
默认：docs/结项答辩-...（东大模板）.pptx -> docs/ppt_preview_v4/ 宽 1600
"""
import os
import sys
import win32com.client

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PPTX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    BASE, "docs", "结项答辩-江南古典园林空间知识图谱可视化平台（东大模板）.pptx")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "docs", "ppt_preview_v4")
WIDTH = int(sys.argv[3]) if len(sys.argv) > 3 else 1600

os.makedirs(OUT, exist_ok=True)
app = win32com.client.Dispatch("PowerPoint.Application")
try:
    pres = app.Presentations.Open(PPTX, WithWindow=False)
    n = pres.Slides.Count
    for i in range(1, n + 1):
        p = os.path.join(OUT, f"slide{i:02d}.png")
        pres.Slides(i).Export(p, "PNG", WIDTH, 0)
    pres.Close()
    print(f"导出 {n} 页 -> {OUT}")
finally:
    app.Quit()
