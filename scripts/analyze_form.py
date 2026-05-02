"""
只截图发布页面，分析"无需邮寄"等表单元素的具体选择器位置
不会发布任何商品
"""
import json, os, time
from pathlib import Path

CONFIG_DIR = Path("/Users/dengjiahao/Documents/xianyu-digital/config")
COOKIE_FILE = CONFIG_DIR / "goofish_cookies.json"

def main():
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # headful to see what's happening
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
        )
        
        with open(COOKIE_FILE) as f:
            context.add_cookies(json.load(f))
        
        page = context.new_page()
        page.goto("https://www.goofish.com/publish", timeout=30000, wait_until="networkidle")
        time.sleep(4)
        
        # Full page screenshot
        page.screenshot(path=str(CONFIG_DIR / "publish_full.png"), full_page=True)
        
        # Get detailed info about shipping options
        shipping_info = page.evaluate("""() => {
            // Find all radio buttons
            const radios = document.querySelectorAll('input[type="radio"]');
            const result = [];
            
            for (const radio of radios) {
                // Walk up to find label/container
                let container = radio;
                for (let i = 0; i < 5; i++) {
                    if (container.parentElement) container = container.parentElement;
                }
                const containerText = container ? container.innerText.trim().substring(0, 100) : '';
                
                // Get the radio's label/nextSibling text
                const label = radio.closest('label');
                const labelText = label ? label.innerText.trim() : '';
                
                // Also check the generic container
                const grandParent = radio.parentElement?.parentElement;
                const gpText = grandParent ? grandParent.innerText.trim().substring(0, 150) : '';
                
                result.push({
                    checked: radio.checked,
                    value: radio.value,
                    name: radio.name,
                    labelText: labelText,
                    containerText: containerText,
                    grandParentText: gpText,
                });
            }
            
            return result;
        }""")
        
        print("=== 所有 Radio 按钮分析 ===")
        for i, r in enumerate(shipping_info):
            print(f"\nRadio #{i}:")
            for k, v in r.items():
                if v:
                    print(f"  {k}: {v}")
        
        # Also get all form fields in detail
        print("\n\n=== 所有 Input/Button 详细分析 ===")
        all_inputs = page.evaluate("""() => {
            const els = document.querySelectorAll('input, textarea, button, [contenteditable="true"], [role="button"], [class*="publish"]');
            return Array.from(els).map(el => ({
                tag: el.tagName,
                type: el.type || '',
                name: el.name || '',
                id: el.id || '',
                className: (el.className || '').substring(0, 50),
                placeholder: el.placeholder || '',
                value: el.value || '',
                text: (el.innerText || '').trim().substring(0, 40),
                ariaLabel: el.getAttribute('aria-label') || '',
                dataAttr: Object.keys(el.dataset).join(',') || '',
                rect: el.getBoundingClientRect ? JSON.stringify({
                    x: Math.round(el.getBoundingClientRect().x),
                    y: Math.round(el.getBoundingClientRect().y),
                    w: Math.round(el.getBoundingClientRect().width),
                    h: Math.round(el.getBoundingClientRect().height)
                }) : '',
            }));
        }""")
        
        for el in all_inputs:
            info = f"  <{el['tag']}"
            if el['type']: info += f" type={el['type']}"
            if el['name']: info += f" name={el['name']}"
            if el['placeholder']: info += f" placeholder={el['placeholder']}"
            if el['text']: info += f" text='{el['text']}'"
            if el['ariaLabel']: info += f" aria='{el['ariaLabel']}'"
            if el['value']: info += f" value={el['value']}"
            if el['rect']: info += f" {el['rect']}"
            print(info)
        
        browser.close()

if __name__ == "__main__":
    main()
