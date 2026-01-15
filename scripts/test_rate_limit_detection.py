#!/usr/bin/env python3
"""
测试脚本：验证速率限制图检测逻辑
"""
import sys
import os
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_rate_limit_detection():
    """测试速率限制图检测"""
    
    # 已知的速率限制图 MD5
    RATE_LIMIT_IMAGE_HASHES = {
        "12aff62f69f5c0a5798c6f2d15dfa3c1",  # 1024x1360 版本
    }
    
    # 测试1: 检测已知速率限制图
    rate_limit_sample = "/tmp/rate_limit_sample.jpg"
    if os.path.exists(rate_limit_sample):
        with open(rate_limit_sample, 'rb') as f:
            content = f.read()
        content_hash = hashlib.md5(content).hexdigest()
        
        is_rate_limit = content_hash in RATE_LIMIT_IMAGE_HASHES
        print(f"[TEST 1] 速率限制图检测: {'✅ PASS' if is_rate_limit else '❌ FAIL'}")
        print(f"         文件: {rate_limit_sample}")
        print(f"         MD5: {content_hash}")
        print(f"         匹配黑名单: {is_rate_limit}")
    else:
        print(f"[TEST 1] ⚠️ SKIP - 速率限制图样本不存在: {rate_limit_sample}")
    
    # 测试2: 正常图片不应被误判
    normal_sample = "/tmp/pollinations_test_有_API_Key.jpg"
    if os.path.exists(normal_sample):
        with open(normal_sample, 'rb') as f:
            content = f.read()
        content_hash = hashlib.md5(content).hexdigest()
        
        is_rate_limit = content_hash in RATE_LIMIT_IMAGE_HASHES
        print(f"\n[TEST 2] 正常图片不误判: {'✅ PASS' if not is_rate_limit else '❌ FAIL'}")
        print(f"         文件: {normal_sample}")
        print(f"         MD5: {content_hash}")
        print(f"         匹配黑名单: {is_rate_limit}")
    else:
        print(f"\n[TEST 2] ⚠️ SKIP - 正常图片样本不存在: {normal_sample}")
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == "__main__":
    test_rate_limit_detection()
