"""Dry-run 测试：打开闲鱼发布页，填写一个商品，截图验证，但不发布"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
PRODUCTS_DIR = PROJECT_ROOT / "products"
CONFIG_DIR = PROJECT_ROOT / "config"

# Generate a test image first
from PIL import Image, ImageDraw
w, h = 600, 800
img = Image.new('RGB', (w, h), (255, 255, 255))
draw = ImageDraw.Draw(img)
for i in range(12):
    x1 = 100 + i * 30
    y1 = 100 + i * 20
    draw.ellipse([x1, y1, x1+80, y1+80], fill=(200, 220, 255), outline=None)
draw.rectangle([20, 20, w-20, h-20], outline=(100, 150, 200), width=3)
test_img = str(PRODUCTS_DIR / f"dry_run_test_{int(__import__('time').time())}.jpg")
img.save(test_img, 'JPEG', quality=85)
print(f"Test image: {test_img}")

# Import publisher
from publish import XianyuPublisher, CONFIG_DIR as cfg_dir

publisher = XianyuPublisher()

if publisher.login_with_cookies():
    print("\n--- Running dry-run... ---")
    result = publisher.publish_product(
        title="🌸 极简花卉填色画 减压电子版",
        description="精美花卉设计填色画，电子版PDF下载。适合成人减压、艺术创作。购买后发网盘链接自取。",
        price="8",
        image_path=test_img,
        dry_run=True
    )
    if result:
        print("\n✅ Dry-run 成功！截图已保存，可检查表单是否填写正确。")
        print("如果截图内容正确，就可以正式发布了。")
    else:
        print("\n❌ Dry-run 失败，需要调试。")
    
    publisher.close()
else:
    print("❌ 登录失败，cookie 可能已过期")
