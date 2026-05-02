"""测试批量上架 3 个商品"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
CONFIG_DIR = PROJECT_ROOT / "config"

from publish import (
    XianyuPublisher, 
    generate_listing, 
    generate_product_image, 
    run_pipeline
)

print("=" * 60)
print("  批量上架测试 — 3 个商品")
print("=" * 60)

# But first, since system Chrome needs headless=False,
# let's modify how we call it — 3 products will open 3 Chrome windows
# Better: generate all products first, then publish one by one

publisher = XianyuPublisher()
if not publisher.login_with_cookies():
    print("登录失败")
    sys.exit(1)

# Generate 3 products
products_data = [
    {"theme": "花卉填色画", "style": "花卉", "price": 8},
    {"theme": "复古手机壁纸", "style": "复古", "price": 3},
    {"theme": "可爱手账贴纸", "style": "可爱", "price": 4},
]

for i, prod in enumerate(products_data):
    print(f"\n--- [{i+1}/3] {prod['theme']} ---")
    
    # AI generate
    listing = generate_listing(prod['theme'], prod['style'], prod['price'])
    title = listing.get('title', f"{prod['style']}风格{prod['theme']}")
    desc = listing.get('description', f"精美{prod['style']}设计，电子版下载。")
    price = str(listing.get('price', prod['price']))
    
    # Image
    img_path = str(PROJECT_ROOT / "products" / f"batch_{i+1}_{int(time.time())}.jpg")
    generate_product_image(prod['theme'], prod['style'], img_path)
    
    print(f"  标题: {title}")
    print(f"  价格: ¥{price}")
    
    # Publish
    ok = publisher.publish_product(title, desc, price, img_path)
    if ok:
        print(f"  ✅ 发布成功")
    else:
        print(f"  ❌ 发布失败")
    
    # Wait between batches
    if i < len(products_data) - 1:
        wait = 60
        print(f"\n⏳ 等待 {wait} 秒后下一个...")
        time.sleep(wait)

publisher.close()

print(f"\n{'='*60}")
print("  批量上架测试完成！")
print(f"{'='*60}")
