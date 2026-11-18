# -*- coding: utf-8 -*-
"""生成 SRTP 结项答辩 PPT（16:9，科研汇报风格，白底蓝绿主色，图表优先）。

用法：python tools/make_defense_ppt.py
输出：docs/结项答辩-江南古典园林空间知识图谱可视化平台.pptx
依据：docs/defense_ppt_plan.md（15 页结构）+ docs/ppt_screenshots/（已采集截图）
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from PIL import Image
import os

# ---------- 主题 ----------
FONT = "微软雅黑"
DARK = "2F4B3C"    # 深绿（标题）
TEAL = "2F8F83"    # 主色（蓝绿）
BLUE = "3B6EA5"    # 辅色（蓝）
GREY = "808A92"    # 次要文字
LINE = "D5DCE0"    # 边框/分隔
BG = "FFFFFF"      # 白底
LIGHT = "F2F6F6"   # 占位框浅底

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(BASE, "docs", "ppt_screenshots")
IMAGES_DIR = os.path.join(BASE, "images")
OUT = os.path.join(BASE, "docs", "结项答辩-江南古典园林空间知识图谱可视化平台.pptx")

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
BLANK = prs.slide_layouts[6]

TOTAL = 15


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
             align=PP_ALIGN.LEFT, line_gap=1.15, anchor=MSO_ANCHOR.TOP):
    """lines: str 或 [(text, size, color, bold, align), ...] 列表"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    if isinstance(lines, str):
        lines = [(lines, size, color, bold, align)]
    for i, item in enumerate(lines):
        if isinstance(item, tuple):
            text = item[0]
            sz = item[1] if len(item) > 1 else size
            col = item[2] if len(item) > 2 else color
            bd = item[3] if len(item) > 3 else bold
            al = item[4] if len(item) > 4 else align
        else:
            text, sz, col, bd, al = item, size, color, bold, align
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = al
        p.line_spacing = line_gap
        run = p.add_run()
        run.text = text
        set_font(run, size=sz, bold=bd, color=col)
    return tb


def add_rect(slide, x, y, w, h, fill=None, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid() if fill else sh.fill.background()
    if fill:
        sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    if line:
        sh.line.color.rgb = RGBColor.from_string(line)
        sh.line.width = Pt(1)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def img_size(path):
    with Image.open(path) as im:
        return im.size  # (w, h) px


def add_image_fit(slide, path, x, y, w, h, border=True):
    """在 (x,y,w,h) 区域内等比缩放居中插入图片，返回实际放置框。"""
    if not os.path.exists(path):
        return add_placeholder(slide, x, y, w, h, f"（缺少截图：{os.path.basename(path)}）")
    pw, ph = img_size(path)
    scale = min(w / pw, h / ph)
    nw, nh = pw * scale, ph * scale
    nx, ny = x + (w - nw) / 2, y + (h - nh) / 2
    if border:
        add_rect(slide, nx - 0.03, ny - 0.03, nw + 0.06, nh + 0.06, fill=None, line=LINE)
    slide.shapes.add_picture(path, Inches(nx), Inches(ny), Inches(nw), Inches(nh))
    return (nx, ny, nw, nh)


def add_placeholder(slide, x, y, w, h, caption):
    add_rect(slide, x, y, w, h, fill=LIGHT, line=LINE)
    add_text(slide, x, y, w, h, caption, size=11, color=GREY, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def new_slide(title, page_no):
    slide = prs.slides.add_slide(BLANK)
    # 标题
    add_text(slide, 0.5, 0.32, 11.5, 0.65, title, size=25, bold=True, color=DARK)
    # 标题下强调线（蓝绿主色）
    add_rect(slide, 0.53, 1.06, 1.5, 0.05, fill=TEAL)
    # 页码
    add_text(slide, 12.35, 7.08, 0.7, 0.3, f"{page_no} / {TOTAL}", size=9, color=GREY, align=PP_ALIGN.RIGHT)
    return slide


# =========================================================
# 第 1 页 项目背景与研究意义
# =========================================================
s = new_slide("项目背景与研究意义", 1)
add_text(s, 0.5, 1.55, 6.6, 4.8, [
    ("江南古典园林", 22, DARK, True),
    ("中国园林艺术的最高成就，以建筑、水体、山石、花木营造", 15, GREY),
    ("“步移景异”的空间体验。", 15, GREY),
    "",
    ("现实问题", 18, BLUE, True),
    ("园林知识分散于文献、测绘、图像等多源资料；", 15, GREY),
    ("传统数据库难以表达实体间复杂的空间与语义关联。", 15, GREY),
    "",
    ("本研究", 18, TEAL, True),
    ("以知识图谱技术组织园林知识，构建空间知识图谱可视化平台，", 15, DARK),
    ("服务园林文化遗产的数字化保护与研究。", 15, DARK),
], line_gap=1.25)
photo = os.path.join(IMAGES_DIR, os.listdir(IMAGES_DIR)[0]) if os.path.isdir(IMAGES_DIR) and os.listdir(IMAGES_DIR) else None
if photo:
    add_image_fit(s, photo, 7.45, 1.5, 5.35, 5.0)
else:
    add_placeholder(s, 7.45, 1.5, 5.35, 5.0, "（园林照片）")

# =========================================================
# 第 2 页 项目目标
# =========================================================
s = new_slide("项目目标", 2)
add_text(s, 0.5, 1.7, 7.0, 4.6, [
    ("01  构建空间语义知识图谱", 18, DARK, True),
    ("园林实体 + 关系 + 空间属性（坐标 / 方向 / 距离 / 环线）", 14, GREY),
    ("",),
    ("02  研发可视化交互平台", 18, DARK, True),
    ("浏览 · 搜索 · 图谱探索 · 空间分析，无需掌握图数据库", 14, GREY),
    ("",),
    ("03  还原空间格局与游览动线", 18, DARK, True),
    ("真实测绘坐标还原平面图，环线数据复原游览路径", 14, GREY),
    ("",),
    ("04  支持多园林动态接入", 18, DARK, True),
    ("一园一库，23 个园林数据库自动发现、一键切换", 14, GREY),
], line_gap=1.3)
add_placeholder(s, 8.0, 1.7, 4.8, 4.6, "（可选配图：平台首页截图）")

# =========================================================
# 第 3 页 技术路线
# =========================================================
s = new_slide("技术路线", 3)
add_image_fit(s, os.path.join(SHOTS, "03-architecture.png"), 0.8, 1.35, 11.7, 3.6)
add_text(s, 0.8, 5.25, 11.7, 1.4, [
    ("多源园林知识 → 空间语义建模 → Neo4j 图数据库（一园一库 × 23）", 15, DARK),
    ("→ FastAPI 只读服务（13 接口） → Vue3 + ECharts 可视化平台（8 页面）", 15, DARK),
], align=PP_ALIGN.CENTER, line_gap=1.5)

# =========================================================
# 第 4 页 数据资源与知识图谱构建
# =========================================================
s = new_slide("数据资源与知识图谱构建", 4)
add_image_fit(s, os.path.join(SHOTS, "04a-stat-cards.png"), 0.5, 1.3, 12.3, 1.2)
add_image_fit(s, os.path.join(SHOTS, "04b-garden-table.png"), 0.5, 2.7, 7.2, 4.6)
add_text(s, 8.0, 2.9, 4.8, 4.3, [
    ("23 个江南园林", 20, TEAL, True),
    ("718 节点 · 1905 关系", 16, DARK, True),
    ("",),
    ("覆盖范围", 15, BLUE, True),
    ("苏州（沧浪亭 / 拙政园 / 留园 / 网师园 / 狮子林 / 耦园…）", 12.5, GREY),
    ("扬州（个园 / 何园）· 南京（瞻园 / 芥子园）", 12.5, GREY),
    ("杭州（郭庄）· 湖州（南浔小莲庄）等", 12.5, GREY),
    ("",),
    ("数据来源", 15, BLUE, True),
    ("测绘资料与历史文献整理：坐标、形制、功能、", 12.5, GREY),
    ("空间关系、游览环线序号", 12.5, GREY),
], line_gap=1.25)

# =========================================================
# 第 5 页 知识图谱数据库设计
# =========================================================
s = new_slide("知识图谱数据库设计", 5)
add_text(s, 0.5, 1.5, 6.6, 5.2, [
    ("实体类型（动态 · 8 类）", 16, DARK, True),
    ("园林 · 建筑 · 山石 · 池沼 · 花木 · 园林要素 · 实体 · 区域", 13.5, GREY),
    ("",),
    ("关系类型（4 类）", 16, DARK, True),
    ("属于（要素→园林）· 相邻（建筑环线 / 可看 / 对景）", 13.5, GREY),
    ("相接（临水 / 在山上 / 在山边）· 连接", 13.5, GREY),
    ("",),
    ("空间语义属性", 16, DARK, True),
    ("x / y 平面坐标（米）· 极径 / 极角（极坐标）", 13.5, GREY),
    ("方向（中文十六方位）· 距离 · 中介 · 环线序号", 13.5, GREY),
    ("",),
    ("设计原则", 16, DARK, True),
    ("一园一库 · 编号唯一约束 · 对称关系双写 · 平台只读", 13.5, GREY),
], line_gap=1.25)
add_placeholder(s, 7.45, 1.4, 5.35, 2.6, "Neo4j Browser 图谱查询截图\n（MATCH (n)-[r]->(m) RETURN n,r,m）")
add_placeholder(s, 7.45, 4.25, 5.35, 2.35, "E-R 示意图（自绘）")

# =========================================================
# 第 6 页 可视化平台总体架构
# =========================================================
s = new_slide("可视化平台总体架构", 6)
add_image_fit(s, os.path.join(SHOTS, "01-dashboard-full.png"), 0.5, 1.3, 8.7, 5.6)
add_text(s, 9.45, 1.6, 3.4, 5.2, [
    ("数据层", 16, DARK, True),
    ("Neo4j 一园一库 × 23", 13, GREY),
    ("",),
    ("知识层", 16, DARK, True),
    ("节点 + 关系 + 空间语义", 13, GREY),
    ("",),
    ("展示层", 16, DARK, True),
    ("8 个功能页面", 13, GREY),
    ("",),
    ("后端", 16, DARK, True),
    ("13 个只读接口", 13, GREY),
    ("多库路由 · 动态 Schema", 13, GREY),
], line_gap=1.3)

# =========================================================
# 第 7 页 园林空间布局可视化
# =========================================================
s = new_slide("园林空间布局可视化", 7)
add_image_fit(s, os.path.join(SHOTS, "07-spatial-layout.png"), 0.5, 1.3, 8.1, 5.3)
add_image_fit(s, os.path.join(SHOTS, "07b-node-detail.png"), 8.75, 1.3, 4.05, 5.3)
add_text(s, 0.5, 6.7, 12.3, 0.55, [
    ("真实 x / y 测绘坐标还原平面图（y 轴翻转 · 边界自适应）　·　按标签类型着色　·　点击节点查看详情（平面 / 极坐标 · 游线序号）",
     12.5, DARK),
])

# =========================================================
# 第 8 页 知识关系网络分析
# =========================================================
s = new_slide("知识关系网络分析", 8)
add_image_fit(s, os.path.join(SHOTS, "08-relation-network.png"), 0.5, 1.3, 7.5, 5.3)
add_image_fit(s, os.path.join(SHOTS, "08b-network-analysis.png"), 8.15, 1.3, 4.65, 5.3)
add_text(s, 0.5, 6.7, 12.3, 0.55, [
    ("力导向知识网络 · 双击逐层展开　·　网络指标（平均连接度 · 最大关联节点）　·　Top 核心节点——园林根节点为网络枢纽",
     12.5, DARK),
])

# =========================================================
# 第 9 页 游线分析
# =========================================================
s = new_slide("游线分析", 9)
add_image_fit(s, os.path.join(SHOTS, "09-route-playing.png"), 0.5, 1.3, 8.3, 5.6)
add_text(s, 9.1, 1.7, 3.7, 4.9, [
    ("环线序号", 18, TEAL, True),
    ("数据驱动提取闭环游线", 13, GREY),
    ("",),
    ("沧浪亭实测", 16, BLUE, True),
    ("14 站闭环", 20, DARK, True),
    ("总长 487.7 m", 20, DARK, True),
    ("",),
    ("空间底图上逐步动画", 13, GREY),
    ("播放 / 暂停 / 滑块回放", 13, GREY),
    ("每段方向 · 距离 · 中介", 13, GREY),
], line_gap=1.3)

# =========================================================
# 第 10 页 空间关系分析
# =========================================================
s = new_slide("空间关系分析", 10)
add_image_fit(s, os.path.join(SHOTS, "10-spatial-filtered.png"), 0.5, 1.3, 8.2, 5.6)
add_image_fit(s, os.path.join(SHOTS, "10b-relation-detail.png"), 8.85, 1.3, 3.95, 4.6)
add_text(s, 8.85, 6.0, 3.95, 1.0, [
    ("相邻 34 / 相接 14", 14, DARK, True),
    ("多条件组合筛选", 12.5, GREY),
    ("地图叠加 · 点击看详情", 12.5, GREY),
], line_gap=1.25)

# =========================================================
# 第 11 页 多园林数据库接入
# =========================================================
s = new_slide("多园林数据库接入", 11)
add_image_fit(s, os.path.join(SHOTS, "04b-garden-table.png"), 0.5, 1.3, 7.3, 5.6)
add_image_fit(s, os.path.join(SHOTS, "11-garden-switcher.png"), 8.1, 1.3, 4.7, 2.4)
add_text(s, 8.1, 3.95, 4.7, 3.0, [
    ("SHOW DATABASES 自动发现", 14, DARK, True),
    ("新库加载零配置接入", 12.5, GREY),
    ("",),
    ("园林切换器", 14, DARK, True),
    ("23 园一键切换 · 全页面联动", 12.5, GREY),
    ("",),
    ("工程健壮性", 14, DARK, True),
    ("名称映射 · 空库排除 · 23 库体检", 12.5, GREY),
], line_gap=1.25)

# =========================================================
# 第 12 页 平台展示效果
# =========================================================
s = new_slide("平台展示效果", 12)
cells = [
    ("07-spatial-layout.png", "空间布局"),
    ("08-relation-network.png", "知识网络"),
    ("09-route-playing.png", "游线分析"),
    ("10-spatial-filtered.png", "空间关系"),
    ("12-path-spatial.png", "路径查询"),
    ("07b-node-detail.png", "节点详情"),
]
cx = [0.5, 4.75, 9.0]
cy = [1.35, 4.25]
for i, (fn, cap) in enumerate(cells):
    x, y = cx[i % 3], cy[i // 3]
    add_image_fit(s, os.path.join(SHOTS, fn), x, y, 3.85, 2.55)
    add_text(s, x, y + 2.58, 3.85, 0.3, cap, size=11, color=GREY, align=PP_ALIGN.CENTER)

# =========================================================
# 第 13 页 项目成果总结
# =========================================================
s = new_slide("项目成果总结", 13)
rows = [
    ("园林知识图谱库", "23 园 · 718 节点 · 1905 关系"),
    ("后端只读接口", "13 个（全部实测通过）"),
    ("前端功能页面", "8 个 + 节点详情面板"),
    ("空间语义数据", "9 园完整游线环线（最长 28 站）"),
    ("测试与文档", "11 步端到端回归 + 23 库体检 + 4 份设计文档"),
]
y = 1.7
for label, val in rows:
    add_rect(s, 0.7, y, 0.12, 0.62, fill=TEAL)
    add_text(s, 1.0, y, 3.4, 0.62, label, size=15, bold=True, color=DARK, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, 4.6, y, 4.4, 0.62, val, size=14, color=GREY, anchor=MSO_ANCHOR.MIDDLE)
    y += 0.92
add_placeholder(s, 9.3, 1.7, 3.5, 4.9, "（可选：平台全景截图）")

# =========================================================
# 第 14 页 创新点
# =========================================================
s = new_slide("创新点", 14)
add_text(s, 0.5, 1.5, 7.2, 5.3, [
    ("① 空间语义三层模型", 16, DARK, True),
    ("位置层—关系层—游线层：知识图谱拓展为空间知识图谱", 13, GREY),
    ("",),
    ("② 真实坐标平面图还原", 16, DARK, True),
    ("测绘坐标直接渲染空间格局，非示意性布局", 13, GREY),
    ("",),
    ("③ 游览动线数据驱动复原", 16, DARK, True),
    ("环线序号自动提取闭环游线并动画呈现", 13, GREY),
    ("",),
    ("④ 全动态 Schema 架构", 16, DARK, True),
    ("标签 / 关系 / 属性运行时读取，23 园差异零改动适配", 13, GREY),
    ("",),
    ("⑤ 面向数据缺陷的鲁棒设计", 16, DARK, True),
    ("无坐标回退质心 · 缺数据优雅降级 · 稳定 ID 合并", 13, GREY),
], line_gap=1.28)
add_placeholder(s, 8.1, 1.5, 4.7, 5.0, "空间语义三层模型示意图（自绘）")

# =========================================================
# 第 15 页 后续工作
# =========================================================
s = new_slide("后续工作", 15)
add_text(s, 0.5, 1.7, 12.3, 3.9, [
    ("01  数据补全", 16, DARK, True),
    ("14 个园林补全空间语义数据（坐标 / 相邻 / 相接 / 环线），实现全库空间功能覆盖", 13.5, GREY),
    ("",),
    ("02  大语言模型智能问答", 16, DARK, True),
    ("接口设计已预留：动态 Schema 注入 + 只读 Cypher 校验", 13.5, GREY),
    ("",),
    ("03  多模态数据融合", 16, DARK, True),
    ("关联历史文献、园林图像、测绘图纸", 13.5, GREY),
    ("",),
    ("04  空间分析深化与数字复原", 16, DARK, True),
    ("视域 / 对景分析 · 游览组织比较 · 空间推演", 13.5, GREY),
], line_gap=1.3)
add_text(s, 0.5, 5.85, 12.3, 0.9, "谢谢聆听 · 请各位老师批评指正", size=24, bold=True, color=TEAL, align=PP_ALIGN.CENTER)

prs.save(OUT)
print("已生成:", OUT)
