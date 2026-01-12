# step3_publish/wellcms_rpa.py
"""
WellCMS RPA 发布器
使用 Playwright (Sync) 自动登录并发布文章
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Tuple, Optional
from playwright.sync_api import sync_playwright, Page, Browser
from shared import config


class WellCMSPublisher:
    """WellCMS RPA 发布器 (同步版)"""
    
    def __init__(self, username: str = None, password: str = None):
        """
        初始化发布器
        
        Args:
            username: CMS 用户名 (不传则使用 config 默认值)
            password: CMS 密码 (不传则使用 config 默认值)
        """
        self.username = username or config.WELLCMS_USERNAME
        self.password = password or config.WELLCMS_PASSWORD
        self.login_url = config.WELLCMS_LOGIN_URL
        self.admin_url = config.WELLCMS_ADMIN_URL
        self.post_url = config.WELLCMS_POST_URL
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    def _init_browser(self):
        """初始化浏览器"""
        self.playwright = sync_playwright().start()
        # 支持通过环境变量控制 Headless (方便本地调试)
        is_headless = os.getenv("HEADLESS", "true").lower() == "true"
        
        # 增加防检测参数
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-infobars",
            "--window-size=1920,1080",
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        self.browser = self.playwright.chromium.launch(
            headless=is_headless,
            args=args
        )
        
        # 使用特定 UserAgent 和 Viewport 创建 Context
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai"
        )
        # 注入 stealth js
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        self.page = context.new_page()
    
    def _close_browser(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def _login(self) -> bool:
        """
        登录 WellCMS (基于用户提供的精确 Selector)
        Step 1: https://heyijiapack.com/news/user-login.html
        Step 2: https://heyijiapack.com/news/admin/index.php
        """
        print("      🔐 [RPA] 启动精确匹配登录流程...")
        try:
            # ==================================================================
            # Step 1: 前台登录
            # ==================================================================
            print(f"      📍 [Step 1] 访问前台: {self.login_url}")
            self.page.goto(self.login_url, wait_until="networkidle", timeout=60000)
            
            try:
                # 检查 #email 是否存在
                if self.page.wait_for_selector('#email', state="visible", timeout=5000):
                    print("      👀 [Step 1] 填写账号密码...")
                    # 用户提供的 Selector: #email, #password
                    self.page.fill('#email', self.username)
                    self.page.fill('#password', self.password)
                    
                    print("      🖱️ [Step 1] 点击登录按钮 (#submit)...")
                    # 用户提供的 Selector: #submit
                    self.page.click('#submit')
                    
                    print("      ⏳ [Step 1] 等待跳转...")
                    self.page.wait_for_load_state("networkidle", timeout=20000)
                else:
                    print("      ℹ️ [Step 1] 未检测到输入框，可能已登录")
            except Exception as e:
                print(f"      ⚠️ [Step 1] 异常: {e}")

            # ==================================================================
            # Step 2: 后台二次验证
            # ==================================================================
            print(f"      📍 [Step 2] 强制访问后台: {self.admin_url}")
            self.page.goto(self.admin_url, wait_until="networkidle", timeout=60000)
            
            # 检查是否被踢回
            if "user-login" in self.page.url:
                 print(f"      ❌ [Step 2] 失败: 被重定向回前台登录页 ({self.page.url})")
                 return False

            try:
                # 页面包含: <input id="password"> 和 <button id="submit">
                # 注意: 这里 input id 也是 password，所以要确保是在 admin 页面下
                if self.page.wait_for_selector('input#password', state="visible", timeout=3000):
                    print("      🔐 [Step 2] 填写后台密码...")
                    self.page.fill('input#password', self.password)
                    
                    print("      🖱️ [Step 2] 点击后台登录按钮 (#submit)...")
                    # 为了防止和顶部搜索搞混（虽然用户说ID是submit），我们加限定
                    # 比如 button#submit 或 input#submit
                    # 用户提供: <button id="submit" ...>
                    self.page.click('button#submit')
                    
                    print("      🔄 [Step 2] 等待跳转...")
                    self.page.wait_for_load_state("networkidle", timeout=20000)
            except Exception as e:
                 print(f"      ℹ️ [Step 2] 无需二次验证或异常: {e}")

            # ==================================================================
            # 结果检查
            # ==================================================================
            current_url = self.page.url
            if "operate-search" in current_url:
                 print(f"      ❌ [Result] 误触搜索页 ({current_url})")
                 return False
                 
            if "admin" in current_url and "login" not in current_url:
                print("      ✅ [Result] 登录成功")
                return True
            else:
                print(f"      ❌ [Result] 登录失败 ({current_url})")
                return False
                
        except Exception as e:
            print(f"      ❌ 登录流程异常终止: {e}")
            return False
    
    def _publish_article(self, article: Dict) -> Tuple[bool, str]:
        """发布文章"""
        try:
            # 导航到发布页面
            self.page.goto(self.post_url, timeout=60000, wait_until="networkidle")
            time.sleep(2)
            
            # 填写标题
            # 填写标题
            try:
                self.page.fill('#subject', article.get('title', ''), timeout=30000)
            except Exception as e:
                print(f"      ❌ 填写标题失败: {e}")
                print(f"      📄 当前页面: {self.page.title()}")
                print(f"      🔗 当前URL: {self.page.url}")
                # 尝试保存截图 (CI/CD Artifacts 无法直接看，但本地调试有用)
                try: 
                    self.page.screenshot(path="error_publish_fail.png") 
                except: pass
                raise e
            
            # 选择分类
            category_id = article.get('category_id', '1')
            try:
                self.page.select_option('select[name="fid"]', category_id)
            except Exception:
                pass  # 分类选择失败不阻塞
            
            time.sleep(1)
            
            # -------------------------------------------------------------------
            # 🖼️ 封面图处理 (修复列表页无图问题)
            # -------------------------------------------------------------------
            html_content = article.get('html_content', '')
            import re
            img_match = re.search(r'src="([^"]+)"', html_content)
            if img_match:
                img_url = img_match.group(1)
                img_url = img_url.replace('&amp;', '&') # 还原用于下载
                print(f"      🖼️ 发现封面图: {img_url[:50]}...")
                
                try:
                    # 下载图片
                    import requests
                    import tempfile
                    
                    # 使用临时文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        try:
                            headers = {
                                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
                            }
                            # 重试机制 (Pollinations.ai 响应较慢)
                            resp = None
                            for retry in range(3):
                                try:
                                    resp = requests.get(img_url, headers=headers, timeout=30)
                                    if resp.status_code == 200:
                                        break
                                except requests.exceptions.Timeout:
                                    if retry < 2:
                                        print(f"      ⏳ 封面图下载超时，重试 {retry + 1}/3...")
                                        time.sleep(2)
                                    else:
                                        raise
                            if resp and resp.status_code == 200:
                                tmp.write(resp.content)
                                tmp.flush()
                                tmp_path = tmp.name
                                
                                # 上传到缩略图输入框
                                # Selector: input element inside the label with class img_1 or data-assoc
                                # Based on HTML dump: <input type="file" multiple="multiple" data-assoc="img_1">
                                file_input = self.page.query_selector('input[data-assoc="img_1"]')
                                if file_input:
                                    file_input.set_input_files(tmp_path)
                                    print("      📤 封面图上传中...")
                                    time.sleep(3) # 等待上传完成
                                else:
                                    print("      ⚠️ 未找到封面图上传框")
                            else:
                                print(f"      ⚠️ 封面图下载失败: {resp.status_code}")
                        except Exception as e:
                            print(f"      ⚠️ 封面图处理异常: {e}")
                        finally:
                            # 清理临时文件
                            try:
                                os.unlink(tmp_path)
                            except:
                                pass
                except Exception as e:
                     print(f"      ⚠️ 封面图逻辑错误: {e}")
            # -------------------------------------------------------------------
            
            # 填写 SEO 字段
            self.page.evaluate("""(data) => {
                const brief = document.querySelector('#brief');
                if (brief) brief.value = data.summary || '';
                
                const keyword = document.querySelector('#keyword');
                if (keyword) keyword.value = data.keywords || '';
                
                const description = document.querySelector('#description');
                if (description) description.value = data.description || '';
            }""", {
                'summary': article.get('summary', ''),
                'keywords': article.get('keywords', ''),
                'description': article.get('description', '')
            })
            
            # 勾选"禁止评论"
            self.page.evaluate("""() => {
                const closedBox = document.querySelector('#closed-box');
                if (closedBox && !closedBox.checked) {
                    closedBox.click();
                }
            }""")
            time.sleep(0.5)
            
            # 填写 tags
            tags = article.get('tags', '')
            if tags:
                self.page.evaluate("""(tagsValue) => {
                    const tagsInput = document.querySelector('#tags');
                    if (tagsInput) tagsInput.value = tagsValue;
                }""", tags)
            time.sleep(0.5)
            
            # 填写正文 (UEditor) - 增强版
            html_content = article.get('html_content', '')
            
            # 🚨 关键修复：移除 4字节字符 (Emoji)
            # 原因：MySQL utf8 编码不支持 Emoji，会导致保存时从 Emoji 处被截断
            # 匹配所有 Unicode 代理对 (Surrogate Pairs) 和非 BMP 字符
            try:
                # 过滤掉所有 ord > 65535 的字符
                html_content = "".join(c for c in html_content if ord(c) <= 65535)
                print("      🛡️ 已过滤 4字节字符 (Emoji) 以防截断")
            except Exception as e:
                print(f"      ⚠️ 字符过滤异常: {e}")

            # 恢复图片功能 (之前误判为图片导致截断，实际是 Emoji)
            # 这里的图片 URL 已经在 Step 2 被转义过 &amp; 了，安全。
            
            # 多次尝试注入内容
            injection_successful = False
            for attempt in range(3):
                try:
                    # 尝试注入
                    inject_success = False
                    
                    # 方案 1: 标准 API 注入 (并在注入后读取验证)
                    result_len = self.page.evaluate("""(content) => {
                        var editor = null;
                        if (typeof UM !== 'undefined') {
                            editor = UM.getEditor('message');
                        } else if (typeof UE !== 'undefined') {
                            editor = UE.getEditor('message');
                        }
                        
                        if (editor) {
                            editor.setContent(content);
                            return editor.getContent().length; // 返回注入后的长度
                        }
                        return -1;
                    }""", html_content)
                    
                    # 验证注入结果
                    if result_len > len(html_content) * 0.5: # 允许少许差异（HTML格式化），但不能太短
                        print(f"      📝 内容注入成功 (长度: {result_len}/{len(html_content)})")
                        inject_success = True
                    elif result_len != -1:
                        print(f"      ⚠️ 内容注入疑似截断 (长度差异大: {result_len}/{len(html_content)})，尝试备用方案...")
                        # 只有当 API 注入失败或截断时，才走下面的 fallback
                    
                    # 方案 2: 备用 - Frame 直接注入 (如果标准 API 失败)
                    if not inject_success:
                        # 查找编辑器 iframe
                        frames = self.page.frames
                        target_frame = None
                        for frame in frames:
                            if "ueditor" in frame.name or "message" in frame.name:
                                target_frame = frame
                                break
                        
                        if target_frame:
                            # 直接写入 iframe body
                            target_frame.evaluate(f"document.body.innerHTML = `{html_content.replace('`', '\\\\`')}`")
                            # 同步回 textarea (尝试触发编辑器的 sync)
                            self.page.evaluate("""() => {
                                if (typeof UM !== 'undefined') UM.getEditor('message').sync();
                                if (typeof UE !== 'undefined') UE.getEditor('message').sync();
                            }""")
                            print("      📝 使用 iframe 直接注入 (Force Mode)")
                            inject_success = True
                    
                    # 方案 3: Textarea 兜底 (Source Mode)
                    if not inject_success:
                         self.page.fill('textarea[name="message"]', html_content)
                         print("      📝 使用 Textarea 注入")
                         inject_success = True

                    if inject_success:
                        time.sleep(2) # 注入后等待渲染
                        injection_successful = True
                        break
                        print(f"      ⚠️ 内容注入失败，重试 {attempt + 1}/3...")
                        time.sleep(2)
                except Exception as e:
                    print(f"      ⚠️ 注入异常: {e}")
                    time.sleep(2)
            
            time.sleep(2)
            
            # 点击提交
            # 点击提交并等待跳转
            # 🚨 终极保险：强制将内容同步到 textarea
            # 无论之前的注入方式如何，提交前必须确保 textarea 有值，因为表单提交的是 textarea
            self.page.evaluate(f"""() => {{
                var el = document.querySelector('textarea[name="message"]');
                if (el) {{
                    el.value = `{html_content.replace('`', '\\\\`')}`;
                }}
            }}""")
            print("      🛡️ 已强制同步内容到 Textarea")

            # 点击提交按钮
            try:
                with self.page.expect_navigation(timeout=60000):
                    self.page.click('#submit')
            except Exception as e:
                print(f"      ⚠️ 等待跳转超时或失败，尝试根据当前 URL 判断: {e}")
            
            # -------------------------------------------------------------------
            # 🔗 URL 修正逻辑 (修复 "Same Link" Bug)
            # -------------------------------------------------------------------
            # 原问题：发布后直接取 page.url，得到的是后台列表页地址
            # 解决方案：
            # 1. 提交后，自动跳转到列表页 (或手动跳转)
            # 2. 在列表页根据标题找到对应的行
            # 3. 提取 data-tid 或 href 中的 tid
            # 4. 拼接前台 URL
            
            print("      🔍 正在解析文章真实 URL...")
            time.sleep(2) # 等待列表页加载
            
            # 确保在列表页 (content-list)
            # 无论之前是在哪，强制去一次内容管理页，确保能找到刚发的文章
            list_url = f"{self.admin_url}?0=content&1=list"
            # 重试机制提取 URL
            max_retries = 3
            tid = None
            
            for attempt in range(max_retries):
                if attempt > 0:
                     print(f"      🔄 尝试 {attempt + 1}/{max_retries}: 正在重试提取 TID...")

                try:
                    # 1. 强制刷新/跳转列表页
                    self.page.goto(list_url, wait_until="networkidle", timeout=30000)
                    
                    # 2. 显式等待表格加载 (尝试等待3秒)
                    try:
                         # 轮询检查是否有包含 data-tid 的行
                         for _ in range(3):
                             found = False
                             for frame in self.page.frames:
                                 if frame.locator("tr[data-tid]").count() > 0:
                                     found = True
                                     break
                             if found: break
                             time.sleep(1)
                    except:
                        pass

                    # 3. 遍历提取
                    frames = self.page.frames
                    print(f"      👀 页面共有 {len(frames)} 个 Frame, 正在查找内容表格...")
                    
                    for frame in frames:
                        rows = frame.locator("tr[data-tid]")
                        count = rows.count()
                        
                        if count > 0:
                            first_row = rows.first
                            tid_attr = first_row.get_attribute("data-tid")
                            if tid_attr:
                                tid = tid_attr
                                print(f"      ✅ [Strategy:Frame+FirstRow] 找到 TID: {tid}")
                                break
                            
                        # Fallback Link (兼容旧版/另一种渲染)
                        links = frame.locator("a[href*='tid=']").all()
                        for link in links[:5]:
                            href = link.get_attribute("href")
                            if href:
                                import re
                                match = re.search(r'tid=(\d+)', href)
                                if match:
                                    tid = match.group(1)
                                    print(f"      ✅ [Strategy:Link] 找到 TID: {tid}")
                                    break
                        if tid: break
                    
                    if tid:
                        break
                    else:
                         print("      ⚠️ 当前页面未找到 TID，等待后重试...")
                         time.sleep(2)

                except Exception as e:
                    print(f"      ⚠️ 提取过程异常: {e}")
                    time.sleep(2)
                
            # 构造最终 URL
            if tid:
                # 格式: https://heyijiapack.com/news/read-{tid}.html
                current_url = f"https://heyijiapack.com/news/read-{tid}.html"
            else:
                # 兜底
                print("      ⚠️ 未能提取 TID (遍历所有 Frame 后)，使用当前页面 URL")
                current_url = self.page.url
            
            print(f"   ✅ 文章发布成功: {article.get('title', '')}")
            print(f"   🔗 链接: {current_url}")
            
            return True, current_url
            
        except Exception as e:
            print(f"   ❌ 发布失败: {e}")
            return False, ""
    
    def publish(self, article: Dict) -> Tuple[bool, str]:
        """
        发布文章到 WellCMS (同步)
        Returns: (success, url)
        """
        try:
            self._init_browser()
            
            if not self._login():
                return False, ""
            
            return self._publish_article(article)
            
        finally:
            self._close_browser()
            
    def publish_sync(self, article: Dict) -> Tuple[bool, str]:
        """兼容旧接口"""
        return self.publish(article)
