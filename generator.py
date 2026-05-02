"""
DeepSeek SVG 设计生成器 v2.0
升级版 — 引入专业设计系统、anti-AI-slop 规则、设计审核管道

知识来源：
- nexu-io/open-design (MIT) — anti-ai-slop.md, color.md, typography.md
- ximinng/LLM4SVG — LLM SVG 生成方法论
- GoogleChromeLabs/ProjectVisBug — 设计工具参考
"""
import json, os, sys, re, base64, random
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()
PRODUCTS_DIR = PROJECT_ROOT / "products"
CONFIG_DIR = PROJECT_ROOT / "config"
DESIGN_SYSTEMS_DIR = PROJECT_ROOT / "design_systems"

for d in [PRODUCTS_DIR, CONFIG_DIR, DESIGN_SYSTEMS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# API
DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"

def _get_key():
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        env_path = Path.home() / "Documents/auto-dropship/.env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("DEEPSEEK_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    return key

def call_deepseek(system, user, temp=0.6, max_tokens=8000):
    """DeepSeek API 调用"""
    import urllib.request
    key = _get_key()
    if not key:
        raise ValueError("No API key")

    body = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temp,
        "max_tokens": max_tokens,
    }).encode()

    req = urllib.request.Request(
        DEEPSEEK_API,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        }
    )
    resp = urllib.request.urlopen(req, timeout=120)
    data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()

# ============================================================
# 专业调色板系统 (OKLch-based, from open-design color.md)
# 避免 AI 默认色（Tailwind indigo / 蓝紫渐变 / 随机 RGB）
# ============================================================

PALETTES = {
    # 日式侘寂 — 温暖米色、陶土、墨色
    "wabi-sabi": {
        "bg": "#F5F0EB", "surface": "#EDE6DC", "fg": "#3D3A36",
        "muted": "#A89F94", "border": "#D5CDC2", "accent": "#8B7355",
        "description": "日式侘寂风 — 温暖质朴，适合手账/Planner",
    },
    # 斯堪的纳维亚 — 白色、浅灰、雾蓝
    "scandinavian": {
        "bg": "#FAFAFA", "surface": "#F0F0F0", "fg": "#2D2D2D",
        "muted": "#9CA3AF", "border": "#E5E5E5", "accent": "#5B7B9A",
        "description": "北欧极简 — 干净通透，适合日程/效率工具",
    },
    # 莫兰迪柔和 — 灰粉、雾紫、燕麦
    "morandi": {
        "bg": "#F8F4F0", "surface": "#F0EAE4", "fg": "#3C3633",
        "muted": "#B5ADA4", "border": "#E0D8D0", "accent": "#9B7B7B",
        "description": "莫兰迪柔和 — 温柔有质感，适合女性向设计",
    },
    # 暗色调高级 — 深灰、炭黑、金
    "dark-luxury": {
        "bg": "#1A1A1A", "surface": "#2A2A2A", "fg": "#E8E8E8",
        "muted": "#8A8A8A", "border": "#3A3A3A", "accent": "#C4A96A",
        "description": "暗黑高级 — 质感商务，适合名片/发票/邀请函",
    },
    # 森林自然 — 鼠尾草绿、米白、木色
    "forest": {
        "bg": "#F4F1EA", "surface": "#EAE5DA", "fg": "#3A3A35",
        "muted": "#A8A095", "border": "#D5CDC2", "accent": "#6B8E6B",
        "description": "自然清新 — 适合植物/环保/健康主题",
    },
    # 现代黑白的专业感灰度
    "corporate": {
        "bg": "#FCFCFC", "surface": "#F2F2F2", "fg": "#1C1C1C",
        "muted": "#888888", "border": "#D8D8D8", "accent": "#2C2C2C",
        "description": "商务专业 — 干净利落，适合发票/合同/商务模板",
    },
}

# ============================================================
# 字体系统 (from open-design typography.md)
# ============================================================

FONT_SYSTEMS = {
    "academic": "'STSong', 'SimSun', 'Noto Serif SC', serif",
    "modern": "'PingFang SC', 'Microsoft YaHei', 'Hiragino Sans', sans-serif",
    "handwriting": "'STKaiti', 'KaiTi', 'ZCOOL XiaoWei', serif",
    "editorial": "'STSong', 'Noto Serif SC', 'Source Han Serif SC', serif",
    "functional": "'PingFang SC', 'Hiragino Sans', 'Noto Sans SC', sans-serif",
}

# ============================================================
# 商品品类模板 v2 — 品类设计更真实，手工感更强
# ============================================================
PRODUCT_TEMPLATES = [
    {
        "name": "weekly-planner-jp",
        "category": "周计划/日程管理",
        "title": "日式极简周计划表 • Weekly Planner 可打印PDF",
        "price": 9,
        "palette": "wabi-sabi",
        "font_system": "modern",
        "design_brief": """日式侘寂风格的每周计划表。
色调：温暖米色 #F5F0EB 底色，陶土棕 #8B7355 点缀，墨色 #3D3A36 文字。
包含：Mon-Sun日期列、6AM-10PM时间轴（半小时间隔）、Priority区域（5行带复选框）、Bucket List（3行）、Notes区域。
标题 WEEKLY PLANNER 用粗体，副标题用小字英文日期。
布局：上半部分为标题+时间轴，下半部分三栏（Priority/Bucket/Notes）。
边框：细水墨感的设计。不要任何AI感的花哨装饰。""",
        "style": "wabi-sabi",
    },
    {
        "name": "daily-planner-minimal",
        "category": "日程管理",
        "title": "极简一日一页计划表 • Daily Log 时间管理模板",
        "price": 8,
        "palette": "scandinavian",
        "font_system": "functional",
        "design_brief": """斯堪的纳维亚风格的一日一页计划表。
色调：纯白 #FAFAFA 底色，浅灰 #F0F0F0 分区，雾蓝 #5B7B9A 点缀，深灰 #2D2D2D 文字。
包含：日期头区域（Today is... + 天气/心情图标）、6AM-12AM时间轴（半小时间隔、竖线列表式）、今日Top3任务（带优先级标记）、饮水追踪（8杯格）、心情记录（笑脸滑块）、Notes区域。
标题用 TODAY 英文加日期副标题。
布局：左边时间轴（约占3/5），右边是任务+追踪区（约占2/5）。
不要多余的渐变和装饰。干净到极致。""",
        "style": "scandinavian",
    },
    {
        "name": "zentangle-coloring",
        "category": "填色画/解压",
        "title": "曼陀罗禅绕画填色本 • Zentangle Coloring 解压涂色",
        "price": 12,
        "palette": "wabi-sabi",
        "font_system": "modern",
        "design_brief": """黑线白底的曼陀罗禅绕画填色页。
色调：纯白背景，纯黑线条（#1A1A1A）。
精细的同心圆曼陀罗图案，线条丰富且密，适合成人解压涂色。
结构：中心为小圆花，向外扩散3-4层同心几何图案（花瓣/波纹/锯齿/菱形交替）。
线条粗细：中心细节0.5-1px，外圈2-3px。
外圈有装饰性边框线（带小圆圈节点）。
纯线条设计，无文字，无颜色填充。
纯SVG路径绘制，不依赖图片。打印友好，高对比度。""",
        "style": "zentangle-mandala",
    },
    {
        "name": "phone-wallpaper-set",
        "category": "手机壁纸",
        "title": "极简高级感手机壁纸 • 抽象渐变 4张套装",
        "price": 5,
        "palette": "morandi",
        "font_system": "modern",
        "design_brief": """莫兰迪色系的高级感抽象壁纸。
色调：灰粉 #9B7B7B / 雾蓝 #7B9B9B / 燕麦 #C4A98B / 鼠尾草绿 #8BA88B — 任选一种为主色。
每张仅使用该主色系的1-2个相近色做渐变或几何叠层。
抽象形态：大块几何色块叠加（圆/方/弧），边缘柔和模糊。
无文字干扰。无装饰性线条。
比例：1080x1920px（竖屏）。
风格：干净大气，ins风，留白70%以上。
每张设计不同，但保持色调一致。""",
        "style": "abstract-gradient",
    },
    {
        "name": "monthly-planner",
        "category": "日程管理",
        "title": "极简月计划表 • Monthly Calendar 月度规划模板",
        "price": 8,
        "palette": "scandinavian",
        "font_system": "functional",
        "design_brief": """北欧极简风格的月历计划表。
色调：纯白底色 #FAFAFA，浅灰分隔线 #E5E5E5，深灰文字 #2D2D2D，雾蓝点缀 #5B7B9A。
包含：月份标题（MONTHLY PLANNER 英文+中文月份副标题）、31天日期格（每格约65x65px，右上角标日期数字）、Month Goals区域（3行带复选框）、Top 3 Priorities（编号列表）、Notes区域。
日历格内留白，方便填写。
设计：仅用极细线条（0.5px）分割日期格。没有圆角大卡片，没有彩色标签。干净到像一本Moleskine。""",
        "style": "minimal-modern",
    },
    {
        "name": "habit-tracker",
        "category": "习惯追踪",
        "title": "习惯追踪打卡表 • Habit Tracker 月度模板",
        "price": 7,
        "palette": "forest",
        "font_system": "modern",
        "design_brief": """月度习惯追踪打卡表。
色调：鼠尾草绿 #6B8E6B 点缀，米白底色 #F4F1EA，木色文字 #3A3A35。
左侧竖排列出10种习惯（阅读/运动/早起/冥想/写作/饮水/学习/记账/清淡饮食/早睡）。
右侧是31天的打卡格（每格圆形或方形，直径约12px）。
每行习惯用不同深浅的绿色做打卡格背景色阶。
标题：HABIT TRACKER 英文+中文副标题。
底部：月度统计区（完成率%、连续打卡天数、最佳习惯）。
设计：手账风格，淡彩格子。不要AI感的花哨图标。""",
        "style": "colorful-dot",
    },
    {
        "name": "gratitude-journal",
        "category": "日记/手账",
        "title": "感恩日记内页 • Gratitude Journal 每日记录模板",
        "price": 8,
        "palette": "morandi",
        "font_system": "handwriting",
        "design_brief": """感恩日记页面，温暖的莫兰迪柔粉色调。
底色 #F8F4F0，柔粉点缀 #9B7B7B，褐色文字 #3C3633。
包含：
- 日期栏（线框内填日期）
- "Today I'm Grateful For" 区域（3行横线，下方空行手写）
- "Today's Highlight" 区域（留白+横线）
- "A Kindness I Received"（2行）
- "Affirmation of the Day"（1行+引号装饰）
标题用 GRATITUDE · 感恩日记。
底部角落有一支小小的手绘花朵线稿（极简）。
整体像一本精致的纸质日记本内页，不是数字模板。""",
        "style": "warm-journal",
    },
    {
        "name": "meal-planner",
        "category": "饮食规划",
        "title": "一周饮食计划表 • Weekly Meal Planner 打印模板",
        "price": 7,
        "palette": "forest",
        "font_system": "functional",
        "design_brief": """一周饮食计划表，清新的绿色调。
底色 #F4F1EA，鼠尾草绿 #6B8E6B 点缀，深色文字 #3A3A35。
7列（Mon-Sun）x 4行（Breakfast / Lunch / Dinner / Snack）。
每单元格为40x50px左右，内留白方便手写。
右侧：Grocery List 区域（带复选框的购物清单，预留10行）。
标题：WEEKLY MEAL PLANNER。
设计风格：极简表格，仅用0.5px细线分割。
食品类用小写英文标注（eggs, milk, bread...）作装饰性提示。
没有插图，没有表情符号。干净利落的家庭实用模板。""",
        "style": "fresh-green",
    },
    {
        "name": "study-planner",
        "category": "学习工具",
        "title": "学霸学习计划表 • Study Schedule 高效备考模板",
        "price": 8,
        "palette": "scandinavian",
        "font_system": "functional",
        "design_brief": """学习计划表，冷静的蓝灰色系。
底色 #FAFAFA，浅灰分区 #F0F0F0，雾蓝点缀 #5B7B9A。
包含：
- 上半部分：科目时间表（周一到周日 x 7AM-11PM），每格可填写学习内容
- 中间：Priority Tasks 区域（3个优先任务编号列表）
- 右下：Progress Tracking（今日完成度% — 用半圆形进度环表示）
- 底部：Revision Notes（4行横线留白）
标题：STUDY SCHEDULE。
设计：像一门严肃的学习工具，不是花哨的app界面。
没有图标，没有插画，只有排版的力量。""",
        "style": "study-blue",
    },
    {
        "name": "invoice-template",
        "category": "商务模板",
        "title": "简约商务发票模板 • Professional Invoice A4",
        "price": 6,
        "palette": "corporate",
        "font_system": "modern",
        "design_brief": """专业商务发票模板。
色调：纯白 #FCFCFC 底色，深灰 #1C1C1C 文字，纯黑 #2C2C2C 作为强调。
包含：
- 顶部：公司名/Logo占位区（左侧）+ INVOICE大字标题（右侧）+ 发票编号/日期
- Bill To 区域（地址/邮箱/电话）
- 表格：Description / Quantity / Unit Price / Total（4列表格）
- Subtotal / Tax / Total 行（总金额加粗）
- 底部：Payment Info（银行账户/支付宝/VX）+ Thank You 结束语
设计：仅用1px黑色细线构建表格。无颜色，无装饰。
就如同一份打印出来的专业发票。干净、可信、商务。""",
        "style": "corporate-clean",
    },
]

# ============================================================
# 专业 SVG 设计系统提示词 v2
# 整合 open-design 的 anti-ai-slop 规则 + 色彩系统 + 字体系统
# ============================================================

DESIGN_SYSTEM_PROMPT = """You are a SENIOR PRINT DESIGNER with 20 years of experience creating printable templates for stationery, planners, and paper goods. You work for a premium independent brand. Your designs are sold in boutique stationery stores.

CRITICAL: You must NEVER use these AI-slop patterns. They are immediate tells of AI-generated design:

FORBIDDEN:
1. ❌ Indigo/purple as accent color (#6366f1, #4f46e5, #8b5cf6, #7c3aed - the "Tailwind indigo" palette)
2. ❌ Blue-to-purple/indigo-to-pink gradients on hero sections
3. ❌ Emoji as icons (★ ✨ 🚀 🎯 ⚡ 🔥 💡) in headings or buttons
4. ❌ Sans-serif on display text when brief specifies serif
5. ❌ Rounded cards with colored left-border accent (the "AI dashboard tile")
6. ❌ Perfectly symmetric layouts — good design has tension and breathing room
7. ❌ Decorative blob/wave SVG backgrounds with no purpose
8. ❌ Two-stop "trust" gradients (purple→blue, blue→cyan)
9. ❌ Fake metrics ("10x faster", "99.9% uptime")
10. ❌ Filler copy (lorem ipsum, "feature one / two / three")

COLOR RULES:
- Neutrals occupy 70-90% of visual area. Accent is used at most 2 times per design.
- NEVER use pure black (#000) or pure white (#fff). Use off-white (#fafafa) and near-black (#1a1a1a).
- Name color tokens by purpose, not hue.
- Maintain minimum 4.5:1 contrast for body text.

DESIGN PHILOSOPHY:
- ~80% proven patterns + ~20% distinctive choice. The 20% is: one bold visual move, voice in microcopy, one detail only a real designer would think of.
- If a reviewer can identify which brand/product this design is from without seeing a logo — it has soul. If not, it's a template.
- Use asymmetrical whitespace. Alternate density (one tight section, one breathing section).
- Every line must serve a purpose. If it doesn't help the user organize their life, remove it.

TECHNICAL REQUIREMENTS:
- Output ONLY valid SVG code. No markdown, no explanation, no wrapper.
- Size: 800x1000px, viewBox="0 0 800 1000"
- Use <style> in <defs> for all styling
- System fonts: include 'PingFang SC', 'Microsoft YaHei', 'Hiragino Sans', 'Noto Sans SC'
- Grid lines: 0.5-1px stroke-width, subtle
- Include a thin border (1-2px) around the full design
- Text alignment must be consistent throughout
- All Chinese text, English subtitles only for aesthetic"""

# ============================================================
# SVG 质量检查 (设计审核管道)
# ============================================================

SVG_QUALITY_CHECKS = {
    "has_svg_tag": lambda svg: svg.strip().startswith("<svg"),
    "has_closing_tag": lambda svg: "</svg>" in svg,
    "has_style_tag": lambda svg: "<style>" in svg,
    "has_viewbox": lambda svg: "viewBox" in svg,
    "no_emoji_icons": lambda svg: not re.search(r'[✦🚀🎯⚡🔥💡✨🌟]', svg),
    "no_indigo_accent": lambda svg: not any(c in svg for c in ["#6366f1", "#4f46e5", "#8b5cf6", "#7c3aed"]),
    "no_pure_black_bg": lambda svg: ('#000000' not in svg[:200]) or ('fill="#000000"' not in svg[:200]),
    "no_pure_white_bg": lambda svg: ('#ffffff' not in svg[:200]) or ('fill="#ffffff"' not in svg[:200]),
    "has_chinese_text": lambda svg: bool(re.search(r'[\u4e00-\u9fff]', svg)) if ('coloring' not in svg[:500].lower() and 'wallpaper' not in svg[:500].lower()) else True,
    "size_reasonable": lambda svg: 500 < len(svg) < 50000,
}

def validate_svg_quality(svg_content: str) -> dict:
    """运行质量检查，返回检查结果"""
    results = {}
    for check_name, check_fn in SVG_QUALITY_CHECKS.items():
        try:
            results[check_name] = check_fn(svg_content)
        except Exception:
            results[check_name] = False
    return results

def format_qa_report(results: dict) -> str:
    """格式化质量报告"""
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    lines = [f"  设计审核: {passed}/{total} 项通过"]
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        label = name.replace("_", " ").title()
        lines.append(f"    {icon} {label}")
    if failed > 0:
        lines.append(f"  ⚠️  {failed} 项不合格，建议重新生成")
    return "\n".join(lines)


# ============================================================
# SVG 生成函数 v2
# ============================================================

def generate_svg_design(design_brief: str, palette: str, font_system: str) -> str:
    """用 DeepSeek 生成专业 SVG 设计稿"""
    palette_info = PALETTES.get(palette, PALETTES["wabi-sabi"])
    font_stack = FONT_SYSTEMS.get(font_system, FONT_SYSTEMS["modern"])

    user_prompt = f"""Design a printable digital product SVG for 闲鱼 Chinese marketplace.

DESIGN BRIEF:
{design_brief}

COLOR PALETTE:
Background: {palette_info['bg']}
Surface: {palette_info['surface']}
Foreground: {palette_info['fg']}
Muted: {palette_info['muted']}
Border: {palette_info['border']}
Accent: {palette_info['accent']}

FONT STACK:
{font_stack}

PALETTE STYLE: {palette_info['description']}

CRITICAL — DO NOT USE:
- Indigo/purple colors (#6366f1, #4f46e5, #8b5cf6, #7c3aed)
- Emoji in the design
- Purple→blue gradients
- Rounded cards with left border
- Decorative blobs/waves
- Lorem ipsum or filler copy
- Perfectly symmetric layouts

INSTEAD:
- Use the EXACT hex values from the palette above — no deviations
- Asymmetrical composition with intentional whitespace
- ~80% neutral colors, accent used sparingly (max 2 times)
- Off-white (#fafafa) and near-black (#1a1a1a) for extremes
- Real Chinese text content that makes sense for the template

Output ONLY the SVG code, nothing else. Begin with <svg and end with </svg>."""

    svg = call_deepseek(DESIGN_SYSTEM_PROMPT, user_prompt, temp=0.6, max_tokens=12000)

    # Strip markdown code blocks if present
    svg = re.sub(r'^```svg\s*', '', svg, flags=re.MULTILINE)
    svg = re.sub(r'^```\s*', '', svg, flags=re.MULTILINE)
    svg = svg.strip()

    # Validate SVG
    if not svg.startswith('<svg'):
        print(f'  [WARN] Response does not start with <svg: {svg[:100]}')

    if '</svg>' not in svg:
        print(f'  [WARN] SVG may be truncated! {len(svg)} chars, no closing </svg>')

    return svg


def svg_to_png(svg_content: str, output_path: str, width=800, height=1000):
    """用 Playwright 将 SVG 直接渲染为 PNG"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": height})
        html = f'<html><body style="margin:0;background:white">{svg_content}</body></html>'
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.screenshot(path=output_path, full_page=False)
        browser.close()


def generate_listing_copy(theme_name: str, title: str, price: int, category: str) -> dict:
    """用 DeepSeek 生成闲鱼商品文案"""
    prompt = f"""Generate a product listing for 闲鱼 (Chinese marketplace) for a digital product.

Product: {theme_name}
Title: {title}
Price: ¥{price}
Category: {category} (digital/printable)

Output JSON:
- title: (max 15 Chinese characters for 闲鱼 title, catchy and benefit-driven)
- description: (30-60 Chinese characters, describe real usage scenarios and specific benefits)
- tags: (3-5 Chinese tags, be specific not generic)
- selling_points: (3 bullet points, each must be a concrete benefit not a vague claim)

Output ONLY JSON, no other text."""

    result = call_deepseek(
        "You are an expert e-commerce copywriter. Write compelling, specific, benefit-driven listings. Avoid clichés like '提升效率', '精美设计'. Be specific about what the product contains and who it helps.",
        prompt,
        temp=0.8,
        max_tokens=800,
    )

    try:
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(result)
    except:
        print(f"  [WARN] Parse failed, using defaults: {result[:100]}")
        return {
            "title": title,
            "description": f"可直接打印的{category}模板。包含完整设计排版，适合日常使用。购买后提供网盘下载链接。",
            "tags": [category, "模板", "电子版", "可打印", "设计"],
            "selling_points": ["可直接打印使用", "精心排版设计", "电子版下载永久拥有"],
        }


# ============================================================
# 主流水线 v2
# ============================================================

def run_pipeline(count=None):
    """完整流水线：生成 SVG 设计 → 质量审核 → 转 PNG → 生成文案"""
    import time

    products = PRODUCT_TEMPLATES[:count] if count else PRODUCT_TEMPLATES

    print(f"DeepSeek SVG Designer v2.0 — 专业设计系统版")
    print(f"品类数: {len(products)}")
    print("=" * 50)

    results = []
    quality_report = []

    for i, prod in enumerate(products, 1):
        ts = int(time.time())
        print(f"\n[{i}/{len(products)}] {prod['name']}...")
        print(f"  调色板: {prod.get('palette', 'wabi-sabi')}")
        print(f"  字体: {prod.get('font_system', 'modern')}")

        # Step 1: Generate SVG with design system
        print(f"  ① 生成 SVG 设计稿...")
        svg = generate_svg_design(
            prod['design_brief'],
            prod.get('palette', 'wabi-sabi'),
            prod.get('font_system', 'modern')
        )
        svg_path = PRODUCTS_DIR / f"{prod['name']}_{ts}.svg"
        svg_path.write_text(svg)
        print(f"     ✓ SVG: {len(svg)} chars saved")

        # Step 2: Quality check
        print(f"  ② 设计质量审核...")
        qa_results = validate_svg_quality(svg)
        qa_text = format_qa_report(qa_results)
        print(f"     {qa_text.replace(chr(10), chr(10)+'     ')}")
        quality_report.append({
            "name": prod['name'],
            "passed": sum(1 for v in qa_results.values() if v),
            "total": len(qa_results),
            "fails": [k for k, v in qa_results.items() if not v],
        })

        # If too many fails, regenerate once with warning
        fail_count = sum(1 for v in qa_results.values() if not v)
        if fail_count > 2:
            print(f"     ⚠️  不合格项较多({fail_count})，重新生成一次...")
            svg = generate_svg_design(
                prod['design_brief'],
                prod.get('palette', 'wabi-sabi'),
                prod.get('font_system', 'modern')
            )
            svg_path.write_text(svg)
            qa_results = validate_svg_quality(svg)
            qa_text = format_qa_report(qa_results)
            print(f"     (重审) {qa_text.replace(chr(10), chr(10)+'     ')}")

        # Step 3: Convert to PNG
        print(f"  ③ 渲染为 PNG...")
        png_path = PRODUCTS_DIR / f"{prod['name']}_{ts}.png"
        svg_to_png(svg, str(png_path))
        png_size = png_path.stat().st_size // 1024
        print(f"     ✓ PNG: {png_size}KB")

        # Step 4: Generate listing copy
        print(f"  ④ 生成商品文案...")
        listing = generate_listing_copy(prod['name'], prod['title'], prod['price'], prod['category'])
        print(f"     ✓ 标题: {listing.get('title', prod['title'])}")
        print(f"     ✓ 价格: ¥{listing.get('price', prod['price'])}")
        print(f"     ✓ 描述: {listing.get('description', '')[:50]}...")

        results.append({
            "name": prod['name'],
            "category": prod['category'],
            "svg": str(svg_path),
            "png": str(png_path),
            "listing": listing,
            "price": listing.get('price', prod['price']),
            "quality_check": {
                "passed": sum(1 for v in qa_results.values() if v),
                "total": len(qa_results),
                "details": qa_results,
            },
        })

        # Brief delay to avoid rate limiting
        if i < len(products):
            wait_time = random.uniform(1.5, 3.0)
            time.sleep(wait_time)

    # Save results
    report = {
        "generated_at": __import__('datetime').datetime.now().isoformat(),
        "version": "v2.0-design-system",
        "total": len(results),
        "quality_summary": {
            "avg_pass_rate": f"{sum(r['passed'] for r in quality_report) / max(len(quality_report), 1) * 100 / max(len(SVG_QUALITY_CHECKS), 1):.0%}",
            "per_product": quality_report,
        },
        "products": results,
    }
    report_path = CONFIG_DIR / "generated_products.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    print(f"\n{'=' * 50}")
    print(f"生成完成！共 {len(results)} 个设计")
    print(f"质量报告: {report['quality_summary']['avg_pass_rate']} 平均通过率")
    print(f"报告文件: {report_path}")

    return results


if __name__ == "__main__":
    import argparse, random
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, help="生成数量")
    args = parser.parse_args()

    run_pipeline(count=args.count)
