"""
测试上架 1 个商品 — 用 AI 生成文案 + 图片
然后 Playwright 自动发布
"""
import json, os, sys, time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
PRODUCTS_DIR = PROJECT_ROOT / "products"
CONFIG_DIR = PROJECT_ROOT / "config"

# Generate AI listing
from publish import generate_listing, generate_product_image, call_deepseek

print("=" * 60)
print("  测试上架 1 个商品")
print("=" * 60)

# Step 1: AI generate listing
print("\n[1/3] AI 生成商品文案...")
listing = generate_listing("极简日程本", "极简", 6)
print(f"  → 标题: {listing.get('title', '')}")
print(f"  → 描述: {listing.get('description', '')[:60]}...")
print(f"  → 价格: ¥{listing.get('price', 6)}")

# Step 2: Generate image
print("\n[2/3] 生成设计稿...")
ts = int(time.time())
img_path = str(PRODUCTS_DIR / f"test_launch_{ts}.jpg")
generate_product_image("极简日程本", "极简", img_path)
print(f"  → 图片: {img_path}")

# Step 3: Publish it
print("\n[3/3] 发布到闲鱼...")
from publish import XianyuPublisher
publisher = XianyuPublisher()

if not publisher.login_with_cookies():
    print("❌ 登录失败！")
    sys.exit(1)

success = publisher.publish_product(
    title=listing.get('title', '极简日程本'),
    description=listing.get('description', '简约设计日程管理本，电子版可打印。'),
    price=str(listing.get('price', 6)),
    image_path=img_path,
    dry_run=False  # 真的发布！
)

publisher.close()

if success:
    print("\n" + "=" * 60)
    print("  ✅ 商品发布成功！")
    print("  📸 截图保存到 config/publish_result_*.png")
    print("=" * 60)
    
    # Save record
    record = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "title": listing.get('title', ''),
        "price": listing.get('price', 6),
        "image": img_path,
        "result": "published"
    }
    with open(CONFIG_DIR / "test_launch_record.json", "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
else:
    print("\n❌ 发布失败，查看截图分析原因")
