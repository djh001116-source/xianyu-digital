"""直接去用户的闲鱼闲置页，查看已发布的商品"""
import json, os, time
from pathlib import Path

CONFIG_DIR = Path("/Users/dengjiahao/Documents/xianyu-digital/config")
COOKIE_FILE = CONFIG_DIR / "goofish_cookies.json"

def main():
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
        )
        
        if COOKIE_FILE.exists():
            with open(COOKIE_FILE) as f:
                context.add_cookies(json.load(f))
        
        page = context.new_page()
        
        # Try to access user's idle items page
        # First find user ID from the page
        page.goto("https://www.goofish.com/", timeout=30000, wait_until="domcontentloaded")
        time.sleep(4)
        
        # Check if logged in
        is_logged_in = "登录" not in (page.evaluate("document.body.innerText") or "")[:500]
        print(f"登录状态: {'✅ 已登录' if is_logged_in else '❌ 未登录'}")
        
        if not is_logged_in:
            print("⏳ 请扫码登录...\n（手机淘宝扫一扫）")
            for i in range(60):
                time.sleep(5)
                body = page.evaluate("document.body.innerText") or ""
                if "登录" not in body[:200]:
                    print("✅ 登录成功！")
                    cookies = context.cookies()
                    with open(COOKIE_FILE, "w") as f:
                        json.dump(cookies, f)
                    break
                if i % 6 == 0:
                    print(f"  等待中... ({i*5+5}秒)")
        
        # Find user link/ID
        user_url = page.evaluate("""() => {
            // Find any link that has the user's name
            const links = document.querySelectorAll('a');
            for (const link of links) {
                const text = (link.innerText || '').trim();
                if (text.includes('肉丸')) {
                    return link.href || link.getAttribute('href') || '';
                }
            }
            // Check for user info in the page's global variables
            return '';
        }""")
        
        print(f"用户链接: {user_url}")
        
        # Try the user profile/idle items URL
        if user_url:
            if user_url.startswith('/'):
                user_url = f"https://www.goofish.com{user_url}"
            
            page.goto(user_url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(5)
            page.screenshot(path=str(CONFIG_DIR / "user_items.png"), full_page=True)
            
            # Check what's on the user page
            user_state = page.evaluate("""() => {
                const result = {};
                result.title = document.title;
                result.url = window.location.href;
                result.content = document.body.innerText.substring(0, 2000);
                
                // Find item-like elements
                const els = document.querySelectorAll('[class*="card"], [class*="item"], [class*="list"], [class*="goods"], li');
                result.elements = Array.from(els).slice(0, 20).map(el => ({
                    text: (el.innerText || '').trim().substring(0, 80),
                    tag: el.tagName,
                    cls: (el.className || '').substring(0, 40),
                }));
                
                return result;
            }""")
            
            print(f"\n=== 用户页面 ===")
            print(f"URL: {user_state.get('url', '')}")
            print(f"标题: {user_state.get('title', '')}")
            print(f"\n内容片段:")
            print(user_state.get('content', '')[:1000])
        else:
            # Try going to a standard user items URL
            print("未找到用户链接，尝试搜索用户ID...")
            
            # Search for '肉丸Mibo'
            page.goto("https://www.goofish.com/search?q=肉丸Mibo", timeout=30000, wait_until="domcontentloaded")
            time.sleep(5)
            page.screenshot(path=str(CONFIG_DIR / "search_user.png"), full_page=True)
            
            user_state = page.evaluate("""() => {
                return {
                    url: window.location.href,
                    content: document.body.innerText.substring(0, 2000),
                    has_user: document.body.innerText.includes('肉丸'),
                };
            }""")
            print(f"\n搜索用户结果:")
            print(user_state.get('content', '')[:1000])
        
        browser.close()

if __name__ == "__main__":
    main()
