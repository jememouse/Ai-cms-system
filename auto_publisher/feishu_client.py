# auto_publisher/feishu_client.py
"""
飞书多维表格客户端
支持读取待发布记录和更新状态
"""
import requests
from typing import List, Dict, Optional
from .config import config


class FeishuClient:
    """飞书多维表格客户端"""
    
    def __init__(self):
        self.app_id = config.FEISHU_APP_ID
        self.app_secret = config.FEISHU_APP_SECRET
        self.base_id = config.FEISHU_BASE_ID
        self.table_id = config.FEISHU_TABLE_ID
        self.token = self._get_tenant_access_token()
    
    def _get_tenant_access_token(self) -> Optional[str]:
        """获取租户访问令牌"""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        try:
            resp = requests.post(url, json={
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }, timeout=30)
            data = resp.json()
            if data.get("code") == 0:
                print("✅ 飞书鉴权成功")
                return data.get("tenant_access_token")
            else:
                print(f"❌ 飞书鉴权失败: {data}")
                return None
        except Exception as e:
            print(f"❌ 飞书鉴权网络错误: {e}")
            return None
    
    def _headers(self) -> Dict:
        """请求头"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8"
        }
    
    def fetch_pending_records(self, category: str, limit: int = 2) -> List[Dict]:
        """
        获取待发布的记录
        
        Args:
            category: 分类名称 (专业知识/行业资讯/产品介绍)
            limit: 每个分类最多获取几条
            
        Returns:
            记录列表，每条包含 record_id, topic, category
        """
        if not self.token:
            return []
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{self.table_id}/records/search"
        
        payload = {
            "filter": {
                "conjunction": "and",
                "conditions": [
                    {"field_name": "Status", "operator": "is", "value": ["Pending"]},
                    {"field_name": "大项分类", "operator": "is", "value": [category]}
                ]
            },
            "page_size": limit
        }
        
        try:
            resp = requests.post(url, headers=self._headers(), json=payload, timeout=30)
            data = resp.json()
            
            if data.get("code") != 0:
                print(f"⚠️ 获取 {category} 记录失败: {data.get('msg')}")
                return []
            
            items = data.get("data", {}).get("items", [])
            results = []
            
            for item in items:
                fields = item.get("fields", {})
                topic_field = fields.get("Topic", [])
                
                # Topic 可能是文本数组
                if isinstance(topic_field, list) and len(topic_field) > 0:
                    topic = topic_field[0].get("text", "") if isinstance(topic_field[0], dict) else str(topic_field[0])
                else:
                    topic = str(topic_field)
                
                results.append({
                    "record_id": item.get("record_id"),
                    "topic": topic,
                    "category": category
                })
            
            print(f"   📋 {category}: 获取到 {len(results)} 条待发布记录")
            return results
            
        except Exception as e:
            print(f"⚠️ 获取记录网络错误: {e}")
            return []
    
    def fetch_all_pending(self) -> List[Dict]:
        """获取所有分类的待发布记录"""
        all_records = []
        for category in config.CATEGORY_MAP.keys():
            records = self.fetch_pending_records(category, config.MAX_ARTICLES_PER_CATEGORY)
            all_records.extend(records)
        return all_records
    
    def update_record_status(self, record_id: str, article_data: Dict) -> bool:
        """
        更新记录状态为 Published，并回填生成的内容
        
        Args:
            record_id: 飞书记录 ID
            article_data: 包含 title, html_content, summary, keywords, description, tags
        """
        if not self.token:
            return False
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{self.table_id}/records/{record_id}"
        
        payload = {
            "fields": {
                "Status": "Published",
                "Title": article_data.get("title", ""),
                "HTML_Content": article_data.get("html_content", ""),
                "摘要": article_data.get("summary", ""),
                "关键词": article_data.get("keywords", ""),
                "描述": article_data.get("description", ""),
                "Tags": article_data.get("tags", "")
            }
        }
        
        try:
            resp = requests.put(url, headers=self._headers(), json=payload, timeout=30)
            data = resp.json()
            
            if data.get("code") == 0:
                print(f"   ✅ 已更新飞书状态: {record_id}")
                return True
            else:
                print(f"   ❌ 更新失败: {data.get('msg')}")
                return False
                
        except Exception as e:
            print(f"   ⚠️ 更新网络错误: {e}")
            return False
