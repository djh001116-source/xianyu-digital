"""检查 dry-run 后表单状态 — 用 JS 而不是 vision API"""
import json, os, time
from pathlib import Path

CONFIG_DIR = Path("/Users/dengjiahao/Documents/xianyu-digital/config")
COOKIE_FILE = CONFIG_DIR / "goofish_cookies.json"

def check_form():
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
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
        
        # Check form state via JS
        form_state = page.evaluate("""() => {
            const result = {};
            
            // 1. Check images/preview
            const imgs = document.querySelectorAll('img');
            result.images_count = imgs.length;
            result.images = Array.from(imgs).map(i => ({
                src: (i.src || '').substring(0, 80),
                naturalWidth: i.naturalWidth,
                naturalHeight: i.naturalHeight,
                visible: i.offsetParent !== null,
            }));
            
            // 2. Check editor content
            const editor = document.querySelector('div[contenteditable="true"]');
            result.editor_found = !!editor;
            result.editor_content = editor ? (editor.innerText || '').substring(0, 200) : '';
            
            // 3. Check price
            const priceInputs = document.querySelectorAll('input[placeholder="0.00"]');
            result.price_inputs_count = priceInputs.length;
            result.price_values = Array.from(priceInputs).map(i => i.value);
            
            // 4. Check radio buttons
            const radios = document.querySelectorAll('input[type="radio"]');
            result.radios = Array.from(radios).map(r => ({
                value: r.value,
                checked: r.checked,
                label: r.closest('label') ? r.closest('label').innerText.trim() : '',
            }));
            
            // 5. Check submit button
            const submitBtn = document.querySelector('button[type="submit"]');
            result.submit_button_found = !!submitBtn;
            result.submit_button_text = submitBtn ? (submitBtn.innerText || '').trim() : '';
            
            // 6. Check for any error messages
            const errorEls = document.querySelectorAll('[class*="error"], [class*="warning"], [class*="alert"]');
            result.error_elements = errorEls.length;
            
            // 7. Check if there's a category/type selector visible
            const categorySelect = document.querySelector('select, [class*="category"], [class*="type-select"]');
            result.category_selector = categorySelect ? (categorySelect.innerText || '').substring(0, 100) : 'not found';
            
            return result;
        }""")
        
        print("=" * 60)
        print("  表单状态检查")
        print("=" * 60)
        print(f"\n📷 图片预览: {form_state['images_count']} 张")
        for img in form_state['images']:
            print(f"   {img['visible'] and '✅' or '❌'} {img['src'][:60]} ({img['naturalWidth']}x{img['naturalHeight']})")
        
        print(f"\n✏️  编辑器: {'✅ 找到' if form_state['editor_found'] else '❌ 未找到'}")
        print(f"   内容: {form_state['editor_content'][:100]}")
        
        print(f"\n💰 价格输入: {form_state['price_inputs_count']} 个")
        for v in form_state['price_values']:
            print(f"   value='{v}'")
        
        print(f"\n🔘 Radio 选项:")
        for r in form_state['radios']:
            check = '✅' if r['checked'] else '  '
            print(f"   {check} value={r['value']} - {r['label']}")
        
        print(f"\n📤 发布按钮: {'✅' if form_state['submit_button_found'] else '❌'} {form_state['submit_button_text']}")
        
        # Take a new screenshot for manual reference
        ts = int(time.time())
        ss_path = str(CONFIG_DIR / f"form_check_{ts}.png")
        page.screenshot(path=ss_path, full_page=True)
        print(f"\n📸 完整截图已保存: {ss_path}")
        
        browser.close()
        return form_state

if __name__ == "__main__":
    state = check_form()
