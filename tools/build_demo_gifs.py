# -*- coding: utf-8 -*-
"""把 capture-demo-gifs.mjs 采集的逐帧截图合成演示 GIF（无限循环，PPT 放映时自动播放）。

用法：python -I tools/build_demo_gifs.py
输入：frontend/scripts/_gif_frames/gifN_fXX.png + durations.json
输出：docs/ppt_screenshots/demo-gif1-畅园空间布局.gif 等 4 个
"""
import json
import os

from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = os.path.join(BASE, "frontend", "scripts", "_gif_frames")
OUT = os.path.join(BASE, "docs", "ppt_screenshots")

NAMES = {
    "gif1": "demo-gif1-畅园空间布局.gif",
    "gif2": "demo-gif2-游线播放.gif",
    "gif3": "demo-gif3-空间关系筛选.gif",
    "gif4": "demo-gif4-路径查询.gif",
}

durs = json.load(open(os.path.join(FRAMES, "durations.json"), encoding="utf-8"))
for gif, out_name in NAMES.items():
    frames = sorted(f for f in os.listdir(FRAMES) if f.startswith(f"{gif}_f"))
    imgs = []
    for f in frames:
        im = Image.open(os.path.join(FRAMES, f)).convert("RGB")
        # 统一降到 1100 宽（4:3 内容占多数时为 1100×619），控制 GIF 体积
        w = 1100
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
        imgs.append(im)
    durations = durs.get(gif) or [1000] * len(imgs)
    assert len(durations) == len(imgs), f"{gif}: 时长与帧数不一致"
    out = os.path.join(OUT, out_name)
    imgs[0].save(
        out, save_all=True, append_images=imgs[1:],
        duration=durations, loop=0, optimize=True, quality=80,
    )
    print(f"{out_name}: {len(imgs)} 帧, {os.path.getsize(out) // 1024} KB, "
          f"总时长 {sum(durations) / 1000:.1f}s")
