"""
闲鱼发布脚本 v2 — 多品类批量上架，使用已生成的设计稿

依赖: playwright (pip install playwright)
"""
import os, sys, json, time, random, logging, io
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
COOKIE_PATH = PROJECT_ROOT / "config" / "goofish_cookies.json"
PRODUCTS_DIR = PROJECT_ROOT / "products"
DRY_RUN_DIR = PROJECT_ROOT / "dry_run_screenshots"
DRY_RUN_DIR.mkdir(exist_ok=True)

# 新闲鱼发布页路由
PUBLISH_URL = "https://www.goofish.com/publish"


def load_cookies(page):
    """Load saved cookies from file."""
    if not COOKIE_PATH.exists():
        log.warning("No cookies found. You need to login first.")
        return False
    cookies = json.loads(open(COOKIE_PATH).read())
    page.context.add_cookies(cookies)
    return True


def save_cookies(page):
    """Save cookies to file."""
    cookies = page.context.cookies()
    COOKIE_PATH.parent.mkdir(parents=True, exist_ok=True)
    json.dump(cookies, open(COOKIE_PATH, "w"))
    log.info(f"Cookies saved ({len(cookies)} items)")


def discover_products():
    """Scan for all generated products (SVG + PNG)."""
    products = []
    if not PRODUCTS_DIR.exists():
        log.error(f"Products directory not found: {PRODUCTS_DIR}")
        return products
    
    for fname in sorted(PRODUCTS_DIR.iterdir(), reverse=True):
        if fname.suffix.lower() in (".svg", ".png"):
            json_path = fname.with_suffix(".json")
            meta = {}
            if json_path.exists():
                meta = json.load(open(json_path))
            
            products.append({
                "name": fname.stem,
                "path": str(fname),
                "ext": fname.suffix.lower(),
                "meta": meta,
                "title": meta.get("title", fname.stem.replace("_", " ").title()),
                "price": meta.get("price", 9.99),
                "description": meta.get("description", ""),
            })
    return products


def get_or_login(browser):
    """Open browser, try loading cookies, if login failed prompt user."""
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        locale="zh-CN",
    )
    page = context.new_page()
    
    # Try with cookies
    page.goto("https://www.goofish.com/", wait_until="load", timeout=45000)
    page.wait_for_timeout(3000)
    
    if load_cookies(page):
        page.goto(PUBLISH_URL, wait_until="load", timeout=45000)
        page.wait_for_timeout(3000)
        
        # Check if we're still logged in
        if "login" in page.url.lower() or "passport" in page.url.lower():
            log.warning("Cookies expired. Need fresh login.")
        else:
            log.info("Logged in via cookies.")
            return page, context
        
    # Interactive login
    page.goto("https://www.goofish.com/", wait_until="load", timeout=45000)
    log.info("Please scan QR code to login in the browser window...")
    page.wait_for_url(lambda url: "login" not in url and "passport" not in url, timeout=120000)
    save_cookies(page)
    page.goto(PUBLISH_URL, wait_until="load", timeout=45000)
    page.wait_for_timeout(3000)
    return page, context


def create_listing(page, product, image_paths, dry_run=False):
    from pathlib import Path
    """
    Fill in one product listing on the publish page.
    Returns True if successful.
    """
    log.info(f"Creating listing: {product['name']} (¥{product['price']})")
    
    # ── 1. Upload images ──
    if image_paths:
        # Headless-safe: find ALL file inputs (antd may wrap differently headless vs headed)
        page.wait_for_timeout(2000)
        file_inputs = page.locator('input[type="file"]')
        count = file_inputs.count()
        log.info(f"Found {count} file input(s) on page")
        if count > 0:
            # Try the most visible one first, fallback to any
            file_inputs.first.set_input_files(image_paths[:9], timeout=15000)
            page.wait_for_timeout(3000)
            log.info(f"Images uploaded: {[Path(p).name for p in image_paths[:3]]}")
        else:
            log.error("No file input found on page")
            return False
    
    # ── 2. Title + Description (editor) ──
    description = product.get("description", "")
    if not description:
        # Generate from name
        name = product["name"]
        price = product["price"]
        description = f"✨ {name.replace('_', ' ').title()} ✨\n数字商品，购买后即可下载使用。\nPrint at home or use digitally.\n¥{price}  |  Digital Download"
    if description:
        editor = page.locator('div[contenteditable]').first
        if editor.is_visible() or True:  # force
  
            editor.click()
            page.wait_for_timeout(500)
            editor.fill(description)
            page.wait_for_timeout(500)
            log.info(f"Description filled ({len(description)} chars)")
    
    # ── 3. Price ──
    price = product.get("price", 9.99)
    price_input = page.locator('input.ant-input[placeholder*="0.00"]').first
    if price_input.is_visible():
        price_input.click()
        price_input.fill(str(price))
        page.wait_for_timeout(300)
        log.info(f"Price set: ¥{price}")
    
    # ── 4. Shipping (radio 3 = no shipping needed) ──
    radiobuttons = page.locator('input[type="radio"]')
    count = radiobuttons.count()
    if count >= 3:
        radiobuttons.nth(2).click()
        page.wait_for_timeout(300)
        log.info("Shipping set: 无需邮寄")
    else:
        log.warning(f"Only {count} radios found, can't set shipping")
    
    if dry_run:
        screenshot_path = str(DRY_RUN_DIR / f"{product['name']}_dry_run.png")
        page.screenshot(path=screenshot_path, full_page=True)
        log.info(f"Dry-run screenshot: {screenshot_path}")
        return True
    
    # ── 5. Submit ──
    submit_btn = page.locator('button:has-text("发布")')
    # Scroll into view if needed — page becomes longer after filling content
    submit_btn.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    submit_btn.click()
    page.wait_for_timeout(3000)
    log.info("Submitted!")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="闲鱼自动发布")
    parser.add_argument("--dry-run", action="store_true", help="Only generate screenshot, don't submit")
    parser.add_argument("--count", type=int, default=0, help="Number of products to process (0 = all)")
    parser.add_argument("--category", type=str, default="", help="Category/keyword filter")
    args = parser.parse_args()
    
    products = discover_products()
    log.info(f"Found {len(products)} generated products")
    
    if not products:
        log.error("No products found to publish!")
        sys.exit(1)
    
    # Filter by category if specified
    if args.category:
        products = [p for p in products if args.category.lower() in p["name"].lower() or args.category.lower() in p["title"].lower()]
        log.info(f"Filtered to {len(products)} products: {args.category}")
    
    # Limit count
    if args.count > 0:
        products = products[:args.count]
    
    # Deduplicate: keep latest version per category
    # Each product name has a timestamp suffix: category_TIMESTAMP.svg
    seen_cats = {}
    for p in products:
        parts = Path(p["path"]).stem.rsplit("_", 1)
        cat = parts[0]
        ts = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 0
        if cat not in seen_cats or ts > seen_cats[cat].get("ts", 0):
            p["ts"] = ts
            seen_cats[cat] = p
    
    products = list(seen_cats.values())
    log.info(f"After dedup by category: {len(products)} products")
    
    log.info(f"Will process {len(products)} products")
    for p in products:
        log.info(f"  [{p['ext']}] ¥{p['price']} {p['name']}")
    
    # Launch browser
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        page, context = get_or_login(browser)
        
        try:
            for i, product in enumerate(products):
                log.info(f"\n{'='*50}")
                log.info(f"Product {i+1}/{len(products)}: {product['name']}")
                
                # Collect image paths (prefer PNG, fallback to SVG)
                img_paths = []
                base_stem = Path(product["path"]).stem
                for ext in [".png", ".svg"]:
                    fp = PRODUCTS_DIR / f"{base_stem}{ext}"
                    if fp.exists():
                        img_paths.append(str(fp))
                
                if not img_paths:
                    log.warning(f"No image files for {product['name']}, skipping")
                    continue
                
                # Navigate to publish page fresh
                if i > 0:
                    page.goto(PUBLISH_URL, wait_until="load", timeout=45000)
                    page.wait_for_timeout(3000)
                
                success = create_listing(page, product, img_paths, dry_run=args.dry_run)
                
                if success and not args.dry_run:
                    # Anti-fraud delay
                    delay = random.randint(45, 90)
                    log.info(f"Waiting {delay}s before next...")
                    time.sleep(delay)
                    
        except KeyboardInterrupt:
            log.info("Interrupted by user")
        except Exception as e:
            log.error(f"Error: {e}")
            screenshot_path = str(DRY_RUN_DIR / f"error_{datetime.now().strftime('%H%M%S')}.png")
            page.screenshot(path=screenshot_path)
            log.info(f"Error screenshot: {screenshot_path}")
            raise
        
        if args.dry_run:
            log.info(f"\nDry-run complete! Screenshots saved to: {DRY_RUN_DIR}")
        else:
            log.info("\nAll products published!")
        
        browser.close()


if __name__ == "__main__":
    main()
