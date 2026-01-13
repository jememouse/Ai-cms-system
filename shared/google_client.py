# shared/google_client.py
"""
Google Sheets 客户端
完全兼容 FeishuClient 接口，支持平滑迁移
支持多工作表 (cms, xhs) 动态切换
"""
import os
import json
import time
import uuid
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Optional, Any
from . import config

class GoogleSheetClient:
    """Google Sheets 客户端"""
    
    def __init__(self):
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.creds_file = config.GOOGLE_CREDENTIALS_FILE
        self.sheet_id = config.GOOGLE_SHEET_ID
        
        self.client = None
        self.spreadsheet = None
        
        if os.path.exists(self.creds_file):
            self._connect()
        else:
            print(f"⚠️ Google Credentials 文件未找到: {self.creds_file}")

    def _connect(self):
        """连接到 Google Spreadsheet"""
        try:
            creds = None
            
            # 1. 尝试从环境变量读取
            json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
            if json_str:
                # print(f"🔍 检测到环境变量 GOOGLE_CREDENTIALS_JSON (长度: {len(json_str)})") # Debug
                try:
                    keyfile_dict = json.loads(json_str)
                    creds = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict, self.scope)
                    # print("✅ 成功解析 Service Account JSON")
                except json.JSONDecodeError as e:
                    print(f"❌ 环境变量 JSON 解析失败: {e}")
            else:
                pass 
                # print("ℹ️ 未检测到环境变量 GOOGLE_CREDENTIALS_JSON")

            # 2. 如果环境变量没搞定，再尝试从文件加载
            if not creds:
                if os.path.exists(self.creds_file):
                    # print(f"🔍 尝试从文件加载: {self.creds_file}")
                    creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, self.scope)
                else:
                    # 只有当两个都失败时，才打印这个警告
                    print(f"⚠️ Google Credentials 文件未找到: {self.creds_file}")

            if not creds:
                print("❌ [Fatal] 未找到有效的 Google Credentials (既无 ENV 也无 File)")
                self.client = None
                return

            # print("🔐 正在进行 gspread 认证...")
            self.client = gspread.authorize(creds)
            
            if self.sheet_id:
                self.spreadsheet = self.client.open_by_key(self.sheet_id)
                print(f"✅ Google Spreadsheet 连接成功: {self.spreadsheet.title}")
            
        except Exception as e:
            print(f"❌ Google Sheet 连接异常: {e}")
            # 打印更详细的错误堆栈，如果是认证错误
            import traceback
            traceback.print_exc()
            self.client = None

    def _get_sheet(self, table_id: str = None):
        """
        根据 table_id (即 worksheet name) 获取 Worksheet 对象
        如果 table_id 为空，使用默认 'cms'
        """
        if not self.spreadsheet: return None
        
        target_name = table_id if table_id else "cms"
        
        try:
            return self.spreadsheet.worksheet(target_name)
        except gspread.WorksheetNotFound:
            print(f"⚠️ 工作表 '{target_name}' 不存在，尝试创建...")
            try:
                # 创建新表
                new_sheet = self.spreadsheet.add_worksheet(title=target_name, rows=100, cols=20)
                # 初始化表头 (根据不同表结构)
                if target_name == "xhs":
                    # Aligned with step4_social/agent_runner.py
                    headers = ["Title", "Content", "Keywords", "Source", "Status", "Cover", "生成时间", "XHS_Link", "Post_Date"]
                else:
                    # Aligned with all steps
                    headers = [
                        "Topic", "Status", "大项分类", "Title", "HTML_Content", 
                        "摘要", "关键词", "描述", "Tags", "Schema_FAQ", "One_Line_Summary",
                        "Key_Points", "URL", "发布时间", "XHS_Status", "选题生成时间", "生成时间"
                    ]
                new_sheet.append_row(headers)
                print(f"✅ 已创建并初始化工作表: {target_name}")
                return new_sheet
            except Exception as e:
                print(f"❌ 创建工作表失败: {e}")
                return None

    def fetch_records_by_status(self, status: str, category: str = None, limit: int = 50) -> List[Dict]:
        """
        获取指定状态的记录
        兼容 FeishuClient 接口
        """
        # 注意：此方法默认针对 CMS 主表
        sheet = self._get_sheet("cms")
        if not sheet: return []
        
        try:
            all_records = sheet.get_all_records()
            results = []
            
            for i, row in enumerate(all_records):
                # 没有 record_id 列了，直接使用 row_index
                row_num = i + 2
                rec_id = f"row:{row_num}"
                
                # 注入临时 record_id 用于更新
                row["record_id"] = rec_id
                
                # 筛选逻辑
                if str(row.get("Status")) == status:
                    if category:
                        if str(row.get("大项分类")) == category:
                            results.append(row)
                    else:
                        results.append(row)
                        
                if len(results) >= limit:
                    break
                    
            print(f"   📋 [GoogleSheet:cms] 获取 {len(results)} 条 {status} 记录")
            return results
        except Exception as e:
            print(f"⚠️ Fetch Error: {e}")
            return []

    def update_record(self, record_id: str, fields: Dict, retry: bool = True) -> bool:
        """
        更新记录 (默认 cms 表)
        Args:
            record_id: 可以是 "row:5" 格式，或者是 UUID
        """
        # 简单处理：目前业务只更新 CMS 表的状态
        sheet = self._get_sheet("cms")
        if not sheet: return False
        
        try:
            row_num = -1
            
            # 策略 1: 解析 Row ID
            if record_id.startswith("row:"):
                try:
                    row_num = int(record_id.split(":")[1])
                except:
                    pass
            
            # 策略 2: 如果不是 Row ID，或者是 UUID，需要扫描查找
            if row_num == -1:
                cell = sheet.find(record_id)
                if cell:
                    row_num = cell.row
            
            if row_num == -1:
                print(f"❌ 未找到记录 ID: {record_id}")
                return False
                
            # 执行更新
            headers = sheet.row_values(1)
            
            for key, value in fields.items():
                if key in headers:
                    col_index = headers.index(key) + 1
                    # 格式处理
                    if isinstance(value, (list, dict)):
                        val_str = json.dumps(value, ensure_ascii=False)
                    else:
                        val_str = str(value)
                        
                    sheet.update_cell(row_num, col_index, val_str)
                else:
                    print(f"⚠️ 警告: 字段 '{key}' 不在 Sheet 表头中，已忽略")
            
            return True
            
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            return False

    def create_record(self, fields: Dict, table_id: str = None) -> Optional[str]:
        """创建记录 (支持指定 table_id/worksheet)"""
        sheet = self._get_sheet(table_id)
        if not sheet: return None
        
        try:
            # 移除 record_id 生成逻辑 (用户不需要)
            now_str = time.strftime("%Y-%m-%d %H:%M:%S")
            fields["created_at"] = now_str
            
            # 自动填充 "生成时间" (System Created Time)
            if "生成时间" not in fields:
                fields["生成时间"] = now_str
            
            # 对齐表头
            headers = sheet.row_values(1)
            row_data = []
            
            for h in headers:
                val = fields.get(h, "")
                if isinstance(val, (list, dict)):
                    val = json.dumps(val, ensure_ascii=False)
                row_data.append(val)
                
            sheet.append_row(row_data)
            return "row:new" # 无法立即知道 row number，除非再查一次
            
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            return None

    def batch_create_records(self, records: List[Dict], table_id: str = None) -> bool:
        """批量创建"""
        sheet = self._get_sheet(table_id)
        if not sheet or not records: return False
        
        try:
            headers = sheet.row_values(1)
            rows_to_append = []
            
            for r in records:
                # 生成 ID
                if "record_id" not in r:
                    r["record_id"] = str(uuid.uuid4())
                
                row_data = []
                for h in headers:
                    val = r.get(h, "")
                    if isinstance(val, (list, dict)):
                        val = json.dumps(val, ensure_ascii=False)
                    row_data.append(val)
                rows_to_append.append(row_data)
                
            sheet.append_rows(rows_to_append)
            print(f"   ✅ Google Sheet [{sheet.title}]: 批量插入 {len(rows_to_append)} 条")
            return True
            
        except Exception as e:
            print(f"❌ 批量创建失败: {e}")
            return False

    def send_notification(self, title: str, content: str) -> bool:
        """
        发送飞书消息通知
        """
        webhook_url = getattr(config, 'FEISHU_WEBHOOK_URL', None)
        if not webhook_url: return False
        # 简化处理，仅打印，或之后恢复 requests 调用
        print(f"📨 [Notification] {title}: {content}")
        return True
