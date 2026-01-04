# step3_publish/wellcms_rpa.py
"""
WellCMS RPA 发布器
使用 Playwright (Sync) 自动登录并发布文章
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Optional
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
            
            # 填写正文 (UEditor)
            html_content = article.get('html_content', '')
            self.page.evaluate("""(content) => {
                // 尝试 UMeditor
                if (typeof UM !== 'undefined') {
                    try { UM.getEditor('message').setContent(content); return; } catch(e) {}
                }
                // 尝试 UEditor
                if (typeof UE !== 'undefined') {
                    try { UE.getEditor('message').setContent(content); return; } catch(e) {}
                }
                // 降级到 textarea
                const el = document.querySelector('#message');
                if (el) el.value = content;
            }""", html_content)
            time.sleep(2)
            
            # 点击提交
            self.page.evaluate("""() => {
                document.getElementById('submit').click();
            }""")
            time.sleep(10)
            
            print(f"   ✅ 文章发布成功: {article.get('title', '')}")
            return True
            
        except Exception as e:
            print(f"   ❌ 发布失败: {e}")
            return False
    
    def publish(self, article: Dict) -> bool:
        """
        发布文章到 WellCMS (同步)
        """
        try:
            self._init_browser()
            
            if not self._login():
                return False
            
            return self._publish_article(article)
            
        finally:
            self._close_browser()
            
    def publish_sync(self, article: Dict) -> bool:
        """兼容旧接口"""
        return self.publish(article)
