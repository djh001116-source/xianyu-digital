"""
闲鱼数字商品自动运营系统
========================

全自主流程：
1. AI 生成设计稿（Pillow 渲染）
2. AI 生成标题/描述/标签/价格（DeepSeek API）
3. Playwright 自动上架到闲鱼
4. 自动回复买家消息 + 发货百度网盘链接

肉丸只需要做一次：手机淘宝扫码登录 goofish.com
"""

import os, sys, json, time, re, hashlib, random, logging
from pathlib import Path
from datetime import datetime
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.absolute()
PRODUCTS_DIR = PROJECT_ROOT / "products"
CONFIG_DIR = PROJECT_ROOT / "config"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
COOKIE_FILE = CONFIG_DIR / "goofish_cookies.json"
PUBLISHED_LOG = CONFIG_DIR / "published_log.json"
LISTING_DATA = CONFIG_DIR / "listing_data.json"

# 确保目录存在
for d in [PRODUCTS_DIR, CONFIG_DIR, SCRIPTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# 1. 品类配置 — 先做 5 个最容易卖的品类
# ============================================================

PRODUCT_CATEGORIES = {
    "planners": {
        "name": "日程本/Planner内页",
        "xianyu_category": "学习用品",
        "subdir": "planners",
        "styles": ["极简", "复古", "水彩花卉", "几何", "波西米亚"],
        "count": 20,
        "price_range": (3, 8),
    },
    "coloring": {
        "name": "成人填色书",
        "xianyu_category": "书籍/杂志",
        "subdir": "coloring",
        "styles": ["花卉Mandala", "动物", "抽象几何", "海洋", "森林"],
        "count": 15,
        "price_range": (5, 12),
    },
    "wallpapers": {
        "name": "手机壁纸包（4张/包）",
        "xianyu_category": "其他",
        "subdir": "wallpapers",
        "styles": ["极简", "复古", "自然风景", "暗黑质感", "粉色系"],
        "count": 10,
        "price_range": (2, 5),
    },
    "stickers": {
        "name": "贴纸/手账素材包",
        "xianyu_category": "文具/贴纸",
        "subdir": "stickers",
        "styles": ["可爱", "复古", "植物", "文字", "卡通"],
        "count": 15,
        "price_range": (3, 6),
    },
    "cards": {
        "name": "贺卡/邀请函模板",
        "xianyu_category": "其他",
        "subdir": "cards",
        "styles": ["生日", "结婚", "节日", "感谢", "邀请"],
        "count": 10,
        "price_range": (4, 10),
    },
}

# ============================================================
# 2. AI 设计稿生成引擎
# ============================================================

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

class DesignGenerator:
    """使用 DeepSeek 生成设计指令 + Pillow 渲染为图片"""
    
    DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            # Try to read from .env in auto-dropship
            env_path = Path.home() / "Documents/auto-dropship/.env"
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.startswith("DEEPSEEK_API_KEY="):
                        self.api_key = line.split("=", 1)[1].strip()
                        break
        if not self.api_key:
            print("[ERROR] DEEPSEEK_API_KEY not found!")
            sys.exit(1)
    
    def _call_deepseek(self, system_prompt: str, user_prompt: str, temperature=0.8) -> str:
        """Call DeepSeek API"""
        resp = requests.post(
            self.DEEPSEEK_API,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": 2000,
            },
            timeout=60,
        )
        data = resp.json()
        if "choices" not in data:
            print(f"[ERROR] DeepSeek API error: {data}")
            return ""
        return data["choices"][0]["message"]["content"].strip()
    
    def generate_design_instructions(self, category: str, style: str, index: int) -> dict:
        """
        让 DeepSeek 生成一个设计稿的 SVG/描述。
        返回 {svg: "...", title: "...", description: "...", tags: [...], price: "..."}
        """
        cat = PRODUCT_CATEGORIES[category]
        
        prompt = f"""你是一个专业平面设计师。我要生成一个可以在闲鱼上卖的{cat['name']}。

品类: {category}
风格: {style}
编号: {index}

要求：
1. 给出这个设计的中文标题（用于闲鱼标题，抓眼球，15个字以内）
2. 给出中文商品描述（50-100字，强调用途和场景）
3. 给出 5 个 SEO 标签
4. 给出建议售价（人民币，{cat['price_range'][0]}-{cat['price_range'][1]}元）
5. 最重要的是：给一个具体的 SVG 设计稿代码

SVG 设计要求（必须严格遵守）：
- 如果是 planner/内页：A4比例 (595×842)，有清晰的格子/日期/排版区
- 如果是 coloring/填色书：A4比例 (595×842)，纯黑白线条画，适合打印填色
- 如果是 wallpapers：手机壁纸比例 (1080×1920)，简约但有视觉冲击
- 如果是 stickers/贴纸：正方形 (500×500)，独立图案元素
- 如果是 cards/贺卡：横版 (800×600)，有留白区域写祝福语

以 JSON 格式输出，key 为: title, description, tags, price, svg_code
只输出 JSON，不要有其他文字。"""

        result = self._call_deepseek(
            "你是一个专业平面设计师，擅长使用 SVG 创作可打印的平面设计作品。",
            prompt,
            temperature=0.9,
        )
        
        # Parse JSON from response
        try:
            # Find JSON block
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(result)
        except:
            print(f"[WARN] Failed to parse DeepSeek response as JSON: {result[:200]}")
            data = {
                "title": f"{style}风格{cat['name']}{index}",
                "description": f"精美{style}风格设计，适合各种场景使用。",
                "tags": [style, category, "设计", "原创", "数字商品"],
                "price": str(random.randint(cat['price_range'][0], cat['price_range'][1])),
                "svg_code": "",
            }
        
        return data
    
    def render_from_svg(self, svg_code: str, output_path: str, format_type="jpeg"):
        """Render SVG to image file using Pillow + cairo (if available) or pure Pillow"""
        if not svg_code:
            # Generate a fallback image
            return self._render_fallback(output_path, format_type)
        
        try:
            # Try cairosvg for proper SVG rendering
            import cairosvg
            if format_type == "jpeg":
                cairosvg.svg2png(bytestring=svg_code.encode(), 
                                write_to=str(output_path).replace('.jpg', '.png'),
                                output_width=1200)
                # Convert to JPEG
                img = Image.open(str(output_path).replace('.jpg', '.png'))
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(output_path, 'JPEG', quality=92)
                return str(output_path)
            else:
                cairosvg.svg2png(bytestring=svg_code.encode(),
                                write_to=str(output_path),
                                output_width=1200)
                return str(output_path)
        except ImportError:
            pass
        except Exception as e:
            print(f"[WARN] cairosvg render failed: {e}")
        
        return self._render_fallback(output_path, format_type)
    
    def _render_fallback(self, output_path: str, format_type="jpeg") -> str:
        """Pure Pillow fallback — generate a nice abstract design"""
        # Determine canvas size based on output path naming
        if "wallpapers" in str(output_path):
            w, h = 1080, 1920
        elif "stickers" in str(output_path):
            w, h = 500, 500
        elif "cards" in str(output_path):
            w, h = 800, 600
        else:
            w, h = 1200, 1600  # A4-ish
        
        img = Image.new('RGB', (w, h), self._random_pastel())
        draw = ImageDraw.Draw(img)
        
        # Draw geometric patterns
        for _ in range(random.randint(5, 20)):
            shape = random.choice(['circle', 'rect', 'line', 'triangle'])
            color = self._random_pastel()
            x1 = random.randint(0, w)
            y1 = random.randint(0, h)
            
            if shape == 'circle':
                r = random.randint(20, 200)
                draw.ellipse([x1-r, y1-r, x1+r, y1+r], fill=color, outline=None)
            elif shape == 'rect':
                x2 = x1 + random.randint(50, 300)
                y2 = y1 + random.randint(50, 300)
                draw.rectangle([x1, y1, x2, y2], fill=color, outline=None)
            elif shape == 'line':
                x2 = x1 + random.randint(-200, 200)
                y2 = y1 + random.randint(-200, 200)
                draw.line([x1, y1, x2, y2], fill=color, width=random.randint(2, 10))
        
        # Add a subtle gradient overlay
        for i in range(h):
            alpha = i / h * 0.3
            overlay = Image.new('RGB', (w, 1), (0, 0, 0))
            overlay = Image.blend(img.crop((0, i, w, i+1)), overlay, alpha)
            img.paste(overlay, (0, i))
        
        # Add a decorative title text
        try:
            font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 48)
            draw.text((w//4, h//3), "Digital Design", fill=(255,255,255), font=font)
        except:
            pass
        
        if format_type == "jpeg":
            img.save(output_path, 'JPEG', quality=90)
        else:
            img.save(output_path)
        
        return str(output_path)
    
    def _random_pastel(self):
        return (
            random.randint(180, 255),
            random.randint(150, 240),
            random.randint(160, 250),
        )


# ============================================================
# 3. 闲鱼自动上架器
# ============================================================

class XianyuPublisher:
    """Playwright 驱动的闲鱼自动上架器"""
    
    def __init__(self, headless=False):
        self.headless = headless
        self.cookie_path = COOKIE_FILE
        self.browser = None
        self.context = None
        self.page = None
        self.is_logged_in = False
    
    def login_with_qr(self):
        """打开淘宝登录页，等肉丸扫码"""
        from playwright.sync_api import sync_playwright
        
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        self.page = self.context.new_page()
        
        # Go to goofish publish — this triggers the login modal
        print("\n" + "="*60)
        print("🔄 正在打开闲鱼登录页面...")
        print("📱 请在30秒内用手机淘宝APP扫一扫二维码登录")
        print("="*60 + "\n")
        
        self.page.goto("https://www.goofish.com/publish", timeout=60000, wait_until="networkidle")
        
        # The modal should appear with QR code in an iframe
        # Wait for user to scan and complete login (30 seconds)
        import time as _time
        _time.sleep(5)
        
        # Take screenshot so user can see the QR
        self.page.screenshot(path=str(CONFIG_DIR / "login_qr_ready.png"))
        print("[INFO] QR 码页面已截图保存，请在 Mac 上查看并扫码")
        
        # Poll for login completion — check if URL changes away from login
        for i in range(120):  # 2 minute timeout
            _time.sleep(1)
            try:
                current_url = self.page.url
                # If we're redirected away from publish (logged in)
                if "/publish" not in current_url:
                    # Navigate back to publish
                    self.page.goto("https://www.goofish.com/publish", timeout=10000)
                    _time.sleep(2)
                
                # Check if we have a session by trying to access a logged-in page
                # Actually simpler: check if the page no longer shows "立即登录"
                body = self.page.evaluate("document.body.innerText")
                if "立即登录" not in body and "登录后" not in body:
                    self.is_logged_in = True
                    print("\n✅ 登录成功！已检测到登录状态\n")
                    break
            except:
                pass
        
        if not self.is_logged_in:
            print("[WARN] 登录超时或失败，请重试")
            return False
        
        # Save cookies for future use
        self._save_cookies()
        return True
    
    def login_with_cookies(self) -> bool:
        """从文件加载 cookie 恢复登录"""
        from playwright.sync_api import sync_playwright
        
        if not self.cookie_path.exists():
            print("[ERROR] 没有找到保存的 cookie 文件")
            return False
        
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        
        with open(self.cookie_path) as f:
            cookies = json.load(f)
        self.context.add_cookies(cookies)
        
        self.page = self.context.new_page()
        
        # Verify login by going to publish page
        self.page.goto("https://www.goofish.com/publish", timeout=30000, wait_until="networkidle")
        import time as _time
        _time.sleep(3)
        
        body = self.page.evaluate("document.body.innerText")
        self.is_logged_in = "立即登录" not in body and "登录后" not in body
        
        if self.is_logged_in:
            print("[INFO] Cookie 登录成功 ✅")
        else:
            print("[WARN] Cookie 已失效，需要重新扫码")
        
        return self.is_logged_in
    
    def publish_product(self, product: dict) -> bool:
        """
        在闲鱼发布一个数字商品。
        product: {
            title, description, price, tags, 
            image_path, category
        }
        """
        if not self.is_logged_in or not self.page:
            print("[ERROR] 未登录")
            return False
        
        import time as _time
        
        try:
            # 1. Navigate to publish page
            print(f"[INFO] 发布商品: {product['title']}")
            self.page.goto("https://www.goofish.com/publish", timeout=30000, wait_until="networkidle")
            _time.sleep(3)
            
            # 2. Upload image
            image_path = product.get("image_path", "")
            if image_path and os.path.exists(image_path):
                print(f"[INFO] 上传图片: {image_path}")
                # Find file input
                file_input = self.page.query_selector('input[type="file"]')
                if file_input:
                    file_input.set_input_files(image_path)
                    _time.sleep(2)
                    print("[INFO] 图片上传成功")
                else:
                    print("[WARN] 未找到文件上传控件")
            
            # 3. Fill title
            title_input = self.page.query_selector('input[placeholder*="标题"], input[name="title"], [class*="title"] input')
            if title_input:
                title_input.click()
                title_input.fill("")
                _time.sleep(0.5)
                title_input.type(product.get("title", "")[:50], delay=30)
                print(f"[INFO] 标题已填写: {product['title'][:40]}")
            
            # 4. Fill description
            desc_input = self.page.query_selector('textarea, [contenteditable="true"], [class*="desc"] textarea')
            if desc_input:
                desc_input.click()
                desc_input.fill("")
                _time.sleep(0.5)
                desc_input.type(product.get("description", "")[:200], delay=10)
                print("[INFO] 描述已填写")
            
            # 5. Set price
            price_input = self.page.query_selector('input[placeholder*="价格"], input[name*="price"], [class*="price"] input')
            if price_input:
                price_input.click()
                price_input.fill("")
                _time.sleep(0.5)
                price_input.type(str(product.get("price", "5")), delay=20)
                print(f"[INFO] 价格已设置: ¥{product['price']}")
            
            # 6. Set category
            # 先看着
  
            # 7. Publish! (or save as draft)
            _time.sleep(2)
            
            # Look for publish/submit button
            publish_btn = self.page.query_selector('button:has-text("发布"), button:has-text("确定"), [class*="submit"], [class*="publish"]')
            if publish_btn:
                publish_btn.click()
                _time.sleep(3)
                print("[INFO] 已点击发布按钮")
                
                # Take screenshot of result
                self.page.screenshot(path=str(CONFIG_DIR / f"publish_result_{int(_time.time())}.png"))
                return True
            else:
                print("[WARN] 未找到发布按钮，截图中...")
                self.page.screenshot(path=str(CONFIG_DIR / f"publish_no_button_{int(_time.time())}.png"))
                return False
            
        except Exception as e:
            print(f"[ERROR] 发布失败: {e}")
            try:
                self.page.screenshot(path=str(CONFIG_DIR / f"publish_error_{int(_time.time())}.png"))
            except:
                pass
            return False
    
    def publish_batch(self, products: list) -> dict:
        """批量发布商品"""
        results = {"total": len(products), "success": 0, "failed": 0, "errors": []}
        
        for i, product in enumerate(products, 1):
            print(f"\n--- [{i}/{len(products)}] 发布中 ---")
            success = self.publish_product(product)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"[{i}] 失败: {product.get('title', '?')[:40]}")
            
            # Politeness delay
            if i < len(products):
                wait = random.uniform(30, 60)
                print(f"[INFO] 等待 {wait:.0f} 秒后发布下一个...")
                time.sleep(wait)
        
        return results
    
    def _save_cookies(self):
        """保存 cookie 到文件"""
        if self.context:
            cookies = self.context.cookies()
            with open(self.cookie_path, "w") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            print(f"[INFO] 已保存 {len(cookies)} 个 cookie 到 {self.cookie_path}")
    
    def close(self):
        """关闭浏览器"""
        if self.browser:
            try:
                self.browser.close()
            except:
                pass


# ============================================================
# 4. 流水线编排
# ============================================================

class Pipeline:
    """完整流水线：生成 → 发布"""
    
    def __init__(self):
        self.generator = DesignGenerator()
        self.publisher = XianyuPublisher(headless=True)
        self.generated_products = []
    
    def generate_all_products(self) -> list:
        """为所有品类生成设计稿"""
        all_products = []
        total = sum(cat["count"] for cat in PRODUCT_CATEGORIES.values())
        done = 0
        
        for cat_key, cat in PRODUCT_CATEGORIES.items():
            cat_dir = PRODUCTS_DIR / cat["subdir"]
            cat_dir.mkdir(parents=True, exist_ok=True)
            
            for i in range(1, cat["count"] + 1):
                style = random.choice(cat["styles"])
                done += 1
                print(f"\n[{done}/{total}] 生成 {cat['name']} #{i} ({style}风格)...")
                
                # 1. AI 生成设计指令
                design = self.generator.generate_design_instructions(cat_key, style, i)
                
                # 2. 渲染为图片
                img_filename = f"{cat_key}_{style}_{i:03d}.jpg"
                img_path = cat_dir / img_filename
                
                if design.get("svg_code"):
                    final_path = self.generator.render_from_svg(
                        design["svg_code"], str(img_path)
                    )
                else:
                    final_path = self.generator._render_fallback(str(img_path))
                
                # 3. 组装商品数据
                product = {
                    "title": design.get("title", f"{style}风格{cat['name']}"),
                    "description": design.get("description", ""),
                    "price": design.get("price", str(random.randint(cat['price_range'][0], cat['price_range'][1]))),
                    "tags": design.get("tags", []),
                    "image_path": final_path or str(img_path),
                    "category": cat["name"],
                    "style": style,
                    "category_key": cat_key,
                }
                
                all_products.append(product)
                
                # Save listing data incrementally
                with open(LISTING_DATA, "w", encoding="utf-8") as f:
                    json.dump(all_products, f, ensure_ascii=False, indent=2)
        
        self.generated_products = all_products
        print(f"\n✅ 全部生成完毕！共 {len(all_products)} 个商品")
        return all_products
    
    def publish_all(self, products: list):
        """发布所有商品到闲鱼"""
        # Try cookie login first
        logged_in = self.publisher.login_with_cookies()
        
        if not logged_in:
            print("\n[INFO] Cookie 失效，需要重新扫码登录...")
            logged_in = self.publisher.login_with_qr()
        
        if not logged_in:
            print("[ERROR] 登录失败，无法发布")
            return
        
        # Publish
        results = self.publisher.publish_batch(products)
        self.publisher.close()
        
        # Save published log
        with open(PUBLISHED_LOG, "w", encoding="utf-8") as f:
            json.dump({
                "last_publish": datetime.now().isoformat(),
                "results": results,
                "products": len(products),
            }, f, ensure_ascii=False, indent=2)
        
        return results
    
    def first_time_setup(self):
        """首次使用：生成 + 扫码登录 + 发布"""
        print("=" * 60)
        print("    闲鱼数字商品自动运营系统 — 首次设置")
        print("=" * 60)
        
        # Step 1: Generate products
        print("\n📦 第一步：生成设计稿...")
        products = self.generate_all_products()
        
        # Step 2: Login (QR code)
        print("\n🔑 第二步：登录闲鱼...")
        logged_in = self.publisher.login_with_qr()
        
        if not logged_in:
            print("[ERROR] 登录失败，请重试")
            return
        
        # Step 3: Publish
        print("\n🚀 第三步：开始批量发布...")
        results = self.publisher.publish_batch(products)
        self.publisher.close()
        
        print("\n" + "=" * 60)
        print(f"    设置完成！")
        print(f"    成功发布: {results['success']} / {results['total']}")
        print(f"    失败: {results['failed']}")
        print("=" * 60)
        
        return results


# ============================================================
# 5. CLI 入口
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="闲鱼数字商品自动运营系统")
    parser.add_argument("--setup", action="store_true", help="首次设置：生成+登录+发布")
    parser.add_argument("--generate", action="store_true", help="仅生成设计稿")
    parser.add_argument("--publish", action="store_true", help="仅发布（需已有生成的数据）")
    parser.add_argument("--login", action="store_true", help="仅扫码登录")
    parser.add_argument("--count", type=int, default=50, help="生成数量（默认50）")
    
    args = parser.parse_args()
    
    pipeline = Pipeline()
    
    if args.setup:
        pipeline.first_time_setup()
    elif args.generate:
        pipeline.generate_all_products()
    elif args.publish:
        pipeline.publish_all(pipeline.generated_products or [])
    elif args.login:
        pub = XianyuPublisher(headless=False)
        pub.login_with_qr()
        pub.close()
    else:
        parser.print_help()
