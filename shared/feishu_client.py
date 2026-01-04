# shared/feishu_client.py
"""
飞书多维表格客户端 (共享)
支持读取不同状态的记录和更新状态
"""
import requests
from typing import List, Dict, Optional
from . import config


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
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8"
        }
    
    def fetch_records_by_status(self, status: str, category: str = None, limit: int = 2) -> List[Dict]:
        """
        获取指定状态的记录
        
        Args:
            status: 状态 (Pending/Ready/Published)
            category: 可选分类筛选
            limit: 最大条数
        """
        if not self.token:
            return []
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{self.table_id}/records/search"
        
        conditions = [{"field_name": "Status", "operator": "is", "value": [status]}]
        if category:
            conditions.append({"field_name": "大项分类", "operator": "is", "value": [category]})
        
        payload = {
            "filter": {"conjunction": "and", "conditions": conditions},
            "page_size": limit
        }
        
        try:
            resp = requests.post(url, headers=self._headers(), json=payload, timeout=30)
            data = resp.json()
            
            if data.get("code") != 0:
                print(f"⚠️ 获取记录失败: {data.get('msg')}")
                return []
            
            items = data.get("data", {}).get("items", [])[:limit]
            results = []
            
            for item in items:
                fields = item.get("fields", {})
                topic_field = fields.get("Topic", [])
                
                if isinstance(topic_field, list) and len(topic_field) > 0:
                    topic = topic_field[0].get("text", "") if isinstance(topic_field[0], dict) else str(topic_field[0])
                else:
                    topic = str(topic_field) if topic_field else ""
                
                # 处理分类字段（可能是字符串或列表）
                category_field = fields.get("大项分类", "行业资讯")
                if isinstance(category_field, list) and len(category_field) > 0:
                    category = category_field[0] if isinstance(category_field[0], str) else str(category_field[0])
                else:
                    category = str(category_field) if category_field else "行业资讯"
                
                results.append({
                    "record_id": item.get("record_id"),
                    "topic": topic,
                    "category": category,
                    "title": fields.get("Title", ""),
                    "html_content": fields.get("HTML_Content", ""),
                    "summary": fields.get("摘要", ""),
                    "keywords": fields.get("关键词", ""),
                    "description": fields.get("描述", ""),
                    "tags": fields.get("Tags", ""),
                })
            
            total = data.get("data", {}).get("total", 0)
            filter_desc = f"{category or '全部'}"
            print(f"   📋 [{filter_desc}] 获取 {len(results)} 条 {status} 记录 (共 {total} 条)")
            return results
            
        except Exception as e:
            print(f"⚠️ 获取记录网络错误: {e}")
            return []
    
    def update_record(self, record_id: str, fields: Dict) -> bool:
        """更新记录字段"""
        if not self.token:
            return False
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{self.table_id}/records/{record_id}"
        
        try:
            resp = requests.put(url, headers=self._headers(), json={"fields": fields}, timeout=30)
            data = resp.json()
            
            if data.get("code") == 0:
                return True
            else:
                print(f"   ❌ 更新失败: {data.get('msg')}")
                return False
        except Exception as e:
            print(f"   ⚠️ 更新网络错误: {e}")
            return False
    
    def batch_create_records(self, records: List[Dict]) -> bool:
        """批量创建记录"""
        if not self.token or not records:
            return False
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{self.table_id}/records/batch_create"
        
        payload_records = [{"fields": r} for r in records]
        
        try:
            resp = requests.post(url, headers=self._headers(), json={"records": payload_records[:50]}, timeout=30)
            if resp.json().get("code") == 0:
                print(f"   ✅ 成功上传 {len(payload_records[:50])} 条记录")
                return True
            else:
                print(f"   ❌ 上传失败: {resp.text}")
                return False
        except Exception as e:
            print(f"   ⚠️ 上传网络错误: {e}")
            return False
