# auto_publisher/wellcms_rpa.py
"""
WellCMS RPA 发布器
使用 Playwright 自动登录并发布文章
"""
import asyncio
from typing import Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
from .config import config


class WellCMSPublisher:
    """WellCMS RPA 发布器"""
    
    def __init__(self):
        self.username = config.WELLCMS_USERNAME
        self.password = config.WELLCMS_PASSWORD
        self.login_url = config.WELLCMS_LOGIN_URL
        self.admin_url = config.WELLCMS_ADMIN_URL
        self.post_url = config.WELLCMS_POST_URL
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def _init_browser(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
    
    async def _close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
    
    async def _login(self) -> bool:
        """登录 WellCMS"""
        try:
            await self.page.goto(self.login_url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)
            
            # 检查是否需要登录
            email_input = await self.page.query_selector('#email')
            if email_input:
                await self.page.fill('#email', self.username)
                await self.page.fill('#password', self.password)
                
                # 点击登录按钮
                submit_buttons = await self.page.query_selector_all('#submit')
                if submit_buttons:
                    await submit_buttons[-1].click()
                
                await asyncio.sleep(5)
            
            # 访问后台
            await self.page.goto(self.admin_url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(3)
            
            # 检查是否需要输入后台密码
            pwd_field = await self.page.query_selector('input[type=password]')
            if pwd_field:
                await pwd_field.fill(self.password)
                await self.page.keyboard.press('Enter')
                await asyncio.sleep(5)
            
            print("   ✅ WellCMS 登录成功")
            return True
            
        except Exception as e:
            print(f"   ❌ 登录失败: {e}")
            return False
    
    async def _publish_article(self, article: Dict) -> bool:
        """发布文章"""
        try:
            # 导航到发布页面
            await self.page.goto(self.post_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)
            
            # 填写标题
            await self.page.fill('#subject', article.get('title', ''))
            
            # 选择分类
            category_id = article.get('category_id', '1')
            try:
                await self.page.select_option('select[name="fid"]', category_id)
            except Exception:
                pass  # 分类选择失败不阻塞
            
            await asyncio.sleep(1)
            
            # 填写 SEO 字段
            await self.page.evaluate("""(data) => {
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
            await self.page.evaluate("""() => {
                const closedBox = document.querySelector('#closed-box');
                if (closedBox && !closedBox.checked) {
                    closedBox.click();
                }
            }""")
            await asyncio.sleep(0.5)
            
            # 填写 tags
            tags = article.get('tags', '')
            if tags:
                await self.page.evaluate("""(tagsValue) => {
                    const tagsInput = document.querySelector('#tags');
                    if (tagsInput) tagsInput.value = tagsValue;
                }""", tags)
            await asyncio.sleep(0.5)
            
            # 填写正文 (UEditor)
            html_content = article.get('html_content', '')
            await self.page.evaluate("""(content) => {
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
            await asyncio.sleep(2)
            
            # 点击提交
            await self.page.evaluate("""() => {
                document.getElementById('submit').click();
            }""")
            await asyncio.sleep(10)
            
            print(f"   ✅ 文章发布成功: {article.get('title', '')}")
            return True
            
        except Exception as e:
            print(f"   ❌ 发布失败: {e}")
            return False
    
    async def publish(self, article: Dict) -> bool:
        """
        发布文章到 WellCMS
        
        Args:
            article: 文章数据，包含 title, html_content, category_id, summary, keywords, description, tags
        """
        try:
            await self._init_browser()
            
            if not await self._login():
                return False
            
            return await self._publish_article(article)
            
        finally:
            await self._close_browser()
    
    def publish_sync(self, article: Dict) -> bool:
        """同步版本的发布方法"""
        return asyncio.run(self.publish(article))
