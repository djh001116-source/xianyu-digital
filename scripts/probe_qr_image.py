"""
Strategy: Login via Taobao (password mode), then check if Goofish inherits the session.
This is much more automation-friendly than QR code.
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

        # Step 1: Navigate to Goofish publish page
        print("[1] Navigating to goofish publish...")
        page.goto("https://www.goofish.com/publish", timeout=30000, wait_until="networkidle")
        time.sleep(1)
        
        # The login modal should be showing. Let's look for the actual QR code image
        # Goofish uses Alibaba SSO - the QR code might be in an iframe
        print("\n[2] Looking for QR code in iframes...")
        frames = page.frames
        print(f"    Found {len(frames)} frames")
        
        for i, frame in enumerate(frames):
            try:
                text = frame.evaluate("document.body?.innerText || ''")[:200]
                url = frame.url[:80]
                print(f"    Frame {i}: {url} | {text}")
            except:
                print(f"    Frame {i}: inaccessible")

        # Step 3: Take a vision screenshot to understand the login modal visually
        # Actually let's check if the login modal contains a QR image
        print("\n[3] Looking for QR image in the page...")
        qr_info = page.evaluate("""() => {
            // Find all images
            const imgs = document.querySelectorAll('img');
            const allImgs = Array.from(imgs).map(i => ({
                src: i.src.substring(0, 100),
                alt: i.alt,
                width: i.naturalWidth,
                height: i.naturalHeight,
                visible: i.offsetParent !== null,
            }));
            
            // Find the login container
            const containers = document.querySelectorAll('[class*="login"], [class*="modal"], .ant-modal');
            const containerHTML = containers.length > 0 ? containers[0].outerHTML.substring(0, 2000) : 'none';
            
            return {allImgs, containerHTML};
        }""")
        
        print(f"    Images found: {len(qr_info.get('allImgs', []))}")
        for img in qr_info.get('allImgs', [])[:10]:
            if img['visible']:
                print(f"      {img['src'][:80]} ({img['width']}x{img['height']})")
        
        print(f"\n    Login container HTML (first 2K): {qr_info.get('containerHTML', '')[:1500]}")

        # Step 4: Alibaba SSO flow — the QR is in an iframe
        # Let's try to navigate directly to the QR login URL
        print("\n[4] Looking for Alibaba QR login directly...")
        # Alibaba QR login page
        page.goto("https://login.taobao.com/member/login.jhtml?qrLogin=true", timeout=30000, wait_until="networkidle")
        time.sleep(3)
        page.screenshot(path=f"{OUTPUT_DIR}/alibaba_qr_login.png")
        
        # Get the QR image URL
        qr_url = page.evaluate("""() => {
            const imgs = document.querySelectorAll('img');
            for (const img of imgs) {
                const src = (img.src || '').toLowerCase();
                if ((src.includes('qr') || src.includes('code')) && img.naturalWidth > 50) {
                    return img.src;
                }
            }
            // Look in iframes
            const frames = document.querySelectorAll('iframe');
            for (const f of frames) {
                try {
                    const doc = f.contentDocument || f.contentWindow.document;
                    if (doc) {
                        const imgs = doc.querySelectorAll('img');
                        for (const img of imgs) {
                            if (((img.src || '').toLowerCase().includes('qr')) && img.naturalWidth > 50) {
                                return img.src;
                            }
                        }
                    }
                } catch(e) {}
            }
            return 'not found';
        }""")
        print(f"    QR image URL: {qr_url}")
        
        tb_text = page.evaluate("document.body.innerText")
        print(f"\n    Login page text: {tb_text[:1500]}")

        browser.close()

if __name__ == "__main__":
    main()
