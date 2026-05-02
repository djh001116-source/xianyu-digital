"""重新扫码登录后，直接搜索商品名验证是否发布成功"""
import json, os, time, sys
from pathlib import Path

CONFIG_DIR = Path("/Users/dengjiahao/Documents/xianyu-digital/config")
COOKIE_FILE = CONFIG_DIR / "goofish_cookies.json"

def main():
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # need user to scan QR code
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
        )
        
        # Load existing cookies if any
        if COOKIE_FILE.exists():
            try:
                with open(COOKIE_FILE) as f:
                    context.add_cookies(json.load(f))
            except:
                pass
        
        page = context.new_page()
        
        # Go to publish page — if not logged in, it will show login QR
        page.goto("https://www.goofish.com/publish", timeout=30000, wait_until="networkidle")
        time.sleep(5)
        
        # Check login status
        body = page.evaluate("document.body.innerText")
        needs_login = "登录" in body[:500] and ("二维码" in body[:500] or "扫码" in body[:500])
        
        if needs_login:
            print("⏳ Cookie 已过期，请重新扫码...")
            print("打开手机淘宝 → 扫一扫 → 扫码登录")
            
            # Wait for user to scan QR
            for i in range(60):  # 5 minutes max
                time.sleep(5)
                body = page.evaluate("document.body.innerText")
                if "登录" not in body[:200] or "肉丸" in body:
                    print("✅ 登录成功！")
                    break
                if i % 6 == 0:
                    print(f"  等待中... ({i*5+5}秒)")
            
            # Save cookies
            cookies = context.cookies()
            with open(COOKIE_FILE, "w") as f:
                json.dump(cookies, f)
            print(f"  Cookie 已保存 ({len(cookies)} 个)")
        else:
            print("✅ Cookie 有效，已登录")
        
        # Now search for the product
        print("\n搜索商品...")
        page.goto(f"https://www.goofish.com/search?q=极简日程本电子版6元", timeout=30000, wait_until="networkidle")
        time.sleep(5)
        
        # Take screenshot of search results
        page.screenshot(path=str(CONFIG_DIR / "search_result.png"), full_page=True)
        
        # Check search results
        search_state = page.evaluate("""() => {
            const result = {};
            
            // Find item cards in search results
            const items = document.querySelectorAll('[class*="item"], [class*="card"], [class*="goods"], li[class*="list"]');
            result.items = Array.from(items).slice(0, 15).map(el => ({
                text: (el.innerText || '').trim().substring(0, 100),
                cls: (el.className || '').substring(0, 40),
            }));
            
            // Any "no results" message
            result.no_result = document.body.innerText.includes('没有找到') || document.body.innerText.includes('暂无');
            
            // Count of items that mention our product
            result.content = document.body.innerText.substring(0, 1000);
            
            // Search for our product title
            const allText = document.body.innerText;
            result.has_product = allText.includes('极简日程本');
            result.has_price_6 = allText.includes('6') || allText.includes('六');
            
            return result;
        }""")
        
        print(f"\n=== 搜索结果 ===")
        if search_state.get('no_result'):
            print("❌ 没有搜索结果")
        print(f"   找到商品'极简日程本': {'✅' if search_state.get('has_product') else '❌'}")
        print(f"\n   页面内容 (前500字):")
        print(f"   {search_state.get('content', '')[:500]}")
        
        browser.close()

if __name__ == "__main__":
    main()
