# -*- coding: utf-8 -*-
"""v4.0 素材准备：① 测绘 PDF 转 PNG ② 候选照片降采样预览 ③ CSV 属性表渲染成图。

产物：
- docs/ppt_assets_v4/  —— 最终嵌入 PPT 的成品图
- /tmp/ppt_previews/    —— 供人工挑选的小预览图
用法：python tools/prep_ppt_assets_v4.py [--preview-only]
"""
import os
import sys
import csv

import fitz  # pymupdf
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None  # 02/ 目录为超高分辨率扫描（~7 亿像素），需放开限制

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRTP = r"C:\Users\jhon.wick\Desktop\srtp"
OUT = os.path.join(BASE, "docs", "ppt_assets_v4")
PREV = os.path.join(os.environ.get("TEMP", "/tmp"), "ppt_previews")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREV, exist_ok=True)

# ---------- ① 测绘 PDF 转 PNG ----------
PDFS = {
    "survey_canglangting": os.path.join(SRTP, "01", "沧浪亭", "01门厅、藕花水榭、面水轩及复廊平面.pdf"),
}

def pdf_to_png(key, pdf_path, max_w=1800):
    doc = fitz.open(pdf_path)
    print(f"[PDF] {key}: {len(doc)} 页, 尺寸 {doc[0].rect.width:.0f}x{doc[0].rect.height:.0f}")
    for i, page in enumerate(doc):
        zoom = min(3.0, max_w / page.rect.width * 72 / 72)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        p = os.path.join(PREV if i else OUT, f"{key}_p{i + 1}.png")
        pix.save(p)
        print(f"  p{i + 1} -> {p}")
    doc.close()

# ---------- ② 候选照片降采样 ----------
PHOTOS = {
    # 实体照片候选：建筑 / 山石 / 池沼 / 花木
    "photo_canglangting": os.path.join(SRTP, "02", "沧浪亭.jpg"),
    "photo_huanxiu_rockery": os.path.join(SRTP, "02", "环秀山庄.jpg"),
    "photo_geyuan": os.path.join(SRTP, "02", "个园.jpg"),
    "photo_heyuan": os.path.join(SRTP, "02", "何园.jpg"),
    "photo_changyuan": os.path.join(SRTP, "02", "畅园.jpg"),
    "photo_shizilin": os.path.join(SRTP, "03", "狮子林.jpg"),
    "photo_ouyuan": os.path.join(SRTP, "03", "耦园.jpg"),
    "photo_ouyuan_east": os.path.join(SRTP, "03", "耦园东花园.jpg"),
    "photo_liuyuan": os.path.join(SRTP, "02", "留园.jpg"),
    # 文献截图候选（复道回廊空间句法）
    "paper_fudao": os.path.join(SRTP, "01", "扬州园林复道回廊的空间句法解析——以何园、个园为例_曹玮",
                                "扬州园林复道回廊的空间句法解析——以何园、个园为例_曹玮_03.jpg"),
    # CAD 平面图（对照页）
    "cad_canglangting": os.path.join(SRTP, "0010-CAD苏州古典园林平面图", "古典园林平面", "沧浪亭.jpg"),
    "cad_shizilin": os.path.join(SRTP, "0010-CAD苏州古典园林平面图", "古典园林平面", "狮子林.jpg"),
    "cad_zhuozhengyuan": os.path.join(SRTP, "0010-CAD苏州古典园林平面图", "古典园林平面", "拙政园.JPG"),
}

def downscale(key, path, max_w=640, to_out=False):
    if not os.path.exists(path):
        print(f"[缺] {key}: {path}")
        return
    im = Image.open(path).convert("RGB")
    w, h = im.size
    nw = min(max_w, w)
    nh = round(h * nw / w)
    im = im.resize((nw, nh), Image.LANCZOS)
    dest = os.path.join(OUT if to_out else PREV, key + ".png")
    im.save(dest)
    print(f"[图] {key}: 原 {w}x{h} -> {nw}x{nh} ({'成品' if to_out else '预览'})")

# ---------- ③ CSV 属性表渲染 ----------
def render_csv(key, csv_path, max_w=1500, title=None):
    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    rows = [r for r in rows if any(c.strip() for c in r)]
    font = None
    for fp in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"):
        if os.path.exists(fp):
            font = fp
            break
    # 先画到临时大图再缩放到 max_w
    f_hdr, f_cell = ImageFont.truetype(font, 34), ImageFont.truetype(font, 30)
    pad, col_pad, row_h = 24, 20, 46
    ncol = max(len(r) for r in rows)
    widths = []
    for c in range(ncol):
        wmax = 0
        for r in rows:
            t = r[c] if c < len(r) else ""
            f = f_hdr if r is rows[0] else f_cell
            wmax = max(wmax, f.getbbox(t)[2])
        widths.append(wmax + col_pad * 2)
    tw = sum(widths)
    th = row_h * len(rows) + pad * 2 + (row_h if title else 0)
    img = Image.new("RGB", (tw, th), "#F3EFE8")
    dr = ImageDraw.Draw(img)
    y = pad
    if title:
        f_t = ImageFont.truetype(font, 42)
        dr.text((pad, y), title, font=f_t, fill="#231815")
        y += row_h + 14
    for ri, r in enumerate(rows):
        x = pad
        for c in range(ncol):
            t = r[c] if c < len(r) else ""
            f = f_hdr if ri == 0 else f_cell
            dr.text((x + col_pad, y + 6), t, font=f,
                    fill="#8A7352" if ri == 0 else "#231815")
            x += widths[c]
        if ri == 0:
            y += row_h
            dr.line([(pad, y), (tw - pad, y)], fill="#AB8F6A", width=2)
        y += row_h
    scale = min(1.0, max_w / tw)
    img = img.resize((round(tw * scale), round(th * scale)), Image.LANCZOS)
    dest = os.path.join(OUT, key + ".png")
    img.save(dest)
    print(f"[表] {key}: {len(rows)} 行 x {ncol} 列 -> {img.size}")

# ---------- 主流程 ----------
if __name__ == "__main__":
    only_preview = "--preview-only" in sys.argv
    if not only_preview:
        for k, p in PDFS.items():
            pdf_to_png(k, p)
        render_csv("table_jichangyuan_buildings", os.path.join(SRTP, "08", "1-1建筑属性表.csv"),
                   title="寄畅园建筑属性表（节选 · 数据来源示例）")
    for k, p in PHOTOS.items():
        downscale(k, p)
    # 成品版（挑定后再生成）——先全部生成预览，成品由下一脚本按挑选结果生成
    print("完成。预览目录:", PREV)
