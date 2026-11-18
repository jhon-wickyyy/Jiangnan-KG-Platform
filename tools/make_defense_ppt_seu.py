# -*- coding: utf-8 -*-
"""基于东南大学科研学术汇报模板生成 SRTP 结项答辩 PPT（v4.2，建筑专业视角表述）。

用法：python tools/make_defense_ppt_seu.py
模板：docs/东南大学科研学术汇报模板.pptx（保留其页面比例/背景/配色/字体/页眉页脚/图形元素）
输出：docs/结项答辩-江南古典园林空间知识图谱可视化平台（东大模板）.pptx
结构：26 页 = 封面 + 目录 + 4 分节页 + 19 内容页 + 致谢
v4.2 变更（案例园林切换为畅园，45 要素 / 130 关系）：① 对照页与空间布局页的沧浪亭 CAD 图换成畅园测绘平面图
    ② 平台截图换畅园版（空间布局 / 节点详情 / 知识关系网络 / 网络分析 / 空间关系分析 / 实体浏览）
    ③ 空间语义 / 空间关系 / 网络分析 / 创新点③等案例表述与实测数字改为畅园（相邻 86 · 相接 44 · 平均关联数 5.76）
    ④ 后端空间关系属性适配畅园字段命名（类型→相邻/接触类型，极径_m→距离_m），空间关系页可用畅园演示
    ⑤ 游线 / 路径两页沿用沧浪亭演示（畅园暂无游线数据）
    ⑥ 实体照片条（建筑/山石/池沼/花木）与第 8 页测绘工作照插入（用户 2026-10-14 提供）
    ⑦ 四个实机演示环节改为录制动图（现场无投屏演示条件）：第 17/19/20/21 页嵌 GIF，放映时自动循环播放
v4.1 变更：数据来源页三张来源实物图 · 实体类别页现状照片条 · 空间布局页 CAD 小对照与大对照页 · 创新点③
表述原则：面向建筑专业评审——以园林/测绘语言表达，避免计算机术语（仅保留 Neo4j 等必要工具名）
数据：全部为对运行中平台实测（tools/verify_ppt_facts.py → docs/_ppt_facts.json）
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from PIL import Image
import os
import time

# ---------- 主题（全部取自模板配色：米金 AB8F6A / 深棕 231815 / 灰绿 587558 系） ----------
FONT = "微软雅黑"
DARK = "231815"      # 深棕黑（标题/正文）
BRONZE = "AB8F6A"    # 米金（主强调）
BRONZE_D = "8A7352"  # 深米金
SAGE = "587558"      # 灰绿（次强调）
SAGE_L = "799179"    # 浅灰绿
GREY = "6B645D"      # 次要文字（暖灰）
LINE = "DBD2C8"      # 边框/分隔线（米色）
LIGHT = "F3EFE8"     # 浅米底
LIGHT2 = "E9E3D8"    # 稍深米底

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(BASE, "docs", "ppt_screenshots")
TEMPLATE = os.path.join(BASE, "docs", "东南大学科研学术汇报模板.pptx")
OUT = os.path.join(BASE, "docs", "结项答辩-江南古典园林空间知识图谱可视化平台（东大模板）.pptx")
PHOTO = os.path.join(BASE, "images", "微信图片_20261013225745_123_118.png")  # 畅园案例照片（用户 2026-10-13 晚提供）
BG7 = os.path.join(BASE, "images", "lixiang_p7_bg.png")  # 立项 PPT 第 7 页背景图（1874×1122，浅色）

# v4.1 素材（tools/prep_ppt_assets_v4.py 生成）
V4 = os.path.join(BASE, "docs", "ppt_assets_v4")
IMG_SURVEY = os.path.join(V4, "survey_canglangting_p1.png")          # 沧浪亭复廊平面测绘图纸（PDF 首页）
IMG_PAPER = os.path.join(V4, "paper_fudao_full.png")                 # 曹玮复道回廊空间句法论文图
IMG_TABLE = os.path.join(V4, "table_jichangyuan_buildings.png")      # 寄畅园建筑属性表渲染图
IMG_CAD_CY = os.path.join(V4, "cad_changyuan_full.png")              # 畅园测绘平面图（1畅园/畅园.png 降采样白底版）
# 实体照片条（建筑/山石/池沼/花木）——畅园现状照片（用户 2026-10-14 提供，经目测分类）
ENTITY_PHOTOS = [
    os.path.join(V4, "photo_building_changyuan.jpg"),
    os.path.join(V4, "photo_rock_changyuan.jpg"),
    os.path.join(V4, "photo_pond_changyuan.jpg"),
    os.path.join(V4, "photo_plant_changyuan.jpg"),
]
IMG_WORK = os.path.join(V4, "photo_survey_changyuan.jpg")  # 测绘工作照（第 8 页）

# v4.2b：演示动图（tools/build_demo_gifs.py 由实机操作录制，放映时自动循环播放）
GIF_SPATIAL = os.path.join(SHOTS, "demo-gif1-畅园空间布局.gif")   # 第 17 页：畅园空间布局+节点详情+关系模式
GIF_ROUTE = os.path.join(SHOTS, "demo-gif2-游线播放.gif")          # 第 19 页：沧浪亭游线播放
GIF_SP_REL = os.path.join(SHOTS, "demo-gif3-空间关系筛选.gif")     # 第 20 页：畅园筛可看+详情
GIF_PATH = os.path.join(SHOTS, "demo-gif4-路径查询.gif")           # 第 21 页：沧浪亭路径查询

INST_CN = "东南大学建筑学院"
INST_EN = "School of Architecture, SEU"

prs = Presentation(TEMPLATE)
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H

# 删除模板示例页（保留版式）
sldIdLst = prs.slides._sldIdLst
for sldId in list(sldIdLst):
    prs.part.drop_rel(sldId.rId)
    sldIdLst.remove(sldId)

LAY = prs.slide_layouts
L_COVER, L_TOC = 0, 1
L_DIV = {1: 2, 2: 4, 3: 6, 4: 8}
L_CONTENT = {1: 3, 2: 5, 3: 7, 4: 9}

CH = {
    1: "项目背景与目标",
    2: "知识图谱数据库构建",
    3: "可视化平台设计与实现",
    4: "项目成果与展望",
}


# ---------- 基础工具 ----------
def set_font(run, size=14, bold=False, color=DARK, italic=False):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.name = FONT
    f.color.rgb = RGBColor.from_string(color)
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", FONT)


def add_text(slide, x, y, w, h, lines, size=14, color=DARK, bold=False,
             align=PP_ALIGN.LEFT, line_gap=1.12, anchor=MSO_ANCHOR.TOP):
    """lines: str 或 [(text, size, color, bold, align, gap), ...]"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    if isinstance(lines, str):
        lines = [(lines, size, color, bold, align)]
    for i, item in enumerate(lines):
        gap = line_gap
        if isinstance(item, tuple):
            text = item[0]
            sz = item[1] if len(item) > 1 else size
            col = item[2] if len(item) > 2 else color
            bd = item[3] if len(item) > 3 else bold
            al = item[4] if len(item) > 4 else align
            if len(item) > 5:
                gap = item[5]
        else:
            text, sz, col, bd, al = item, size, color, bold, align
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = al
        p.line_spacing = gap
        run = p.add_run()
        run.text = text
        set_font(run, size=sz, bold=bd, color=col)
    return tb


def add_rect(slide, x, y, w, h, fill=None, line=None, line_w=0.75, round_=False):
    shp = MSO_SHAPE.ROUNDED_RECTANGLE if round_ else MSO_SHAPE.RECTANGLE
    sh = slide.shapes.add_shape(shp, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid() if fill else sh.fill.background()
    if fill:
        sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    if line:
        sh.line.color.rgb = RGBColor.from_string(line)
        sh.line.width = Pt(line_w)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    if round_:
        try:
            sh.adjustments[0] = 0.08
        except Exception:
            pass
    return sh


def add_rect_alpha(slide, x, y, w, h, fill="FFFFFF", opacity=82, round_=True):
    """半透明填充圆角矩形（opacity 0-100 为不透明度），用于压图文字面板。"""
    sh = add_rect(slide, x, y, w, h, fill=fill, line=None, round_=round_)
    sF = sh.fill._xPr.find(qn("a:solidFill"))
    clr = sF.find(qn("a:srgbClr"))
    alpha = clr.makeelement(qn("a:alpha"), {"val": str(int(opacity * 1000))})
    clr.append(alpha)
    return sh


def img_size(path):
    with Image.open(path) as im:
        return im.size


def add_image_fit(slide, path, x, y, w, h, border=True):
    """在 (x,y,w,h) 区域内等比缩放居中插入图片，返回实际放置框。"""
    if not os.path.exists(path):
        add_rect(slide, x, y, w, h, fill=LIGHT, line=LINE)
        add_text(slide, x, y, w, h, f"（缺少截图：{os.path.basename(path)}）",
                 size=11, color=GREY, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        return (x, y, w, h)
    pw, ph = img_size(path)
    scale = min(w / pw, h / ph)
    nw, nh = pw * scale, ph * scale
    nx, ny = x + (w - nw) / 2, y + (h - nh) / 2
    if border:
        add_rect(slide, nx - 0.025, ny - 0.025, nw + 0.05, nh + 0.05, fill=None, line=LINE)
    slide.shapes.add_picture(path, Inches(nx), Inches(ny), Inches(nw), Inches(nh))
    return (nx, ny, nw, nh)


def ph_by_pos(slide, x, y, tol=0.2):
    for ph in slide.placeholders:
        if abs(Emu(ph.left).inches - x) < tol and abs(Emu(ph.top).inches - y) < tol:
            return ph
    return None


def set_ph(ph, text, size, bold=False, color=DARK, align=PP_ALIGN.LEFT, line_gap=1.05):
    tf = ph.text_frame
    tf.word_wrap = True
    tf.clear()
    lines = text if isinstance(text, (list, tuple)) else [text]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_gap
        run = p.add_run()
        run.text = ln
        set_font(run, size=size, bold=bold, color=color)


def new_slide(layout_idx):
    return prs.slides.add_slide(LAY[layout_idx])


def content_slide(chapter, page_title, sub_en, page_no, bg_image=None):
    """章节内容页：填好页眉（本页标题 / Chapter N / 章节标题 / 页码）。
    bg_image：可选整页背景图（置于最底层）。"""
    s = new_slide(L_CONTENT[chapter])
    if bg_image and os.path.exists(bg_image):
        # 按高度铺满（图 1874×1122 ≈ 1.67:1，两侧留白与白色边角自然衔接），置于最底层
        pic = s.shapes.add_picture(bg_image, Inches(0.4), Inches(0), Inches(12.52), Inches(7.5))
        move_to_back(s, pic)
    set_ph(s.placeholders[11], page_title, size=13, bold=True, color=DARK)
    set_ph(s.placeholders[12], sub_en, size=9, color=SAGE_L)
    set_ph(s.placeholders[16], CH[chapter], size=10, color=BRONZE_D)
    # 页码：版式自带的徽章大半出血在画面外，改为画面内右下角的灰绿标签（完全在 13.33×7.5 画面内）
    chip(s, 11.95, 7.08, 1.35, 0.42, str(page_no), fill=SAGE, size=11)
    return s


def metric_card(slide, x, y, w, h, value, label, value_color=BRONZE, value_size=30):
    add_rect(slide, x, y, w, h, fill=LIGHT, line=LINE)
    add_rect(slide, x, y, 0.07, h, fill=value_color)
    add_text(slide, x + 0.22, y + 0.08, w - 0.35, h * 0.62, value,
             size=value_size, bold=True, color=value_color)
    add_text(slide, x + 0.22, y + h * 0.62, w - 0.35, h * 0.32, label,
             size=11, color=GREY)


def caption_band(slide, lines, y=6.32, h=0.62, accent=SAGE):
    add_rect(slide, 0.5, y, 12.33, h, fill=LIGHT2, line=LINE, round_=True)
    add_rect(slide, 0.5, y, 0.07, h, fill=accent)
    add_text(slide, 0.75, y + 0.06, 11.9, h - 0.12, lines, size=11.5, color=DARK,
             anchor=MSO_ANCHOR.MIDDLE)


def chip(slide, x, y, w, h, text, fill=BRONZE, color="FFFFFF", size=11):
    add_rect(slide, x, y, w, h, fill=fill, round_=True)
    add_text(slide, x, y, w, h, text, size=size, bold=True, color=color,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def move_to_back(slide, shape):
    """把形状移到页面最底层（背景图用）。"""
    spTree = slide.shapes._spTree
    el = shape._element
    spTree.remove(el)
    spTree.insert(2, el)


def arrow_right(slide, x, y, w=0.34, h=0.42, fill=BRONZE):
    sh = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    sh.line.fill.background()
    sh.shadow.inherit = False


def bar_chart(slide, x, y, w, title, data, bar_color=BRONZE, label_w=1.15, bar_max_w=3.45, row_h=0.34):
    """单色系横向条形图：左侧名称 + 色条 + 直接数值标注（文本用墨色，不用系列色）。"""
    add_text(slide, x, y, w, 0.3, title, size=12.5, bold=True, color=DARK)
    y += 0.38
    vmax = max(v for _, v in data)
    # 基线（弱化的轴线）
    add_rect(slide, x + label_w, y - 0.04, 0.012, row_h * len(data) + 0.1, fill=LINE)
    for i, (name, val) in enumerate(data):
        yy = y + i * row_h
        add_text(slide, x, yy + 0.06, label_w - 0.12, 0.25, name, size=10, color=GREY,
                 align=PP_ALIGN.RIGHT)
        bw = max(bar_max_w * val / vmax, 0.035)
        add_rect(slide, x + label_w + 0.06, yy + 0.07, bw, 0.2, fill=bar_color)
        add_text(slide, x + label_w + 0.12 + bw, yy + 0.055, 0.9, 0.25, str(val),
                 size=10, bold=True, color=DARK)
    return y + row_h * len(data)


# =========================================================
# 第 1 页 封面
# =========================================================
s = new_slide(L_COVER)
set_ph(ph_by_pos(s, 10.19, 0.15), INST_CN, size=10, color=DARK)
set_ph(ph_by_pos(s, 10.20, 0.36), INST_EN, size=9, color=GREY)
set_ph(ph_by_pos(s, 2.07, 2.67), "江南古典园林空间知识图谱可视化平台", size=30, bold=True, color=DARK)
set_ph(ph_by_pos(s, 4.11, 4.26), "SRTP Innovation Training Program · Final Defense", size=11.5, color=BRONZE_D, align=PP_ALIGN.CENTER)
set_ph(ph_by_pos(s, 5.34, 4.83), "汇报人：杨思成", size=15, color=DARK, align=PP_ALIGN.CENTER)
set_ph(ph_by_pos(s, 5.34, 5.41), ["成员：王梓萌、余悦", "导师：邵星宇、王笑"], size=11, color=GREY, align=PP_ALIGN.CENTER)

# =========================================================
# 第 2 页 目录
# =========================================================
s = new_slide(L_TOC)
set_ph(ph_by_pos(s, 0.14, 0.17), INST_CN, size=10, color=DARK)
set_ph(ph_by_pos(s, 0.16, 0.38), INST_EN, size=9, color=GREY)
toc_items = [
    ("01  项目背景与目标", 1.66),
    ("02  知识图谱数据库构建", 2.95),
    ("03  可视化平台设计与实现", 4.29),
    ("04  项目成果与展望", 5.59),
]
for text, y in toc_items:
    set_ph(ph_by_pos(s, 8.9, y), text, size=14, bold=True, color=DARK)

# =========================================================
# 第 3 页 分节页 壹
# =========================================================
s = new_slide(L_DIV[1])
set_ph(ph_by_pos(s, 6.87, 3.28), CH[1], size=22, bold=True, color=DARK)
set_ph(ph_by_pos(s, 10.17, 0.20), INST_CN, size=10, color=DARK)
set_ph(ph_by_pos(s, 10.19, 0.41), INST_EN, size=9, color=GREY)

# =========================================================
# 第 4 页 项目背景与研究意义
# =========================================================
s = content_slide(1, "项目背景与研究意义", "Chapter 01 · Background", 4)
bgs = [
    ("①", "江南古典园林数字化保护需求", "中国古典园林是国家文化自信与文化传承的重要载体；历史变迁中大量名园湮灭或改建，现存园林遗产缺乏整合现状与历史信息的动态数字平台。", BRONZE),
    ("②", "传统园林知识分散问题", "园林知识分散于历史文献、测绘图纸、园林图像等多源资料，表达形式与结构各异；传统的表格式记录难以表达建筑、山水、花木之间复杂的空间与语义关联。", SAGE),
    ("③", "知识图谱与空间可视化技术价值", "以“实体—关系—属性”组织园林知识，结合空间坐标可视化还原园林空间格局；国际同类工作（如意大利 ArCo 文化遗产知识图谱）已验证该路线的有效性。", BRONZE_D),
]
by = 1.35
for num, t, d, c in bgs:
    add_rect(s, 0.5, by, 7.3, 1.35, fill=LIGHT, line=LINE, round_=True)
    chip(s, 0.72, by + 0.4, 0.55, 0.55, num, fill=c, size=16)
    add_text(s, 1.5, by + 0.14, 6.1, 0.45, t, size=15, bold=True, color=DARK)
    add_text(s, 1.5, by + 0.6, 6.1, 0.7, d, size=11, color=GREY, line_gap=1.15)
    by += 1.53
add_image_fit(s, PHOTO, 8.15, 1.35, 4.6, 2.97)
add_text(s, 8.15, 4.42, 4.6, 0.3, "苏州畅园 · 项目实测案例", size=10.5, color=GREY, align=PP_ALIGN.CENTER)
add_rect(s, 8.15, 4.82, 4.6, 1.25, fill=LIGHT2, line=LINE, round_=True)
add_text(s, 8.4, 4.92, 4.15, 1.05, [
    ("研究意义", 12.5, SAGE, True),
    ("为园林遗产“数字化建档—知识检索—空间分析”提供一套可复制的方法与工具，服务教学、研究与公众科普。", 10.5, DARK),
], line_gap=1.25)
caption_band(s, [
    ("提出核心问题：能否利用知识图谱整合多源园林信息，构建服务于数字化保护与研究的空间知识可视化体系？——本项目以 23 园空间知识图谱与可视化平台给出工程化回答。",
     11.5, DARK),
], accent=BRONZE_D)

# =========================================================
# 第 5 页 项目基础与依托课题（忠实还原立项 PPT 第 7 页）
# =========================================================
s = content_slide(1, "项目基础与依托课题", "Chapter 01 · Foundation", 5)
# 左侧：立项第 7 页原图（独立放置，不与文字叠加）
add_image_fit(s, BG7, 0.5, 1.35, 5.9, 3.53)
# 右侧：课题文字
add_text(s, 6.7, 1.5, 6.1, 3.5, [
    ("《人工智能辅助的江南古典园林“文/画/图”复原方法研究》", 14.5, DARK, True),
    ("江苏省自然科学基金项目 · 项目号：BK20241351", 12, BRONZE_D, True),
    ("本项目参与省基金课题中的知识图谱构建部分", 13, DARK, True),
    ("",),
    ("课题测绘（复原）图、本体提炼（建筑 / 水体 / 山体 / 植物）与语义关联（建筑之间、山水要素之间的位置关系）资料是本项目的直接数据来源。", 11, GREY),
], line_gap=1.3)
# 底部三栏：课题已有成果 / 团队基础 / 数据继承
b3 = [
    ("课题已有成果", "archtree01 图文数据集 · SD1.5 LoRA 图像生成测试 · 网师园 / 耦园 / 艺圃 / 瞻园精测资料", BRONZE),
    ("团队基础", "园林史论与案例分析基础 · 多源资料整理能力（文献 / 图像 / 测绘）· 导师“文—画—图”研究积累", SAGE),
    ("数据继承", "课题数据 → 本项目空间知识图谱（23 园），为课题复原研究与后续 AI 应用提供结构化知识底座", BRONZE_D),
]
for (t, d, c), x in zip(b3, [0.5, 4.72, 8.94]):
    add_rect(s, x, 5.15, 3.97, 1.5, fill=LIGHT, line=LINE, round_=True)
    add_rect(s, x, 5.15, 0.07, 1.5, fill=c)
    add_text(s, x + 0.25, 5.27, 3.55, 0.4, t, size=12.5, bold=True, color=DARK)
    add_text(s, x + 0.25, 5.68, 3.55, 0.9, d, size=10.5, color=GREY, line_gap=1.2)

# =========================================================
# 第 6 页 项目研究目标
# =========================================================
s = content_slide(1, "项目研究目标", "Chapter 01 · Objectives", 6)
goals = [
    ("01", "构建空间语义知识图谱", "以实体、关系与空间信息（平面坐标、方位、距离、游线序号）组织园林知识，形成可查询、可计算的空间知识图谱。", BRONZE),
    ("02", "研发可视化交互平台", "面向非计算机背景的使用者提供浏览、搜索、图谱探索与空间分析等 8 个功能页面，降低园林知识获取门槛。", SAGE),
    ("03", "还原空间格局与游览动线", "以真实测绘坐标 1:1 还原园林平面格局，以游线序号数据复原游览动线，支撑园林空间格局研究。", BRONZE_D),
    ("04", "支持多园林动态接入", "一园一库、自动识别：23 个园林数据独立建档、一键切换，新园林数据接入无需改动程序。", SAGE),
]
for (num, t, d, c), (x, y) in zip(goals, [(0.5, 1.45), (6.72, 1.45), (0.5, 3.2), (6.72, 3.2)]):
    add_rect(s, x, y, 6.11, 1.55, fill=LIGHT, line=LINE, round_=True)
    chip(s, x + 0.25, y + 0.47, 0.62, 0.62, num, fill=c, size=15)
    add_text(s, x + 1.1, y + 0.18, 4.85, 0.45, t, size=15, bold=True, color=DARK)
    add_text(s, x + 1.1, y + 0.68, 4.85, 0.8, d, size=11, color=GREY, line_gap=1.15)
add_rect(s, 0.5, 5.05, 12.33, 0.95, fill=LIGHT2, line=LINE, round_=True)
add_rect(s, 0.5, 5.05, 0.07, 0.95, fill=SAGE)
add_text(s, 0.85, 5.12, 11.8, 0.8, [
    ("研究内容：① 数据建模——本体框架与空间语义三层模型（位置层 / 关系层 / 游线层）　② 平台实现——13 项查询功能 + 8 个功能页面　③ 多园验证——23 园数据质量核查与全流程功能核验",
     12, DARK),
], line_gap=1.25, anchor=MSO_ANCHOR.MIDDLE)

# =========================================================
# 第 6 页 总体技术路线
# =========================================================
s = content_slide(1, "总体技术路线", "Chapter 01 · Approach", 7)
steps = [
    ("园林数据", "测绘资料 · 历史文献", BRONZE),
    ("知识图谱构建", "要素 · 关系 · 空间信息建模", SAGE),
    ("Neo4j 数据库", "一园一库 × 23", BRONZE_D),
    ("可视化分析平台", "8 页面 · 13 项查询", SAGE),
]
sx = 0.5
bw, bh = 2.55, 1.6
for i, (t, d, c) in enumerate(steps):
    add_rect(s, sx, 1.4, bw, bh, fill=LIGHT, line=LINE, round_=True)
    add_rect(s, sx, 1.4, bw, 0.12, fill=c)
    add_text(s, sx + 0.15, 1.62, bw - 0.3, 0.45, t, size=15, bold=True, color=DARK, align=PP_ALIGN.CENTER)
    add_text(s, sx + 0.15, 2.18, bw - 0.3, 0.7, d, size=11, color=GREY, align=PP_ALIGN.CENTER, line_gap=1.2)
    if i < 3:
        arrow_right(s, sx + bw + 0.08, 2.0, 0.3, 0.4, fill=c)
    sx += bw + 0.47
add_text(s, 0.5, 3.18, 12.33, 0.55, [
    ("数据加工：本体提炼（建筑 / 水体 / 山体 / 植物）→ 要素识别与关系梳理 → 空间信息录入（坐标 / 方位 / 距离 / 游线序号）",
     11.5, DARK),
], align=PP_ALIGN.CENTER, line_gap=1.25)
add_image_fit(s, os.path.join(SHOTS, "03-architecture.png"), 0.8, 3.85, 11.7, 2.15)
caption_band(s, [
    ("技术实现：网页交互式可视化界面（支持缩放、平移、拖拽）· 轻量数据查询服务 · Neo4j 图数据库存储（一园一库）；平台全程只读，不修改任何原始数据",
     11.5, DARK),
])

# =========================================================
# 第 7 页 分节页 贰
# =========================================================
s = new_slide(L_DIV[2])
set_ph(ph_by_pos(s, 6.87, 3.28), CH[2], size=22, bold=True, color=DARK)
set_ph(ph_by_pos(s, 10.17, 0.20), INST_CN, size=10, color=DARK)
set_ph(ph_by_pos(s, 10.19, 0.41), INST_EN, size=9, color=GREY)

# =========================================================
# 第 8 页 数据来源与数据规模
# =========================================================
s = content_slide(2, "数据来源与数据规模", "Chapter 02 · Data", 9)
cards = [
    ("23", "江南园林数据库（一园一库）"),
    ("718", "实体要素（4 个类别）"),
    ("1905", "关联关系（4 类）"),
    ("9", "园具备完整空间信息"),
]
cx = 0.5
for v, l in cards:
    metric_card(s, cx, 1.3, 2.95, 1.05, v, l)
    cx += 3.12
add_image_fit(s, os.path.join(SHOTS, "04b-garden-table.png"), 0.5, 2.55, 7.0, 3.15)
add_rect(s, 7.8, 2.55, 5.0, 1.75, fill=LIGHT, line=LINE, round_=True)
add_text(s, 8.0, 2.66, 4.6, 1.55, [
    ("数据来源", 13, SAGE, True),
    ("测绘资料 + 历史文献整理：坐标、形制、功能、空间关系、游览环线序号", 10.5, GREY),
    ("",),
    ("数据加工流程", 11.5, BRONZE_D, True),
    ("资料整理 → 本体提炼 → 要素识别 → 关系梳理 → 入库校验", 10.5, GREY),
], line_gap=1.18)
add_rect(s, 7.8, 4.42, 5.0, 1.6, fill=LIGHT, line=LINE, round_=True)
add_text(s, 8.0, 4.52, 4.6, 1.4, [
    ("覆盖范围", 13, SAGE, True),
    ("苏州（沧浪亭 / 拙政园 / 留园 / 网师园 / 狮子林…）· 扬州（个园 / 何园）", 10.5, GREY),
    ("南京（瞻园 / 芥子园）· 杭州（郭庄）· 湖州（南浔小莲庄）等 8 市", 10.5, GREY),
    ("对照立项 15 园清单扩展至 23 园，含乐郊园、影园等已消失名园", 10.5, BRONZE_D, True),
], line_gap=1.22)
# v4.1：底部三张来源实物图 + 测绘工作照
add_text(s, 0.5, 5.72, 2.6, 0.25, "测绘图纸（沧浪亭复廊平面）", size=9.5, color=GREY, align=PP_ALIGN.CENTER)
add_image_fit(s, IMG_SURVEY, 0.5, 5.98, 2.6, 1.2)
add_text(s, 3.3, 5.72, 0.86, 0.25, "历史文献（复道回廊研究）", size=9.5, color=GREY, align=PP_ALIGN.CENTER)
add_image_fit(s, IMG_PAPER, 3.3, 5.98, 0.86, 1.2)
add_text(s, 4.35, 5.72, 4.9, 0.25, "属性数据表（寄畅园建筑）", size=9.5, color=GREY, align=PP_ALIGN.CENTER)
add_image_fit(s, IMG_TABLE, 4.35, 5.98, 4.9, 1.2)
add_text(s, 9.45, 5.72, 3.38, 0.25, "测绘工作照（畅园现场调研）", size=9.5, color=GREY, align=PP_ALIGN.CENTER)
add_image_fit(s, IMG_WORK, 9.45, 5.98, 3.38, 1.2)

# =========================================================
# 第 9 页 实体类别与关系类型
# =========================================================
s = content_slide(2, "实体类别与关系类型", "Chapter 02 · Categories", 10)
add_text(s, 0.5, 1.35, 6.35, 0.35, "实体类别（4 类）", size=14, bold=True, color=DARK)
labels = ["建筑 441", "山石 111", "花木 78", "池沼 75"]
for i, lb in enumerate(labels):
    x = 0.5 + (i % 4) * 1.58
    y = 1.70 + (i // 4) * 0.42
    chip(s, x, y, 1.45, 0.42, lb, fill=SAGE if i % 2 else BRONZE, size=11)
rels = [
    ("属于", "要素 → 园林（单向挂接）", "809 条"),
    ("相邻", "建筑环线 / 可看 / 对景，带方位 · 距离 · 中介", "794 条"),
    ("相接", "临水 / 在山上 / 在山边", "267 条"),
    ("连接", "要素间一般关联", "35 条"),
]
# v4.1：实体照片条（建筑 / 山石 / 池沼 / 花木 现状照片）——用户提供照片后填入 ENTITY_PHOTOS 即自动显示
photo_cats = ["建筑", "山石", "池沼", "花木"]
has_photos = len(ENTITY_PHOTOS) == 4 and all(os.path.exists(p) for p in ENTITY_PHOTOS)
if has_photos:
    for i, cat in enumerate(photo_cats):
        x = 0.5 + i * 1.63
        add_image_fit(s, ENTITY_PHOTOS[i], x, 2.60, 1.45, 0.76)
        add_text(s, x, 3.40, 1.45, 0.18, cat + "（现状）", size=9, color=GREY, align=PP_ALIGN.CENTER)
    add_text(s, 0.5, 3.66, 4.6, 0.3, "关系类型（4 类）", size=14, bold=True, color=DARK)
    add_text(s, 3.1, 3.70, 3.75, 0.25, "要素字段：编号 · 名称 · 类型 · 功能 · 平面坐标 · 极坐标",
             size=9.5, color=GREY)
    ry = 4.0
else:
    add_text(s, 0.5, 2.92, 6.35, 0.35, "关系类型（4 类）", size=14, bold=True, color=DARK)
    ry = 3.3
for name, desc, cnt in rels:
    add_rect(s, 0.5, ry, 6.35, 0.52, fill=LIGHT, line=LINE, round_=True)
    chip(s, 0.68, ry + 0.06, 0.95, 0.4, name, fill=BRONZE_D, size=11.5)
    add_text(s, 1.8, ry + 0.05, 3.4, 0.42, desc, size=10, color=GREY, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, 5.3, ry + 0.05, 1.3, 0.42, cnt, size=10, bold=True, color=DARK,
             align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    ry += 0.58
if not has_photos:
    add_text(s, 0.5, 5.65, 6.35, 0.25, "要素信息字段：编号（唯一）· 名称 · 类型 · 功能 · 平面坐标 · 极坐标",
             size=10, color=GREY)
bar_chart(s, 7.2, 1.35, 5.6, "各实体类别数量（实测）",
          [("建筑", 441), ("山石", 111), ("花木", 78), ("池沼", 75)],
          bar_color=BRONZE)
bar_chart(s, 7.2, 4.55, 5.6, "各关系类型数量（实测）",
          [("属于", 809), ("相邻", 794), ("相接", 267), ("连接", 35)],
          bar_color=SAGE)
caption_band(s, [
    ("关系信息字段：方位（中文十六方位）· 距离 · 中介（园路 / 水面等）· 相邻类型 / 接触类型 · 游线序号；建库原则：一园一库 · 编号唯一 · 双向关系成对记录 · 平台只读",
     11.5, DARK),
], accent=BRONZE)

# =========================================================
# 第 10 页 空间语义数据模型
# =========================================================
s = content_slide(2, "空间语义数据模型", "Chapter 02 · Spatial Model", 11)
layers = [
    ("位置层", "实体在哪里", "每处要素带平面坐标（米制，以大门 / 入口为原点）与极坐标；缺失坐标的要素自动置于平面中心", "→ 支撑空间布局模式（园林平面图还原）", BRONZE),
    ("关系层", "要素如何联系", "相邻（建筑环线 / 可看 / 对景）· 相接（临水 / 在山上 / 在山边），并记录方位（中文十六方位）、距离、中介（园路 / 水面 / 山径等 18 种）", "→ 支撑空间关系展示与条件筛选", SAGE),
    ("游线层", "如何游览", "“建筑环线”关系带游线序号（1–14），按序构成游览闭环，总长 487.7 m（沧浪亭实测）", "→ 支撑游线分析（逐步动画还原动线）", BRONZE_D),
]
ly = 1.3
for tag, t, d, f, c in layers:
    add_rect(s, 0.5, ly, 7.15, 1.42, fill=LIGHT, line=LINE, round_=True)
    chip(s, 0.68, ly + 0.45, 1.15, 0.52, tag, fill=c, size=12.5)
    add_text(s, 2.0, ly + 0.1, 5.55, 0.4, t, size=13.5, bold=True, color=DARK)
    add_text(s, 2.0, ly + 0.5, 5.55, 0.55, d, size=10, color=GREY, line_gap=1.05)
    add_text(s, 2.0, ly + 1.06, 5.55, 0.3, f, size=10.5, bold=True, color=c)
    if ly < 4.2:
        arrow_right(s, 3.6, ly + 1.42, h=0.3, fill=c)
    ly += 1.72
add_image_fit(s, os.path.join(SHOTS, "05-changyuan-neo4j-graph.png"), 7.95, 1.3, 4.85, 2.5)
add_text(s, 7.95, 3.95, 4.85, 1.85, [
    ("图数据库实测查询（畅园库）", 13, SAGE, True),
    ("45 个要素 / 130 条关系（双向成对记录）", 11, DARK),
    ("相邻 86（可看 / 路径）· 相接 44", 11, GREY),
    ("池沼 4 处（不规则水面）· 廊桥类 13 段", 11, GREY),
    ("平均关联数 2.91 · 留云山房 / 涤我尘襟为核心", 11, GREY),
], line_gap=1.3)
caption_band(s, [
    ("空间语义三层模型是平台功能的组织主线；全部字段（坐标、相邻类型、中介、方位、距离、游线序号）取自数据库实际结构，平台按“有则显示”原则自动适配，其他园林缺少相应数据时功能自动调整",
     11.5, DARK),
])

# =========================================================
# 第 11 页 多园林数据库架构
# =========================================================
s = content_slide(2, "多园林数据库架构", "Chapter 02 · Multi-Garden", 12)
add_image_fit(s, os.path.join(SHOTS, "11b-neo4j-databases.png"), 0.5, 1.3, 7.15, 3.66)
add_rect(s, 0.5, 5.0, 7.15, 1.28, fill=LIGHT, line=LINE, round_=True)
add_text(s, 0.75, 5.08, 6.7, 1.12, [
    ("园林数据自动识别", 12.5, SAGE, True),
    ("新园林数据加载后自动出现在列表中 · 空库自动排除 · 园名自动校正（11 个库）", 10.5, GREY),
    ("由单一沧浪亭库扩展至 23 园全量在线，各园数据结构差异自动适配，无需为任何新园改动程序", 10.5, GREY),
], line_gap=1.22)
add_image_fit(s, os.path.join(SHOTS, "11-garden-switcher.png"), 7.95, 1.3, 1.65, 2.7)
add_text(s, 9.8, 1.4, 3.0, 2.5, [
    ("园林切换器", 13, BRONZE, True),
    ("23 园一键切换", 11, DARK),
    ("全部页面数据", 11, GREY),
    ("自动联动刷新", 11, GREY),
], line_gap=1.25)
add_rect(s, 7.95, 4.35, 4.85, 1.9, fill=LIGHT, line=LINE, round_=True)
add_text(s, 8.2, 4.45, 4.35, 1.75, [
    ("工程稳健性", 12.5, SAGE, True),
    ("修复访问高峰卡顿：并发请求合并 + 轻量状态检查", 10.5, GREY),
    ("23 园数据质量核查：坐标完整率 / 游线闭合 / 空间关系 / 重复编号检测", 10.5, GREY),
    ("缺数据自动适配：无坐标自动居中 · 无游线友好提示", 10.5, GREY),
], line_gap=1.3)
caption_band(s, [
    ("新园林数据加载后点「⟳」刷新即接入，无需修改任何程序；核查结果逐园生成坐标完整率 / 游线闭合 / 空间关系 / 重复编号检测表",
     11.5, DARK),
])

# =========================================================
# 第 12 页 分节页 叁
# =========================================================
s = new_slide(L_DIV[3])
set_ph(ph_by_pos(s, 6.87, 3.28), CH[3], size=22, bold=True, color=DARK)
set_ph(ph_by_pos(s, 10.17, 0.20), INST_CN, size=10, color=DARK)
set_ph(ph_by_pos(s, 10.19, 0.41), INST_EN, size=9, color=GREY)

# =========================================================
# 第 13 页 平台总体架构与数据概览
# =========================================================
s = content_slide(3, "平台总体架构与数据概览", "Chapter 03 · Overview", 14)
add_image_fit(s, os.path.join(SHOTS, "01-dashboard-full.png"), 0.5, 1.3, 8.35, 5.15)
arch = [
    ("数据层", "Neo4j 图数据库 · 一园一库 × 23", "按园林自动定位对应数据", BRONZE),
    ("知识层", "要素 + 关系 + 空间信息", "结构动态读取 · 信息完整保留", SAGE),
    ("展示层", "8 个功能页面", "网络图与平面图 · 园林一键切换", BRONZE_D),
]
ay = 1.35
for t, d1, d2, c in arch:
    add_rect(s, 9.1, ay, 3.7, 1.02, fill=LIGHT, line=LINE, round_=True)
    add_rect(s, 9.1, ay, 0.07, 1.02, fill=c)
    add_text(s, 9.32, ay + 0.08, 3.4, 0.4, t, size=13, bold=True, color=DARK)
    add_text(s, 9.32, ay + 0.44, 3.4, 0.55, [(d1, 10.5, GREY), (d2, 10.5, GREY)], line_gap=1.05)
    ay += 1.18
add_rect(s, 9.1, 4.9, 3.7, 1.35, fill=LIGHT2, line=LINE, round_=True)
add_text(s, 9.32, 5.0, 3.3, 1.2, [
    ("数据查询服务", 12.5, SAGE, True),
    ("13 项查询功能（全部实测通过）", 10.5, DARK),
    ("只读设计 · 园林自动识别 · 查询安全防护", 10.5, GREY),
], line_gap=1.18)
caption_band(s, [
    ("访问链路：网页界面 → 查询服务 → 图数据库（一园一库）；平台只提供浏览查询功能，不修改任何原始数据",
     11.5, DARK),
])

# =========================================================
# 第 14 页 实体浏览与搜索
# =========================================================
s = content_slide(3, "实体浏览与搜索", "Chapter 03 · Entities", 15)
add_image_fit(s, os.path.join(SHOTS, "cy-12b-entities.png"), 0.5, 1.3, 7.9, 4.6)
add_text(s, 8.65, 1.5, 4.15, 4.3, [
    ("分类浏览", 13.5, BRONZE, True),
    ("按实体类别分页签浏览（页签由数据自动生成）；列表展示名称 / 类别 / 关联数量 / 所属园林，支持分页浏览。", 11, GREY),
    ("",),
    ("实体搜索", 13.5, SAGE, True),
    ("关键词查找：精确优先 + 模糊匹配；支持按类别与园林筛选、跨园林查找。", 11, GREY),
    ("",),
    ("详情抽屉", 13.5, BRONZE_D, True),
    ("展示要素全部信息与关联要素（按关系类型分组，含方向与关系说明），数据字段缺失时自动适配。", 11, GREY),
    ("",),
    ("图谱联动", 13.5, SAGE, True),
    ("“在图谱中查看”一键定位，将要素放入关系网络与平面图中。", 11, GREY),
], line_gap=1.2)
caption_band(s, [
    ("名称显示规则：优先显示名称 → 无名称显示编号 → 再退类别；跨园林统一编号保证要素唯一可查",
     11.5, DARK),
])

# =========================================================
# 第 15 页 知识图谱探索
# =========================================================
s = content_slide(3, "知识图谱探索", "Chapter 03 · Explore", 16)
add_image_fit(s, os.path.join(SHOTS, "cy-08-relation-network.png"), 0.5, 1.3, 8.0, 4.37)
add_text(s, 8.75, 1.5, 4.05, 4.3, [
    ("自动网络排布", 13.5, BRONZE, True),
    ("关系网络自动排布：要素可拖拽、画面缩放平移；节点大小反映关联数量。", 11, GREY),
    ("",),
    ("双击展开", 13.5, SAGE, True),
    ("双击要素自动加载其直接关联的要素，逐层浏览（探索式），已加载要素不重复显示。", 11, GREY),
    ("",),
    ("关系筛选", 13.5, BRONZE_D, True),
    ("按关系类型 / 相邻类型筛选显示；双向重复记录可合并显示。", 11, GREY),
    ("",),
    ("空间信息提示", 13.5, SAGE, True),
    ("悬浮显示关系类型与空间信息（方位 / 距离 / 中介）；详情面板分组展示关联要素。", 11, GREY),
], line_gap=1.2)
caption_band(s, [
    ("知识关系网络 ⇄ 园林平面图一键切换——同一批数据两种视图；图例与配色按类别自动生成，新增类别自动适配",
     11.5, DARK),
])

# =========================================================
# 第 16 页 空间布局可视化【演示】
# =========================================================
s = content_slide(3, "空间布局可视化", "Chapter 03 · Spatial Layout", 17)
add_image_fit(s, GIF_SPATIAL, 0.5, 1.3, 5.85, 4.6)
add_image_fit(s, IMG_CAD_CY, 6.55, 1.3, 1.75, 4.6)
add_text(s, 6.55, 4.95, 1.75, 0.5, ["畅园测绘平面图", "（同批数据·同源坐标）"], size=9.5, color=GREY,
         align=PP_ALIGN.CENTER, line_gap=1.15)
add_image_fit(s, os.path.join(SHOTS, "cy-07b-node-detail.png"), 8.5, 1.3, 1.95, 4.6)
add_text(s, 10.65, 1.45, 2.15, 4.3, [
    ("真实坐标", 14, BRONZE, True),
    ("测绘坐标 1:1 还原平面格局", 10, GREY),
    ("",),
    ("坐标适配", 13.5, SAGE, True),
    ("北向适配 · 边界自动缩放", 10, GREY),
    ("",),
    ("按类别着色", 13.5, BRONZE_D, True),
    ("建筑 / 山石 / 池沼 / 花木", 10, GREY),
    ("",),
    ("节点详情", 13.5, SAGE, True),
    ("坐标 + 极坐标 + 形制功能", 10, GREY),
], line_gap=1.18)
caption_band(s, [
    ("动图演示（自动循环播放）：切「畅园」→ 空间布局模式还原平面图 → 点击水香榭查看详情 → 切知识关系模式；外户门原点、北侧留云山房、沿东边界折行的东曲廊、中部何池分布一目了然（右列测绘平面图与平台平面图同源，详见下页对照）",
     11.5, DARK),
])

# =========================================================
# 第 17 页 测绘平面图与平台还原对照（v4.1 新增 · 重点页）
# =========================================================
s = content_slide(3, "测绘平面图与平台还原对照", "Chapter 03 · Plan vs Platform", 18)
add_text(s, 0.6, 1.35, 4.3, 0.3, "畅园测绘平面图", size=12, bold=True, color=DARK, align=PP_ALIGN.CENTER)
add_image_fit(s, IMG_CAD_CY, 0.6, 1.7, 4.3, 4.6)
add_text(s, 5.4, 1.35, 7.3, 0.3, "平台空间布局渲染（同一批数据 · 坐标 1:1 还原）",
         size=12, bold=True, color=DARK, align=PP_ALIGN.CENTER)
add_image_fit(s, os.path.join(SHOTS, "cy-07-spatial-layout.png"), 5.4, 1.7, 7.3, 3.55)
add_rect(s, 5.4, 5.35, 7.3, 0.9, fill=LIGHT, line=LINE, round_=True)
add_text(s, 5.65, 5.42, 6.9, 0.8, [
    ("两图对应要素：外户门（原点）· 留云山房 · 桐华书屋 · 水香榭 · 何池 · 东曲廊 / 西廊", 11, DARK),
    ("同一批测绘数据 → 结构化入库 → 平台按坐标自动还原平面格局，并叠加游览动线与空间关系", 10.5, GREY),
], line_gap=1.2)
caption_band(s, [
    ("平台平面图不是示意图——节点位置直接来自测绘坐标（外户门为原点），与测绘平面图同源可对照；评委可对比两图验证还原准确性",
     11.5, DARK),
], accent=BRONZE_D)

# =========================================================
# 第 18 页 游线分析【演示】
# =========================================================
s = content_slide(3, "游线分析", "Chapter 03 · Tour Route", 19)
add_image_fit(s, GIF_ROUTE, 0.5, 1.3, 8.15, 4.95)
metric_card(s, 8.95, 1.4, 3.85, 1.0, "14 站闭环", "沧浪亭游览动线（游线序号 1–14）", value_size=24)
metric_card(s, 8.95, 2.5, 3.85, 1.0, "487.7 m", "闭环总长（实测数据）", value_size=24, value_color=SAGE)
metric_card(s, 8.95, 3.6, 3.85, 1.0, "28 站 · 770.8 m", "全库最长：狮子林", value_size=20, value_color=BRONZE_D)
add_text(s, 8.95, 4.72, 3.9, 1.55, [
    ("依据数据中的游线序号自动生成闭环游览动线，无需人工整理", 11, DARK),
    ("空间平面图上逐步动画：播放 / 暂停 / 单步 / 滑块回放", 11, DARK),
    ("行程列表：每段起止建筑、方位、距离、中介，点击跳转", 11, DARK),
], line_gap=1.3)
caption_band(s, [
    ("动图演示（自动循环播放）：点「▶ 播放游线」按游线序号逐步还原游览动线（橙色=已走 · 虚线=未走）；全库 9 园含闭环游线，最长狮子林 28 站 770.8 m",
     11.5, DARK),
])

# =========================================================
# 第 19 页 空间关系分析
# =========================================================
s = content_slide(3, "空间关系分析", "Chapter 03 · Spatial Relations", 20)
add_image_fit(s, GIF_SP_REL, 0.5, 1.3, 7.4, 4.85)
add_image_fit(s, os.path.join(SHOTS, "cy-10b-relation-detail.png"), 8.1, 1.3, 1.5, 3.1)
add_text(s, 9.85, 1.4, 2.95, 4.25, [
    ("关系统计", 13, BRONZE, True),
    ("相邻 86 / 相接 44，双向记录保留方向含义", 10.5, GREY),
    ("",),
    ("多条件筛选", 13, SAGE, True),
    ("类型 / 相邻类型 / 接触类型 / 中介 / 距离上限，选项由数据自动生成", 10.5, GREY),
    ("",),
    ("地图叠加", 13, BRONZE_D, True),
    ("筛选结果叠加到平面图：彩色=符合条件 · 灰色=不符合", 10.5, GREY),
    ("",),
    ("详情面板", 13, SAGE, True),
    ("点击连线查看完整空间信息：类型 · 方位 · 距离 · 中介", 10.5, GREY),
], line_gap=1.18)
caption_band(s, [
    ("动图演示（自动循环播放）：筛选「可看」关系（畅园 72 条）→ 平面图连线叠加 → 点击连线查看空间信息（如 留云山房 →相邻·可看·9.5 m→ 水香榭）",
     11.5, DARK),
])

# =========================================================
# 第 20 页 知识网络分析与路径查询
# =========================================================
s = content_slide(3, "知识网络分析与路径查询", "Chapter 03 · Network & Path", 21)
add_image_fit(s, os.path.join(SHOTS, "cy-08b-network-analysis.png"), 0.5, 1.3, 5.95, 3.47)
add_text(s, 0.5, 4.95, 5.95, 1.4, [
    ("知识网络分析", 13.5, BRONZE, True),
    ("平均关联数 2.91（畅园：每个要素平均与约 3 个要素直接关联）· 关联最多的节点 = 留云山房 / 涤我尘襟（各 10 条关联）", 10.5, DARK),
    ("核心要素排行印证畅园空间组织：主厅堂（留云山房）与开敞轩（涤我尘襟）关联最密，东曲廊 / 曲桥等线状要素串联全园", 10.5, GREY),
], line_gap=1.25)
add_image_fit(s, GIF_PATH, 6.75, 1.3, 5.95, 3.44)
add_text(s, 6.75, 4.95, 5.95, 1.4, [
    ("路径查询：沧浪亭假山 → 面水轩（沧浪亭示例）", 13.5, SAGE, True),
    ("3 段 · 总距 96.7 m（仅沿空间关系寻路）：相接·在山上 9.6 m → 相邻·建筑环线·可看 63.9 m → 相接·临水 23.2 m", 10.5, DARK),
    ("支持起点 / 终点选择（可交换）；平面图上高亮路径（绿=起点 · 红=终点）", 10.5, GREY),
], line_gap=1.25)
caption_band(s, [
    ("动图演示（自动循环播放）：知识网络分析页查看指标与核心要素排行（畅园）→ 路径查询页以沧浪亭为例演示空间路径（畅园暂无游线 / 路径数据）",
     11.5, DARK),
])

# =========================================================
# 第 21 页 分节页 肆
# =========================================================
s = new_slide(L_DIV[4])
set_ph(ph_by_pos(s, 6.87, 3.28), CH[4], size=22, bold=True, color=DARK)
set_ph(ph_by_pos(s, 10.17, 0.20), INST_CN, size=10, color=DARK)
set_ph(ph_by_pos(s, 10.19, 0.41), INST_EN, size=9, color=GREY)

# =========================================================
# 第 22 页 项目成果总结
# =========================================================
s = content_slide(4, "项目成果总结", "Chapter 04 · Achievements", 23)
results = [
    ("01", "建立江南古典园林知识图谱数据库", "23 个江南园林 · 718 个要素 · 1905 条关系；实体 4 类（建筑 / 山石 / 花木 / 池沼）、关系 4 类，覆盖苏州、扬州、南京等 8 市现存与已消失名园。", BRONZE),
    ("02", "完成多园林数据库管理", "各园林独立建档、自动识别与一键切换；23 园数据质量核查与缺项处理（重复编号合并 / 园名校正）。", SAGE),
    ("03", "构建知识图谱可视化平台", "8 个功能页面 + 13 项查询功能；界面与数据分离、平台只读，全部功能经逐项核验通过。", BRONZE_D),
    ("04", "实现空间关系与游线分析", "9 园闭环游线逐步动画复原（最长 28 站 770.8 m）；空间关系组合筛选与平面图叠加联动。", SAGE),
]
for (num, t, d, c), (x, y) in zip(results, [(0.5, 1.4), (6.72, 1.4), (0.5, 3.75), (6.72, 3.75)]):
    add_rect(s, x, y, 6.11, 2.2, fill=LIGHT, line=LINE, round_=True)
    chip(s, x + 0.25, y + 0.3, 0.62, 0.62, num, fill=c, size=18)
    add_text(s, x + 1.1, y + 0.26, 4.85, 0.85, t, size=15, bold=True, color=DARK, line_gap=1.15)
    add_text(s, x + 0.3, y + 1.25, 5.55, 0.85, d, size=11, color=GREY, line_gap=1.22)
stats = ["23 园林", "718 要素", "1905 关系", "13 项查询", "8 页面", "9 园游线"]
sx = 0.5
for st in stats:
    chip(s, sx, 6.18, 1.95, 0.55, st, fill=BRONZE, size=13)
    sx += 2.07
caption_band(s, [
    ("项目形成的空间知识图谱数据集与可视化平台，为江南古典园林数字化保护与研究提供可复用的数据基础与工具支撑",
     11.5, DARK),
], y=6.8, h=0.35, accent=BRONZE_D)

# =========================================================
# 第 24 页 创新点（v4.2c：左列 6 项 + 右栏知识图谱配图与拆解式表达示意）
# =========================================================
s = content_slide(4, "创新点", "Chapter 04 · Innovations", 24)
inno = [
    ("①", "园林知识的图谱化储存", "以「要素—关系—属性」的图谱形式组织园林信息，替代传统表格记录——建筑、山水、花木之间的空间与语义关联得以结构化储存、查询与计算。", BRONZE),
    ("②", "空间语义三层模型", "位置—关系—游线三个层次：不仅表达“有什么”，更表达“在哪里、怎么联系、如何游览”。", SAGE),
    ("③", "真实坐标平面图还原", "测绘坐标直接生成平面格局（非示意图）：南北方向适配 + 边界自动缩放，平面图 1:1 还原。", BRONZE_D),
    ("④", "复杂要素的拆解式表达", "不规则水面、折廊等复杂形态拆解为逐段小要素——以小要素为视角记录其编号、坐标、形制，及小要素之间、小要素与其他要素之间的关系（畅园东曲廊 4 段 / 西廊 2 段 / 曲桥 6 段，建筑—廊道相接 32 条）。", SAGE),
    ("⑤", "游览动线自动复原", "依据游线序号自动生成闭环动线并动画呈现：无需人工整理，动线可回放、可定位。", BRONZE),
    ("⑥", "全动态结构与缺项适配", "类别 / 关系 / 字段均由数据自动读取，23 园结构差异零改动接入；无坐标自动居中 · 缺数据友好提示 · 重复编号自动合并。", BRONZE_D),
]
ry = 1.3
for num, t, d, c in inno:
    add_rect(s, 0.5, ry, 8.0, 0.79, fill=LIGHT, line=LINE, round_=True)
    add_rect(s, 0.5, ry, 0.07, 0.79, fill=c)
    chip(s, 0.72, ry + 0.12, 0.55, 0.55, num, fill=c, size=15)
    add_text(s, 1.5, ry + 0.06, 6.85, 0.3, t, size=12.5, bold=True, color=DARK)
    add_text(s, 1.5, ry + 0.4, 6.85, 0.36, d, size=10, color=GREY, line_gap=1.05)
    ry += 0.83

# 右栏上：园林知识以图谱形式储存（畅园知识关系网络实拍）
add_image_fit(s, os.path.join(SHOTS, "cy-08-relation-network.png"), 8.72, 1.3, 4.11, 2.02)
add_text(s, 8.72, 3.34, 4.11, 0.28, "以知识图谱形式储存园林信息（畅园 45 要素 · 130 关系）",
         size=9, color=GREY, align=PP_ALIGN.CENTER)

# 右栏下：复杂要素拆解式表达示意（自绘）
add_text(s, 8.72, 3.64, 4.11, 0.3, "拆解式表达：整体 → 小要素 → 关系记录",
         size=10.5, bold=True, color=DARK, align=PP_ALIGN.CENTER)
add_rect(s, 9.82, 3.96, 1.9, 0.4, fill=BRONZE, round_=True)
add_text(s, 9.82, 4.0, 1.9, 0.32, "东曲廊（折廊整体）", size=10, bold=True, color="FFFFFF",
         align=PP_ALIGN.CENTER)
arr = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(10.65), Inches(4.4), Inches(0.24), Inches(0.3))
arr.fill.solid()
arr.fill.fore_color.rgb = RGBColor.from_string(BRONZE_D)
arr.line.fill.background()
arr.shadow.inherit = False
for i, ox in enumerate([9.5, 10.3, 11.1, 11.9]):
    ov = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(ox), Inches(4.76), Inches(0.46), Inches(0.46))
    ov.fill.solid()
    ov.fill.fore_color.rgb = RGBColor.from_string(SAGE)
    ov.line.fill.background()
    ov.shadow.inherit = False
    p = ov.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "①②③④"[i]
    set_font(run, size=12, bold=True, color="FFFFFF")
add_text(s, 8.72, 5.26, 4.11, 0.24, "4 个独立小要素（各自编号 · 坐标 · 形制）", size=9, color=GREY,
         align=PP_ALIGN.CENTER)
add_text(s, 8.95, 5.54, 3.85, 0.72, [
    ("③ —相接 4.2 m— 憩间", 9, DARK),
    ("② —相接 2.0 m— 水香榭", 9, DARK),
    ("① —相接 4.7 m— 桐华书屋", 9, DARK),
    ("以小要素为视角，记录与其他要素的关系", 9, GREY),
], line_gap=1.15)

# =========================================================
# 第 24 页 不足与展望
# =========================================================
s = content_slide(4, "不足与展望", "Chapter 04 · Limitations", 25)
add_rect(s, 0.5, 1.35, 6.11, 4.95, fill=LIGHT, line=LINE, round_=True)
chip(s, 0.75, 1.55, 1.3, 0.5, "不足", fill=BRONZE_D, size=13)
limits = [
    ("①", "空间信息覆盖不完整——14 个园林仅有隶属关系数据，空间布局 / 游线 / 关系分析功能有待数据补全后覆盖。"),
    ("②", "立项中的 AI 复原生成模型与跨模态融合未开展——仅预留智能问答入口，现阶段为后续智能化应用提供知识基础。"),
    ("③", "个别园林存在数据质量问题——如重复编号、无类别要素，已由平台合并显示与名称兜底规则处理，数据本身待修复。"),
    ("④", "平台依赖本机数据库运行——尚未部署为在线服务，多用户访问与运维方案有待完善。"),
]
ly = 2.2
for num, d in limits:
    add_text(s, 0.85, ly, 5.55, 1.0, [(num + " ", 12, SAGE, True), (d, 10.5, DARK)], line_gap=1.2)
    ly += 1.02
add_rect(s, 6.72, 1.35, 6.11, 4.95, fill=LIGHT, line=LINE, round_=True)
chip(s, 6.97, 1.55, 1.3, 0.5, "展望", fill=SAGE, size=13)
outs = [
    ("①", "数据补全——14 园补齐坐标 / 相邻 / 相接 / 环线数据，实现全库空间功能覆盖，充分释放平台空间分析能力。"),
    ("②", "智能问答——入口已预留（自动读取数据结构 + 只读校验），支持自然语言查询园林知识。"),
    ("③", "多模态数据融合——历史文献、园林图像、测绘图纸与知识图谱关联，呼应立项“跨模态”目标。"),
    ("④", "空间分析深化与数字复原——视域 / 对景分析、游览组织比较、空间推演，衔接立项 AI 复原方向。"),
]
oy = 2.2
for num, d in outs:
    add_text(s, 7.07, oy, 5.55, 1.0, [(num + " ", 12, BRONZE, True), (d, 10.5, DARK)], line_gap=1.2)
    oy += 1.02
caption_band(s, [
    ("数据是平台的基础——空间信息的持续补全将直接释放平台的空间分析能力；知识图谱同时为后续智能应用提供结构化知识底座",
     11.5, DARK),
], accent=BRONZE_D)

# =========================================================
# 第 25 页 致谢
# =========================================================
s = new_slide(L_COVER)
set_ph(ph_by_pos(s, 10.19, 0.15), INST_CN, size=10, color=DARK)
set_ph(ph_by_pos(s, 10.20, 0.36), INST_EN, size=9, color=GREY)
set_ph(ph_by_pos(s, 2.07, 2.67), "谢谢聆听 · 敬请各位老师批评指导", size=30, bold=True, color=DARK)
set_ph(ph_by_pos(s, 4.11, 4.26), "Thank You for Listening", size=14, color=BRONZE_D, align=PP_ALIGN.CENTER)
set_ph(ph_by_pos(s, 5.34, 4.83), "汇报人：杨思成", size=15, color=DARK, align=PP_ALIGN.CENTER)
set_ph(ph_by_pos(s, 5.34, 5.41), ["成员：王梓萌、余悦", "导师：邵星宇、王笑"], size=11, color=GREY, align=PP_ALIGN.CENTER)

try:
    prs.save(OUT)
    print("已生成:", OUT)
except PermissionError:
    # 成品正被 PowerPoint 打开时无法覆盖，另存带时间戳的副本
    alt = OUT.replace(".pptx", time.strftime("（%H%M%S）.pptx"))
    prs.save(alt)
    print("原文件被占用，已另存:", alt)
    print("（关闭 PowerPoint 中打开的旧文件后重跑本脚本即可覆盖正名）")
print("总页数:", len(prs.slides._sldIdLst))
