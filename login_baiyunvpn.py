import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 打开登录页面
        await page.goto("https://www.baiyuncloud.cc/login")
        
        # 等待页面加载完成
        await page.wait_for_load_state("networkidle")
        
        # 等待并定位邮箱与密码输入框（按占位符更稳健）
        email_input = page.get_by_placeholder("输入邮箱")
        await email_input.wait_for(state="visible")
        await email_input.fill("183683266@qq.com")

        password_input = page.get_by_placeholder("输入密码")
        await password_input.wait_for(state="visible")
        await password_input.fill("004321-abcdef")

        # 点击登录按钮（按按钮可访问名称）
        await page.get_by_role("button", name="登录").click()

        # 等待跳转到控制台页（更明确的登录完成标志）
        try:
            await page.wait_for_url("**/console", timeout=60000)
        except Exception:
            # 如未跳转，至少等待网络静止以便后续检查
            await page.wait_for_load_state("networkidle")

        # 轮询等待认证数据出现（cookies 或 localStorage token）
        authed = False
        for _ in range(30):  # 最多等待 ~30s
            cookies = await context.cookies()
            ls_keys = await page.evaluate("Object.keys(localStorage)")
            has_token_like = any(k.lower() in [
                "token", "access_token", "authorization", "auth_token"
            ] for k in ls_keys)
            if cookies or has_token_like:
                authed = True
                break
            await page.wait_for_timeout(1000)

        if not authed:
            print("未检测到登录凭据（cookies 或 token），可能登录未成功。")
            await page.screenshot(path="login_failed.png")
        else:
            # 保存登录状态到本地文件（包含 cookies/localStorage）
            await context.storage_state(path="baiyun_state.json")
            print("登录成功，状态已保存")
        await page.wait_for_timeout(3000)

        # 关闭旧上下文
        await context.close()

        # 创建新上下文并加载登录状态（仅在已保存时）
        try:
            new_context = await browser.new_context(storage_state="baiyun_state.json")
            new_page = await new_context.new_page()
            await new_page.goto("https://www.baiyuncloud.cc/console")
            content = await new_page.content()
            print("控制台页面内容长度:", len(content))
            await new_page.wait_for_timeout(3000)
            # await new_context.close()
        except Exception:
            pass
            

if __name__ == "__main__":
    asyncio.run(main())
