"""查看用户页面完整的文本"""
import json, os, time
from pathlib import Path

CONFIG_DIR = Path("/Users/dengjiahao/Documents/xianyu-digital")
COOKIE_FILE = Path("/Users/dengjiahao/Documents/xianyu-digital/config/goofish_cookies.json")

def main():
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        
        with open(COOKIE_FILE) as f:
            context.add_cookies(json.load(f))
        
        page = context.new_page()
        
        # Go to personal page
        page.goto("https://www.goofish.com/personal", timeout=30000, wait_until="domcontentloaded")
        time.sleep(5)
        
        body = page.evaluate("document.body.innerText") or ""
        
        # Print all lines containing ¥ (prices)
        print("=== 含¥的行（商品价格行）===")
        for i, line in enumerate(body.split('\n')):
            line = line.strip()
            if '¥' in line:
                # Print context (3 lines before)
                lines = body.split('\n')
                idx = body.split('\n').index(line)
                start = max(0, idx-3)
                ctx = lines[start:idx+1]
                for c in ctx:
                    if c.strip():
                        print(f"  {c.strip()}")
                print("  ---")
        
        # Also check for specific keywords
        for kw in ["极简日程本", "花卉填色画", "复*壁纸", "贴纸", "设计接单"]:
            if kw in body:
                print(f"✅ 找到: {kw}")
            else:
                print(f"❌ 未找到: {kw}")
        
        # Get the whole body
        print(f"\n=== 页面原始内容（前2000字）===")
        print(body[:2000])
        
        page.screenshot(path=str(CONFIG_DIR / "personal_page_raw.png"), full_page=True)
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    main()
