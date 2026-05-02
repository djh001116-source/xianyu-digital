"""
研究闲鱼上热卖的数字商品设计风格
不花钱的方法：打开闲鱼网页版，搜索关键词，截图分析
"""
import os, json, time
from pathlib import Path

CONFIG_DIR = Path("/Users/dengjiahao/Documents/xianyu-digital/config")
COOKIE_FILE = CONFIG_DIR / "goofish_cookies.json"

os.makedirs(CONFIG_DIR, exist_ok=True)

def main():
    from playwright.sync_api import sync_playwright
    
    categories = [
        "手账素材 电子版",
        "填色画 成人 电子版", 
        "手机壁纸 电子版",
        "planner 模板 电子版",
        "贴纸 素材 电子版",
        "PPT模板 电子版",
        "简历模板 电子版",
        "手写字体 电子版",
        "插画 素材 电子版",
        "笔记模板 电子版",
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
        )
        
        if COOKIE_FILE.exists():
            with open(COOKIE_FILE) as f:
                context.add_cookies(json.load(f))
        
        page = context.new_page()
        
        # Screenshot storage
        screenshots_dir = CONFIG_DIR / "research"
        screenshots_dir.mkdir(exist_ok=True)
        
        all_findings = {}
        
        for i, keyword in enumerate(categories):
            print(f"\n{'='*60}")
            print(f"[{i+1}/{len(categories)}] 搜索: {keyword}")
            print('='*60)
            
            try:
                page.goto(f"https://www.goofish.com/search?q={keyword}", 
                         timeout=30000, wait_until="domcontentloaded")
                time.sleep(5)
                
                # Get page content
                content = page.evaluate("document.body.innerText") or ""
                print(f"  页面长度: {len(content)} 字")
                
                # Screenshot
                fname = f"search_{keyword[:4]}_{int(time.time())}.png"
                page.screenshot(path=str(screenshots_dir / fname), full_page=True)
                print(f"  📸 截图: {fname}")
                
                # Extract product listings
                entries = extract_products(content, keyword)
                all_findings[keyword] = entries
                
                print(f"  找到 {len(entries)} 个商品摘要")
                for e in entries[:5]:
                    print(f"    • {e['title'][:40]} | {e['price']}")
                
            except Exception as ex:
                print(f"  ❌ 错误: {ex}")
            
            time.sleep(3)
        
        browser.close()
        
        # Save findings
        report_path = str(screenshots_dir / "research_summary.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(all_findings, f, ensure_ascii=False, indent=2)
        print(f"\n📄 研究报告已保存: {report_path}")
        
        # Generate summary
        print("\n\n" + "=" * 60)
        print("  研究摘要")
        print("=" * 60)
        for kw, entries in all_findings.items():
            prices = []
            for e in entries:
                try:
                    p = float(e['price'].replace('¥', '').replace('万', '0000').replace('.', ''))
                    if p < 1000:  # filter out real goods
                        prices.append(p)
                except:
                    pass
            avg = sum(prices)/len(prices) if prices else 0
            print(f"\n{kw}:")
            print(f"  商品数: {len(entries)}")
            print(f"  均价: ¥{avg:.1f}" if avg else "  均价: -")

def extract_products(text, keyword):
    """从页面文本中提取商品信息"""
    lines = text.split('\n')
    products = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if '¥' in line:
            price = line
            # Look back for title
            title = ""
            for j in range(i-1, max(0, i-5), -1):
                t = lines[j].strip()
                if t and len(t) > 2 and '¥' not in t and '肉丸' not in t and len(t) < 60:
                    title = t
                    break
            products.append({
                "title": title,
                "price": price,
                "source": keyword
            })
        i += 1
    return products

if __name__ == "__main__":
    main()
