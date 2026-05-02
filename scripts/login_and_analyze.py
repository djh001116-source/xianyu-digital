"""
闲鱼扫码登录脚本 — 只需肉丸用手机淘宝扫一次码

流程：
1. 打开闲鱼发布页面
2. 显示登录弹窗（含二维码）
3. 肉丸手机淘宝扫码
4. cookie 自动保存
5. 截图发布页面结构供后续分析
"""

import json, os, time, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
CONFIG_DIR = PROJECT_ROOT / "config"
COOKIE_FILE = CONFIG_DIR / "goofish_cookies.json"

def main():
    from playwright.sync_api import sync_playwright
    
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        # 1. Go to publish page — will trigger login modal
        print("\n" + "=" * 60)
        print("  正在打开闲鱼发布页面...")
        print("=" * 60)
        page.goto("https://www.goofish.com/publish", timeout=30000, wait_until="networkidle")
        time.sleep(3)

        # 2. Check current state — is there a login modal?
        body_text = page.evaluate("document.body.innerText")
        print(f"\n页面状态: {'需登录' if '登录后' in body_text or '立即登录' in body_text else '已登录'}")
        
        # 3. Take screenshot
        screenshot_path = str(CONFIG_DIR / "01_login_modal.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n截图已保存: {screenshot_path}")
        
        # 4. Check iframes for login form
        frames = page.frames
        print(f"\n页面含有 {len(frames)} 个 iframe:")
        for i, frame in enumerate(frames):
            try:
                url = frame.url[:100]
                text = frame.evaluate("document.body?.innerText || ''")[:200]
                print(f"  [{i}] {url}")
                if text.strip():
                    print(f"      内容: {text[:150]}")
            except:
                print(f"  [{i}] (inaccessible)")

        # 5. If login modal exists, find and click login button
        if "立即登录" in body_text:
            print("\n📱 检测到登录弹窗，正在寻找按钮...")
            
            # Look for the login button inside the modal
            login_btn = page.query_selector("text=立即登录")
            if login_btn:
                print("  找到「立即登录」按钮，尝试点击...")
                try:
                    login_btn.click(timeout=5000)
                    time.sleep(3)
                    page.screenshot(path=str(CONFIG_DIR / "02_after_login_click.png"))
                    print("  已点击登录按钮")
                except:
                    print("  点击失败，可能被模态框遮挡")
            
            # Check if the passport iframe appeared
            time.sleep(2)
            frames = page.frames
            for i, frame in enumerate(frames):
                try:
                    url = frame.url[:120]
                    if "passport" in url or "login" in url or "alibaba" in url:
                        text = frame.evaluate("document.body?.innerText || ''")[:500]
                        print(f"\n🔐 找到登录框 iframe [{i}]:")
                        print(f"  URL: {url}")
                        print(f"  内容: {text[:400]}")
                        
                        # Take screenshot of this frame
                        try:
                            frame.screenshot(path=str(CONFIG_DIR / f"03_login_iframe_{i}.png"))
                        except:
                            pass
                except:
                    pass
            
            print("\n" + "=" * 60)
            print("  📱 请用手机淘宝APP扫一扫功能扫码登录")
            print("  （扫码位置可能在弹窗中或淘宝登录页面）")
            print("=" * 60)
            print()
            
            # 6. Wait for user to scan QR code (up to 2 minutes)
            print("⏳ 等待扫码登录（最长120秒）...")
            logged_in = False
            for sec in range(120):
                time.sleep(1)
                try:
                    current_url = page.url
                    body = page.evaluate("document.body.innerText")
                    
                    # Check if we went past the login
                    if "立即登录" not in body and "登录后" not in body and ("发布" in body or "title" in body.lower()):
                        logged_in = True
                        print(f"\n✅ 登录成功！用时 {sec+1} 秒")
                        break
                    
                    # Also check if URL changed significantly
                    if "/publish" in current_url:
                        # Try to check if we can see publish form elements
                        has_form = page.evaluate("""() => {
                            const inputs = document.querySelectorAll('input');
                            return inputs.length > 3;
                        }""")
                        if has_form:
                            logged_in = True
                            print(f"\n✅ 登录成功！检测到表单元素 ({sec+1}秒)")
                            break
                    
                    if sec % 10 == 0 and sec > 0:
                        print(f"  ⏳ 已等待 {sec} 秒，请扫码...")
                except:
                    pass
            
            if not logged_in:
                print("\n❌ 登录超时（120秒），未检测到登录状态")
                print("可能原因：")
                print("  1. 没有扫码")
                print("  2. 二维码已过期，需要重新运行")
                print("  3. 闲鱼风控拦截了登录")
                
                # Save final state
                page.screenshot(path=str(CONFIG_DIR / "04_login_timeout.png"))
                browser.close()
                return False
        
        # 7. Save cookies
        cookies = context.cookies()
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"\n💾 已保存 {len(cookies)} 个 cookie 到 {COOKIE_FILE}")
        
        # 8. Analyze the publish page structure
        print("\n" + "=" * 60)
        print("  分析发布页面结构...")
        print("=" * 60)
        
        time.sleep(2)
        page.screenshot(path=str(CONFIG_DIR / "05_publish_page.png"), full_page=True)
        
        # Get all interactive elements
        elements = page.evaluate("""() => {
            const all = document.querySelectorAll('input, textarea, select, button, [contenteditable="true"], [role="button"], [class*="upload"], [class*="submit"], [type="file"]');
            return Array.from(all).map(el => ({
                tag: el.tagName,
                type: el.type || '',
                name: el.name || '',
                placeholder: el.placeholder || '',
                className: (el.className || '').substring(0, 60),
                id: el.id || '',
                text: (el.innerText || '').trim().substring(0, 40),
                visible: el.offsetParent !== null,
                rect: el.getBoundingClientRect ? JSON.stringify({
                    x: Math.round(el.getBoundingClientRect().x),
                    y: Math.round(el.getBoundingClientRect().y),
                    w: Math.round(el.getBoundingClientRect().width),
                    h: Math.round(el.getBoundingClientRect().height)
                }) : ''
            })).filter(e => e.visible);
        }""")
        
        print(f"\n找到 {len(elements)} 个可见交互元素:\n")
        for el in elements:
            info = f"  <{el['tag']}"
            if el['type']: info += f" type={el['type']}"
            if el['name']: info += f" name={el['name']}"
            if el['placeholder']: info += f" placeholder=\"{el['placeholder']}\""
            if el['text']: info += f" text=\"{el['text']}\""
            if el['id']: info += f" id={el['id']}"
            info += f" class={el['className'][:40]}"
            info += f" pos={el['rect']}"
            print(info)
        
        # Save full page HTML for detailed analysis
        html = page.content()
        with open(CONFIG_DIR / "publish_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"\n📄 页面 HTML 已保存 ({len(html)} 字符)")
        
        # Get all text on page (to understand categories and fields)
        all_text = page.evaluate("document.body.innerText")
        print(f"\n📝 页面文字内容 ({len(all_text)} 字符):")
        print(all_text[:2000])
        
        browser.close()
        
        print("\n" + "=" * 60)
        print("  ✅ 第一步完成！")
        print("  接下来我分析发布页面结构，形成上架方案")
        print("=" * 60)
        
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
