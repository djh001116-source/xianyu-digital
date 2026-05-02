"""
闲鱼数字商品升级策略分析
用途：在不上架新商品的情况下，分析现有问题、给出升级方案
"""
import json, os
from pathlib import Path

BASE = Path("/Users/dengjiahao/Documents/xianyu-digital")
CONFIG = BASE / "config"
PWD = os.getcwd()

print("=" * 60)
print("  闲鱼数字商品 — 现状诊断")
print("=" * 60)

# 1. 检查现有的已发布商品
published_log = CONFIG / "published_log.json"
if published_log.exists():
    data = json.loads(published_log.read_text())
    print(f"\n📋 发布记录: {json.dumps(data, ensure_ascii=False, indent=2)}")

# 2. 检查所有生成过的图片
from datetime import datetime
product_files = sorted([f for f in os.listdir(BASE / "products") 
                       if f.endswith(('.jpg','.png'))])
print(f"\n🖼️  商品图片数: {len(product_files)}")
for f in product_files:
    path = BASE / "products" / f
    sz = path.stat().st_size
    print(f"     {sz//1024:>3}KB  {f}")

# 3. 检查 cookie 有效性
cookie_file = CONFIG / "goofish_cookies.json"
if cookie_file.exists():
    cookies = json.loads(cookie_file.read_text())
    print(f"\n🍪 Cookie: {len(cookies)} 个存储")
    # Check for expiry
    expired = 0
    for c in cookies:
        if 'expires' in c:
            import time
            if c['expires'] < time.time():
                expired += 1
    if expired > 0:
        print(f"   ⚠️  有 {expired} 个已过期")
    else:
        print(f"   ✅ Cookie 均未过期")
else:
    print(f"\n🍪 Cookie: 未找到")

# 4. 发布脚本中的设计模板简单度评估  
print(f"\n📐 设计策略评估:")
print(f"    当前: Pillow 随机圆形/矩形/线条")
print(f"    评分: 1/3 (简陋)")
print(f"    问题: 缺少真正的设计元素(文字排版、渐变、图标)")

# 5. 竞品分析总结
print(f"\n📊 竞争分析:")
print(f"    手账素材: ¥3-15, 多为精美实拍/设计稿")
print(f"    壁纸类: ¥2-10, 需要视觉冲击力")
print(f"    填色画: ¥5-20, 需要展示内页内容")
print(f"    模板类: ¥5-30, 需要展示功能示意图")

# 6. 建议策略
print(f"\n🎯 建议策略:")
print(f"    1. 保留现有已上架商品（已有点击和曝光沉淀）")
print(f"    2. 专注用 Claude Code 生成高质量 SVG 设计代替 Pillow 绘制")
print(f"    3. 每品类只做 3-5 个精品的，不做粗放批量")
print(f"    4. 价格上浮 50-100% (从 ¥3-8 提到 ¥8-15)")
print(f"    5. 增加品类: 大人向填色画(禅绕画风格)、周计划/月计划模板")
print(f"    6. 在现有 4 个商品基础上，每周增加 3-5 个高质量新商品")

print(f"\n{'='*60}")
print(f"  建议第一步：用 Claude Code 生成第一批高质量 SVG")
print(f"  同时升级现有 4 个商品的描述和主图")
print(f"{'='*60}")
