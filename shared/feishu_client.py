# shared/feishu_client.py
"""
飞书多维表格客户端 (共享)
支持读取不同状态的记录和更新状态
"""
import requests
import time
from typing import List, Dict, Optional
from . import config


class FeishuClient:
    """飞书多维表格客户端"""
    
    # Token 有效期 2 小时，提前 5 分钟刷新
    TOKEN_REFRESH_INTERVAL = 2 * 60 * 60 - 5 * 60  # 1小时55分钟
    
    def __init__(self):
        self.app_id = config.FEISHU_APP_ID
        self.app_secret = config.FEISHU_APP_SECRET
        self.base_id = config.FEISHU_BASE_ID
        self.table_id = config.FEISHU_TABLE_ID
        self.token = None
        self.token_acquired_at = 0
        self._refresh_token()
    
    def _refresh_token(self) -> bool:
        """刷新 Token"""
        token = self._get_tenant_access_token()
        if token:
            self.token = token
            self.token_acquired_at = time.time()
            return True
        return False
    
    def _ensure_valid_token(self) -> bool:
        """确保 Token 有效，必要时自动刷新"""
        elapsed = time.time() - self.token_acquired_at
        if not self.token or elapsed >= self.TOKEN_REFRESH_INTERVAL:
            print("🔄 Token 即将过期，正在刷新...")
            return self._refresh_token()
        return True
    
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
        if not self._ensure_valid_token():
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
                
                # 辅助函数：处理飞书富文本字段
                def parse_text_field(field_value):
                    if not field_value:
                        return ""
                    if isinstance(field_value, str):
                        return field_value
                    if isinstance(field_value, list) and len(field_value) > 0:
                        first = field_value[0]
                        if isinstance(first, dict):
                            return first.get("text", "")
                        return str(first)
                    return str(field_value)
                
                results.append({
                    "record_id": item.get("record_id"),
                    "topic": topic,
                    "category": category,
                    "title": parse_text_field(fields.get("Title", "")),
                    "html_content": parse_text_field(fields.get("HTML_Content", "")),
                    "summary": parse_text_field(fields.get("摘要", "")),
                    "keywords": parse_text_field(fields.get("关键词", "")),
                    "description": parse_text_field(fields.get("描述", "")),
                    "tags": parse_text_field(fields.get("Tags", "")),
                    # 新增字段 (GEO 优化) - 文本类型，存储 JSON 字符串
                    "schema_faq": parse_text_field(fields.get("Schema_FAQ", "")),
                    "one_line_summary": parse_text_field(fields.get("One_Line_Summary", "")),
                    "key_points": parse_text_field(fields.get("Key_Points", "")),
                    "url": parse_text_field(fields.get("URL", "")),
                    "published_at": parse_text_field(fields.get("发布时间", "")),
                    "xhs_status": parse_text_field(fields.get("XHS_Status", "")), # 新增状态字段
                })
            
            total = data.get("data", {}).get("total", 0)
            filter_desc = f"{category or '全部'}"
            print(f"   📋 [{filter_desc}] 获取 {len(results)} 条 {status} 记录 (共 {total} 条)")
            return results
            
        except Exception as e:
            print(f"⚠️ 获取记录网络错误: {e}")
            return []
    
    def update_record(self, record_id: str, fields: Dict, retry: bool = True) -> bool:
        """
        更新记录字段
        
        Args:
            record_id: 记录 ID
            fields: 要更新的字段
            retry: 是否在 Token 失效时重试
        """
        if not self._ensure_valid_token():
            return False
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{self.table_id}/records/{record_id}"
        
        try:
            resp = requests.put(url, headers=self._headers(), json={"fields": fields}, timeout=30)
            data = resp.json()
            
            if data.get("code") == 0:
                return True
            
            # Token 失效时尝试刷新后重试一次
            error_msg = data.get('msg', '')
            if retry and 'token' in error_msg.lower():
                print("   🔄 Token 失效，尝试刷新后重试...")
                if self._refresh_token():
                    return self.update_record(record_id, fields, retry=False)
            
            print(f"   ❌ 更新失败: {error_msg}")
            if "TextFieldConvFail" in str(error_msg):
                print(f"   🐛 Debug Payload: {fields}")
            return False
        except Exception as e:
            print(f"   ⚠️ 更新网络错误: {e}")
            return False
    
    def create_record(self, fields: Dict, table_id: str = None) -> Optional[str]:
        """创建单条记录"""
        target_table_id = table_id if table_id else self.table_id
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{target_table_id}/records"
        
        try:
            resp = requests.post(url, headers=self._headers(), json={"fields": fields}, timeout=30)
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("record", {}).get("record_id")
            print(f"   ❌ 创建记录失败: {data.get('msg')}")
            return None
        except Exception as e:
            print(f"   ⚠️ 创建记录网络错误: {e}")
            return None

    def batch_create_records(self, records: List[Dict], table_id: str = None) -> bool:
        """批量创建记录"""
        if not self.token or not records:
            return False
        
        target_table_id = table_id if table_id else self.table_id
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.base_id}/tables/{target_table_id}/records/batch_create"
        
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
    
    def send_notification(self, title: str, content: str) -> bool:
        """
        发送飞书消息通知（使用 Webhook）
        
        Args:
            title: 通知标题
            content: 通知内容
        """
        webhook_url = getattr(config, 'FEISHU_WEBHOOK_URL', None)
        if not webhook_url:
            print("   ⚠️ 未配置 FEISHU_WEBHOOK_URL，跳过通知")
            return False
        
        try:
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": title},
                        "template": "blue"
                    },
                    "elements": [
                        {"tag": "div", "text": {"tag": "lark_md", "content": content}}
                    ]
                }
            }
            resp = requests.post(webhook_url, json=payload, timeout=10)
            if resp.status_code == 200:
                print(f"   📨 飞书通知已发送: {title}")
                return True
            else:
                print(f"   ⚠️ 飞书通知失败: {resp.text}")
                return False
        except Exception as e:
            print(f"   ⚠️ 飞书通知异常: {e}")
            return False
