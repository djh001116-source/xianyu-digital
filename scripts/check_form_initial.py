"""检查闲鱼发布页面的初始表单结构 — 直接新开页面"""
import json, os, time
from pathlib import Path

CONFIG_DIR = Path("/Users/dengjiahao/Documents/xianyu-digital/config")
COOKIE_FILE = CONFIG_DIR / "goofish_cookies.json"

def main():
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # headful to see
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
        )
        
        with open(COOKIE_FILE) as f:
            context.add_cookies(json.load(f))
        
        page = context.new_page()
        
        # Fresh nav
        page.goto("https://www.goofish.com/publish", timeout=30000, wait_until="networkidle")
        time.sleep(5)
        
        # Print ALL elements in the page
        all_els = page.evaluate("""() => {
            function describe(el) {
                const tag = el.tagName.toLowerCase();
                const type = el.type || '';
                const id = el.id || '';
                const cls = (el.className || '').substring(0, 60);
                const placeholder = el.placeholder || '';
                const contenteditable = el.getAttribute('contenteditable') || '';
                const role = el.getAttribute('role') || '';
                const value = el.value || '';
                const text = (el.innerText || '').trim().substring(0, 50);
                const rect = el.getBoundingClientRect();
                return `${tag}${type ? ' type='+type : ''}${id ? ' id='+id : ''}${cls ? ' class='+cls : ''}${placeholder ? ' ph='+placeholder : ''}${contenteditable ? ' [editable]' : ''}${role ? ' role='+role : ''}${value ? ' val='+value : ''}${text ? ' text="'+text+'"' : ''} xy=${Math.round(rect.x)},${Math.round(rect.y)} ${Math.round(rect.w)}x${Math.round(rect.h)}`;
            }
            
            const results = [];
            
            // All inputs
            document.querySelectorAll('input').forEach(el => results.push(describe(el)));
            
            // All contenteditable
            document.querySelectorAll('[contenteditable="true"]').forEach(el => results.push(describe(el)));
            
            // All buttons
            document.querySelectorAll('button').forEach(el => results.push(describe(el)));
            
            // All textareas
            document.querySelectorAll('textarea').forEach(el => results.push(describe(el)));
            
            // All selects
            document.querySelectorAll('select').forEach(el => results.push(describe(el)));
            
            return results;
        }""")
        
        print(f"=== 页面元素 ({len(all_els)} 个) ===")
        for el in all_els:
            print(f"  {el}")
        
        browser.close()

if __name__ == "__main__":
    main()
