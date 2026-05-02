"""
Probe the Xianyu (闲鱼) web page structure to understand how to automate.
First, let's see if there's a web version we can use.
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

        # 1. Go to xianyu main site
        print("[1] Probing 闲鱼 web...")
        page.goto("https://2.taobao.com/", timeout=30000, wait_until="networkidle")
        page.screenshot(path=f"{OUTPUT_DIR}/xianyu_home.png")
        title = page.title()
        url = page.url
        print(f"    Title: {title}")
        print(f"    URL:   {url}")

        # Check what's on the page
        body = page.evaluate("document.body.innerText")
        print(f"    Body preview: {body[:800]}")

        # 2. Check if we can go to the sell/publish page
        print("\n[2] Trying to access publish page...")
        page.goto("https://2.taobao.com/publish.htm", timeout=30000, wait_until="networkidle")
        page.screenshot(path=f"{OUTPUT_DIR}/xianyu_publish.png")
        print(f"    URL: {page.url}")
        print(f"    Body: {page.evaluate('document.body.innerText')[:500]}")

        # 3. Try going through Alibaba login
        print("\n[3] Trying to detect login state...")
        # Check if there's a user avatar or login button
        has_login = page.evaluate("""() => {
            const body = document.body.innerText;
            return {
                hasSignIn: body.includes('登录') || body.includes('sign') || body.includes('login'),
                buttons: Array.from(document.querySelectorAll('a, button')).map(e => e.innerText.trim()).filter(t => t.length > 0 && t.length < 30).slice(0,20)
            }
        }""")
        print(f"    Login state: {json.dumps(has_login, ensure_ascii=False, indent=2)}")

        # 4. Try Goofish (闲鱼国际版 or alibaba seller center)
        for url_path in [
            "https://www.goofish.com/",
            "https://www.goofish.com/publish",
            "https://www.taobao.com/",
        ]:
            print(f"\n[4] Trying {url_path}...")
            page.goto(url_path, timeout=30000, wait_until="networkidle")
            page.screenshot(path=f"{OUTPUT_DIR}/probe_{url_path.replace('https://','').replace('/','_')}.png")
            print(f"    URL: {page.url}")
            print(f"    Body preview: {page.evaluate('document.body.innerText')[:400]}")

        browser.close()

if __name__ == "__main__":
    main()
