"""验证商品列表"""
import json, os, time
from pathlib import Path

PROJECT_ROOT = Path("/Users/dengjiahao/Documents/xianyu-digital")
CONFIG_DIR = PROJECT_ROOT / "config"
COOKIE_FILE = CONFIG_DIR / "goofish_cookies.json"

def main():
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        
        with open(COOKIE_FILE) as f:
            context.add_cookies(json.load(f))
        
        page = context.new_page()
        page.goto("https://www.goofish.com/personal", timeout=30000, wait_until="domcontentloaded")
        time.sleep(5)
        
        # Get all listings
        body = page.evaluate("document.body.innerText") or ""
        print("=== 用户页面商品 ===")
        
        # Find all product-like entries
        lines = body.split('\n')
        products = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line: continue
            # Look for price patterns (¥ + number)
            if line.startswith('¥') and any(c.isdigit() for c in line):
                # The title is usually 1-2 lines before
                title = lines[i-1].strip() if i > 0 else ''
                if title and len(title) > 2 and len(title) < 30:
                    products.append(f"  {title} {line}")
        
        print(f"\n共 {len(products)} 个商品:")
        for p in products:
            print(f"  {p}")
        
        page.screenshot(path=str(CONFIG_DIR / "verify_all_products.png"), full_page=True)
        time.sleep(3)
        browser.close()

if __name__ == "__main__":
    main()
