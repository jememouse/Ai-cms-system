# auto_publisher/publisher.py
"""
自动发文主调度器
串联飞书读取 -> AI 生成 -> RPA 发布 -> 状态更新
"""
import time
from typing import List, Dict
from .feishu_client import FeishuClient
from .article_generator import ArticleGenerator
from .wellcms_rpa import WellCMSPublisher


class AutoPublisher:
    """自动发文调度器"""
    
    def __init__(self):
        self.feishu = FeishuClient()
        self.generator = ArticleGenerator()
        self.publisher = WellCMSPublisher()
    
    def run(self) -> List[Dict]:
        """
        执行自动发文流程
        
        Returns:
            处理结果列表
        """
        print("\n" + "=" * 50)
        print("🚀 盒艺家自动发文系统启动")
        print("=" * 50 + "\n")
        
        # 1. 获取待发布记录
        print("📋 正在获取待发布记录...")
        records = self.feishu.fetch_all_pending()
        
        if not records:
            print("⚠️ 没有待发布的记录")
            return []
        
        print(f"\n📝 共获取到 {len(records)} 条待发布记录\n")
        
        results = []
        
        # 2. 逐条处理
        for idx, record in enumerate(records):
            print(f"\n--- [{idx + 1}/{len(records)}] 处理: {record['topic'][:30]}... ---")
            
            result = {
                "record_id": record["record_id"],
                "topic": record["topic"],
                "category": record["category"],
                "status": "pending"
            }
            
            try:
                # 2.1 AI 生成文章
                print("   🤖 正在生成文章...")
                article = self.generator.generate(record["topic"], record["category"])
                
                if not article:
                    result["status"] = "generation_failed"
                    results.append(result)
                    continue
                
                # 2.2 RPA 发布到 WellCMS
                print("   📤 正在发布到 WellCMS...")
                published = self.publisher.publish_sync(article)
                
                if not published:
                    result["status"] = "publish_failed"
                    results.append(result)
                    continue
                
                # 2.3 更新飞书状态
                print("   📊 正在更新飞书状态...")
                updated = self.feishu.update_record_status(record["record_id"], article)
                
                if updated:
                    result["status"] = "success"
                    result["title"] = article.get("title", "")
                else:
                    result["status"] = "update_failed"
                
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")
                result["status"] = "error"
                result["error"] = str(e)
            
            results.append(result)
            
            # 间隔，避免请求过快
            time.sleep(2)
        
        # 3. 打印统计
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: List[Dict]):
        """打印统计摘要"""
        print("\n" + "=" * 50)
        print("📊 发布统计")
        print("=" * 50)
        
        success = sum(1 for r in results if r["status"] == "success")
        failed = len(results) - success
        
        print(f"   ✅ 成功: {success}")
        print(f"   ❌ 失败: {failed}")
        print("=" * 50 + "\n")
        
        if failed > 0:
            print("失败详情:")
            for r in results:
                if r["status"] != "success":
                    print(f"   - [{r['status']}] {r['topic'][:40]}...")


def main():
    """入口函数"""
    publisher = AutoPublisher()
    publisher.run()


if __name__ == "__main__":
    main()
