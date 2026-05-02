"""
直接搜索刚发布的商品名来验证上架
"""
import json, os, time
from pathlib import Path

CONFIG_DIR = Path("/Users/dengjiahao/Documents/xianyu-digital/config")
COOKIE_FILE = CONFIG_DIR / "goofish_cookies.json"

def main():
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
        )
        
        with open(COOKIE_FILE) as f:
            context.add_cookies(json.load(f))
        
        page = context.new_page()
        
        # Go to user's profile/idle page
        # Try the standard xianyu user URL pattern
        print("尝试打开用户闲鱼主页...")
        
        # First, get user ID from the page
        page.goto("https://www.goofish.com/", timeout=30000, wait_until="networkidle")
        time.sleep(3)
        
        # Click on the user avatar/name to go to profile
        user_el = page.query_selector('a:has-text("肉丸Mibo")')
        if user_el:
            user_href = user_el.get_attribute('href')
            print(f"用户链接: {user_href}")
            page.goto(f"https://www.goofish.com{user_href}", timeout=30000, wait_until="networkidle")
            time.sleep(4)
            page.screenshot(path=str(CONFIG_DIR / "user_profile.png"), full_page=True)
        else:
            # Direct search for the product
            print("未找到用户链接，直接搜索商品...")
            page.goto("https://www.goofish.com/", timeout=30000, wait_until="networkidle")
            time.sleep(2)
        
        # Check if we can see any listings
        page_state = page.evaluate("""() => {
            const result = {};
            
            // Find all item/product cards
            const cards = document.querySelectorAll('[class*="card"], [class*="item"], [class*="product"], li, [class*="list-item"]');
            result.cards_count = cards.length;
            result.cards = Array.from(cards).slice(0, 10).map(c => ({
                text: (c.innerText || '').trim().substring(0, 80),
                cls: (c.className || '').substring(0, 40),
            }));
            
            // Page title
            result.title = document.title;
            
            // All links
            result.links = Array.from(document.querySelectorAll('a[href]')).slice(0, 15).map(a => ({
                text: (a.innerText || '').trim().substring(0, 30),
                href: a.href.substring(0, 100),
            }));
            
            return result;
        }""")
        
        print(f"\n=== 页面标题: {page_state['title']} ===")
        print(f"\n=== 商品卡片: {page_state['cards_count']} 个 ===")
        for c in page_state['cards']:
            if c['text']:
                print(f"  [{c['cls']}] {c['text']}")
        
        print("\n=== 链接 ===")
        for link in page_state['links']:
            if link['text']:
                print(f"  {link['text']} → {link['href']}")
        
        browser.close()

if __name__ == "__main__":
    main()
