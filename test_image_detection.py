#!/usr/bin/env python3
"""
测试图片检测机制
"""
import sys
import os
import hashlib
import requests

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def test_image_url(url: str):
    """测试指定 URL 的图片是否为限流图"""
    print(f"\n{'='*80}")
    print(f"测试 URL: {url}")
    print(f"{'='*80}\n")

    # 下载图片
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            print(f"❌ HTTP {resp.status_code}")
            return

        content = resp.content
        content_size = len(content)
        content_hash = hashlib.md5(content).hexdigest()

        print(f"📊 图片信息:")
        print(f"   - 大小: {content_size:,} bytes ({content_size/1024:.2f} KB)")
        print(f"   - MD5:  {content_hash}")
        print(f"   - URL 包含 key: {'✓' if 'key=' in url else '✗'}")

        # 加载黑名单
        import json
        blacklist_file = os.path.join(PROJECT_ROOT, "config", "rate_limit_image_blacklist.json")
        try:
            with open(blacklist_file, 'r') as f:
                data = json.load(f)
                blacklist = set(data.get("blacklist", [])) | set(data.get("auto_learned", []))
        except FileNotFoundError:
            blacklist = {"12aff62f69f5c0a5798c6f2d15dfa3c1", "694684906bafe9aec36a70ca08e8c1a7"}

        # 检测规则
        print(f"\n🔍 检测结果:")

        SUSPICIOUS_SIZE_MIN = 45000
        SUSPICIOUS_SIZE_MAX = 55000

        # 规则 1: 尺寸检测
        if SUSPICIOUS_SIZE_MIN <= content_size <= SUSPICIOUS_SIZE_MAX:
            print(f"   ⚠️  启发式规则: 疑似限流图 (尺寸在 {SUSPICIOUS_SIZE_MIN}-{SUSPICIOUS_SIZE_MAX} 范围内)")
            is_rate_limit = True
        else:
            print(f"   ✓  启发式规则: 通过 (尺寸不在可疑范围)")
            is_rate_limit = False

        # 规则 2: MD5 黑名单
        if content_hash in blacklist:
            print(f"   ⚠️  MD5 黑名单: 命中")
            is_rate_limit = True
        else:
            print(f"   ✓  MD5 黑名单: 未命中")

        # 最终结论
        print(f"\n{'='*80}")
        if is_rate_limit:
            print(f"🚫 结论: 这是一张 **限流图**，应该被拦截")
            print(f"\n建议操作:")
            print(f"   1. 将 MD5 {content_hash} 添加到黑名单")
            print(f"   2. 检查 API key 是否有效")
            print(f"   3. Fallback 到其他图库（Pexels/Pixabay/Unsplash）")
        else:
            print(f"✅ 结论: 这是一张 **正常图片**")
        print(f"{'='*80}\n")

        # 保存图片用于人工检查
        output_file = "/tmp/downloaded_image.jpg"
        with open(output_file, "wb") as f:
            f.write(content)
        print(f"💾 图片已保存到: {output_file}")
        print(f"   请手动打开查看以确认检测结果\n")

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    # 测试用户提供的 URL
    test_url = "https://image.pollinations.ai/prompt/small-business-unboxing-experience-kraft-paper?width=1024&height=768&nologo=true"

    if len(sys.argv) > 1:
        test_url = sys.argv[1]

    test_image_url(test_url)
