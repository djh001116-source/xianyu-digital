"""
Directly navigate to the goofish login page and see the QR code login option.
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

        # Go to goofish publish (which shows login modal)
        page.goto("https://www.goofish.com/publish", timeout=30000, wait_until="networkidle")
        
        # Wait a moment for the modal to appear
        time.sleep(2)
        
        # Take a full-page screenshot to see the login modal
        page.screenshot(path=f"{OUTPUT_DIR}/login_modal.png", full_page=True)
        
        # Try to find the QR code tab/button in the modal
        # Look for elements inside the modal
        modal_elements = page.evaluate("""() => {
            // Look for the login modal container
            const modal = document.querySelector('.login-modal, [class*="modal"], [class*="login"], .ant-modal');
            if (!modal) return 'No modal found';
            
            // Get all text in the modal
            const texts = Array.from(modal.querySelectorAll('*'))
                .filter(el => el.childElementCount === 0 && el.textContent.trim())
                .map(el => el.textContent.trim())
                .filter(t => t.length > 0);
            
            // Get all clickable elements
            const clickable = Array.from(modal.querySelectorAll('button, a, [role="button"], [class*="tab"], [class*="qr"], [class*="scan"]'))
                .map(el => ({
                    tag: el.tagName,
                    text: (el.innerText || '').trim().substring(0, 50),
                    class: (el.className || '').substring(0, 30),
                }));
            
            return {texts, clickable};
        }""")
        
        print("=== Login Modal Analysis ===")
        print(json.dumps(modal_elements, ensure_ascii=False, indent=2))

        # Also try to find QR code iframe or image
        qr_imgs = page.evaluate("""() => {
            const imgs = document.querySelectorAll('img[src*="qr"], img[src*="QR"], img[src*="code"]');
            return Array.from(imgs).map(i => i.src);
        }""")
        print(f"\nQR images found: {qr_imgs}")
        
        # Let me try: go to alibaba login page directly (this is what backs goofish)
        # Alibaba OAuth login supports QR code on desktop
        print("\n\n=== Trying Alibaba login page ===")
        page.goto("https://login.taobao.com/member/login.jhtml", timeout=30000, wait_until="networkidle")
        time.sleep(2)
        page.screenshot(path=f"{OUTPUT_DIR}/taobao_login_page.png")
        tb_text = page.evaluate("document.body.innerText")
        print(f"Taobao login text: {tb_text[:1000]}")
        
        # Check for QR login on Alibaba
        alibaba_qr = page.evaluate("""() => {
            const body = document.body.innerText;
            const hasQR = body.includes('扫码') || body.includes('二维码');
            const hasPassword = body.includes('密码登录');
            const hasSMS = body.includes('验证码');
            
            // Find QR code image
            const imgs = document.querySelectorAll('img');
            const qrImgs = Array.from(imgs).filter(i => {
                const src = (i.src || '').toLowerCase();
                return src.includes('qr') || src.includes('code');
            }).map(i => i.src);
            
            return {hasQR, hasPassword, hasSMS, qrImages: qrImgs};
        }""")
        print(f"Alibaba login methods: {json.dumps(alibaba_qr, ensure_ascii=False)}")

        browser.close()

if __name__ == "__main__":
    main()
