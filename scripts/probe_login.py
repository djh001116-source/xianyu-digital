"""
Explore the Goofish login flow and publish page in detail.
"""
import json, os, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "/Users/dengjiahao/Documents/xianyu-digital/config"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        # 1. Go to publish page (will show login prompt)
        print("[1] Publish page state...")
        page.goto("https://www.goofish.com/publish", timeout=30000, wait_until="networkidle")
        page.screenshot(path=f"{OUTPUT_DIR}/publish_unauthenticated.png")
        
        # Get all interactive elements
        interactive = page.evaluate("""() => {
            const els = document.querySelectorAll('a, button, [role="button"], input, [class*="login"], [class*="btn"]');
            return Array.from(els).map(e => ({
                tag: e.tagName,
                text: (e.innerText || e.value || '').trim().substring(0, 50),
                href: e.href || '',
                className: (e.className || '').substring(0, 40),
                visible: e.offsetParent !== null
            })).filter(e => e.visible && (e.text || e.href));
        }""")
        print(f"    Interactive elements: {len(interactive)}")
        for el in interactive[:30]:
            print(f"      {el['tag']:6s} | {el['text'][:40]:40s} | class={el['className'][:30]}")

        # 2. Click the login button to see login options
        login_btn = page.query_selector("text=立即登录")
        if login_btn:
            print("\n[2] Clicking '立即登录'...")
            login_btn.click()
            time.sleep(3)
            page.screenshot(path=f"{OUTPUT_DIR}/login_options.png")
            print(f"    URL after click: {page.url}")
            
            # Check what login methods are available
            login_body = page.evaluate("document.body.innerText")
            print(f"    Login page text: {login_body[:1500]}")

        # 3. Check if there's QR code login option (Alibaba ecosystem)
        print("\n[3] Looking for QR code login...")
        has_qr = page.evaluate("""() => {
            const body = document.body.innerText;
            const qr = (body.includes('二维码') || body.includes('扫码') || body.includes('QR')).toString();
            const wechat = body.includes('微信').toString();
            const taobao = body.includes('淘宝').toString();
            const alipay = body.includes('支付宝').toString();
            return {qr, wechat, taobao, alipay};
        }""")
        print(f"    Login methods: {json.dumps(has_qr, ensure_ascii=False)}")

        # 4. Also check: can we login via taobao.com and get cross-domain cookies?
        print("\n[4] Checking Taobao login flow (cross-domain cookies with Goofish)...")
        page.goto("https://login.taobao.com/", timeout=30000, wait_until="networkidle")
        page.screenshot(path=f"{OUTPUT_DIR}/taobao_login.png")
        taobao_text = page.evaluate("document.body.innerText")[:2000]
        print(f"    Taobao login page: {taobao_text[:800]}")

        browser.close()

if __name__ == "__main__":
    main()
