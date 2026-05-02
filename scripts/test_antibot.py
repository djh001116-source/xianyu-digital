"""测试不同的反检测策略 — 逐个尝试直到成功"""
import json, os, time, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))
CONFIG_DIR = PROJECT_ROOT / "config"
COOKIE_FILE = CONFIG_DIR / "goofish_cookies.json"

def test_browser_config(name, launch_args, ctx_args=None):
    """测试一个浏览器配置"""
    print(f"\n\n{'='*60}")
    print(f"  测试: {name}")
    print('='*60)
    
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_args)
        
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            **(ctx_args or {}),
        )
        
        if COOKIE_FILE.exists():
            with open(COOKIE_FILE) as f:
                ctx.add_cookies(json.load(f))
        
        page = ctx.new_page()
        
        try:
            page.goto("https://www.goofish.com/", timeout=30000, wait_until="domcontentloaded")
            time.sleep(3)
        except:
            print("  ❌ 页面加载超时")
            browser.close()
            return False
        
        # Wait for page to render
        time.sleep(2)
        
        body = page.evaluate("document.body.innerText") or ""
        
        # Check for anti-bot detection
        if "非法访问" in body or "请使用正常浏览器" in body:
            print(f"  ❌ 被拦截：反爬检测")
            result = False
        elif "登录" in body[:500]:
            print(f"  ✅ 加载成功（需要登录）")
            result = True
        else:
            print(f"  ✅ 加载成功（已登录）")
            result = True
        
        # Screenshot
        page.screenshot(path=str(CONFIG_DIR / f"debug_config_{name.replace(' ','_')}.png"))
        
        browser.close()
        return result

# Test 1: headless=False (visible browser) — this worked before
test_browser_config("headless=False", {
    "headless": False,
    "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox"],
})

# Test 2: headless=True with extra stealth args
test_browser_config("headless=True+stealth", {
    "headless": True,
    "args": [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-setuid-sandbox",
    ],
})

# Test 3: Use a more standard user agent with headless=True
test_browser_config("headless=True+standard_ua", {
    "headless": True,
    "args": ["--no-sandbox"],
})

# Test 4: Channel=chrome (use installed Chrome)
print("\n\n检查系统Chrome...")
import subprocess
try:
    result = subprocess.run(["mdfind", "kMDItemKind == 'Application' && kMDItemFSName == 'Google Chrome.app'"], capture_output=True, text=True, timeout=5)
    print(f"  Chrome 路径: {result.stdout.strip()}")
except:
    print("  未找到系统 Chrome")

print("\n\n=== 测试完毕 ===")
print("注：所有测试可在 headless=False 时看到浏览器窗口")
print("建议：当前 cookie 有效，headless=False 时应可直接访问")
