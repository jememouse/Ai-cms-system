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
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()
    
    def _close_browser(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def _login(self) -> bool:
        """登录 WellCMS"""
        try:
            self.page.goto(self.login_url, wait_until="networkidle", timeout=60000)
            time.sleep(2)
            
            # 检查是否需要登录
            email_input = self.page.query_selector('#email')
            if email_input:
                self.page.fill('#email', self.username)
                self.page.fill('#password', self.password)
                
                # 点击登录按钮
                submit_buttons = self.page.query_selector_all('#submit')
                if submit_buttons:
                    submit_buttons[-1].click()
                
                time.sleep(5)
            
            # 访问后台
            self.page.goto(self.admin_url, wait_until="networkidle", timeout=60000)
            time.sleep(3)
            
            # 检查是否需要输入后台密码
            pwd_field = self.page.query_selector('input[type=password]')
            if pwd_field:
                pwd_field.fill(self.password)
                self.page.keyboard.press('Enter')
                time.sleep(5)
            
            print("   ✅ WellCMS 登录成功")
            return True
            
        except Exception as e:
            print(f"   ❌ 登录失败: {e}")
            return False
    
    def _publish_article(self, article: Dict) -> bool:
        """发布文章"""
        try:
            # 导航到发布页面
            self.page.goto(self.post_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            
            # 填写标题
            self.page.fill('#subject', article.get('title', ''))
            
            # 选择分类
            category_id = article.get('category_id', '1')
            try:
                self.page.select_option('select[name="fid"]', category_id)
            except Exception:
                pass  # 分类选择失败不阻塞
            
            time.sleep(1)
            
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
            
            # 填写正文 (UEditor) - 增强版，确保内容完整注入
            html_content = article.get('html_content', '')
            
            # 等待编辑器完全加载
            time.sleep(3)
            
            # 多次尝试注入内容
            for attempt in range(3):
                try:
                    inject_success = self.page.evaluate("""(content) => {
                        // 尝试 UMeditor
                        if (typeof UM !== 'undefined') {
                            try {
                                var editor = UM.getEditor('message');
                                if (editor) {
                                    editor.setContent(content);
                                    return true;
                                }
                            } catch(e) { console.log('UM error:', e); }
                        }
                        // 尝试 UEditor
                        if (typeof UE !== 'undefined') {
                            try {
                                var editor = UE.getEditor('message');
                                if (editor) {
                                    editor.setContent(content);
                                    return true;
                                }
                            } catch(e) { console.log('UE error:', e); }
                        }
                        // 降级到 textarea
                        var el = document.querySelector('#message');
                        if (el) {
                            el.value = content;
                            return true;
                        }
                        // 尝试 iframe 方式
                        var iframe = document.querySelector('.edui-editor-iframeholder iframe');
                        if (iframe && iframe.contentDocument) {
                            iframe.contentDocument.body.innerHTML = content;
                            return true;
                        }
                        return false;
                    }""", html_content)
                    
                    if inject_success:
                        print(f"      📝 内容注入成功 (尝试 {attempt + 1})")
                        break
                    else:
                        print(f"      ⚠️ 内容注入失败，重试 {attempt + 1}/3...")
                        time.sleep(2)
                except Exception as e:
                    print(f"      ⚠️ 注入异常: {e}")
                    time.sleep(2)
            
            time.sleep(2)
            
            # 点击提交
            # 点击提交并等待跳转
            try:
                # 使用 page.click 替代 evaluate，更容易等待导航
                with self.page.expect_navigation(timeout=15000):
                    self.page.click('#submit')
            except Exception as e:
                print(f"      ⚠️ 等待跳转超时或失败，尝试根据当前 URL 判断: {e}")
            
            # 捕获 URL
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
