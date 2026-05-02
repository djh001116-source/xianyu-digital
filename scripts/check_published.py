"""检查刚才发布的商品是否真的上架了"""
import json, os, time
from pathlib import Path

CONFIG_DIR = Path("/Users/dengjiahao/Documents/xianyu-digital/config")
COOKIE_FILE = CONFIG_DIR / "goofish_cookies.json"

def main():
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # visible so I can see
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
        )
        
        with open(COOKIE_FILE) as f:
            context.add_cookies(json.load(f))
        
        page = context.new_page()
        
        # Go to the user's shop/listings page
        print("打开用户主页/我的发布...")
        page.goto("https://www.goofish.com/", timeout=30000, wait_until="networkidle")
        time.sleep(4)
        
        # Try clicking on user avatar to get to profile
        page.screenshot(path=str(CONFIG_DIR / "homepage.png"), full_page=True)
        
        # Check if we can find "我的" navigation
        # Look for user name / profile link
        nav_state = page.evaluate("""() => {
            const result = {};
            
            // Find links/buttons with user info
            const links = document.querySelectorAll('a, button, [role="button"], [class*="user"], [class*="profile"], [class*="avatar"]');
            result.nav_items = Array.from(links).slice(0, 20).map(el => ({
                tag: el.tagName,
                text: (el.innerText || '').trim().substring(0, 30),
                href: el.href || '',
                cls: (el.className || '').substring(0, 40),
            }));
            
            // Find all spans/text that contain '我的' or '发布'
            result.my_text = [];
            document.querySelectorAll('*').forEach(el => {
                const t = (el.innerText || '').trim();
                if ((t.includes('我的') || t.includes('发布') || t.includes('卖出的') || t.includes('商品')) && t.length < 20 && t.length > 1) {
                    if (!result.my_text.find(x => x.text === t)) {
                        result.my_text.push({ tag: el.tagName, text: t });
                    }
                }
            });
            
            return result;
        }""")
        
        print("\n=== 导航 ===")
        for item in nav_state.get('nav_items', []):
            if item.get('text'):
                print(f"  {item['tag']}: {item['text']}")
        
        print("\n=== 包含关键词的文字 ===")
        for item in nav_state.get('my_text', [])[:15]:
            print(f"  <{item['tag']}> {item['text']}")
        
        browser.close()

if __name__ == "__main__":
    main()
