import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        os.makedirs("videos", exist_ok=True)
        context = await browser.new_context(
            record_video_dir="videos",
            record_video_size={"width": 1280, "height": 720}
        )
        page = await context.new_page()

        # 打开登录页面
        await page.goto("https://www.baiyuncloud.cc/login")
        
        # 等待页面加载完成
        await page.wait_for_load_state("networkidle")

        # 注入可视化鼠标指示器（Playwright 官方示例改编）
        await page.add_script_tag(content="""
        (() => {
          const box = document.createElement('playwright-mouse-pointer');
          const style = document.createElement('style');
          style.innerHTML = `
            playwright-mouse-pointer {
              position: fixed;
              z-index: 2147483647;
              width: 20px; height: 20px;
              background: rgba(0,0,0,.4);
              border: 2px solid white; border-radius: 10px;
              margin-top: -10px; margin-left: -10px;
              pointer-events: none;
              transition: background .2s, border-color .2s;
            }
            playwright-mouse-pointer.button-1 { background: rgba(0,0,0,.9); }
            playwright-mouse-pointer.button-2 { background: rgba(0,0,0,.9); }
            playwright-mouse-pointer.button-3 { background: rgba(0,0,0,.9); }
            playwright-mouse-pointer.button-4 { border-color: red; }
            playwright-mouse-pointer.button-5 { border-color: red; }
          `;
          document.head.appendChild(style);
          document.body.appendChild(box);
          document.addEventListener('mousemove', event => {
            box.style.left = event.pageX + 'px';
            box.style.top = event.pageY + 'px';
          }, true);
          document.addEventListener('mousedown', event => {
            box.classList.add('button-' + event.which);
          }, true);
          document.addEventListener('mouseup', event => {
            box.classList.remove('button-' + event.which);
          }, true);
        })();
        """)
        
        # 等待并定位邮箱与密码输入框（按占位符更稳健）
        email_input = page.get_by_placeholder("输入邮箱")
        await email_input.wait_for(state="visible")
        # 使用 mouse.move 将指针移动到邮箱输入框中心
        box = await email_input.bounding_box()
        await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
        # 鼠标移动到邮箱输入框
        await email_input.hover()
        await email_input.fill("183683266@qq.com")

        password_input = page.get_by_placeholder("输入密码")
        await password_input.wait_for(state="visible")
        # 使用 mouse.move 将指针移动到密码输入框中心
        box = await password_input.bounding_box()
        await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
        # 鼠标移动到密码输入框
        await password_input.hover()
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

        # 先关闭页面以完成视频文件写入
        try:
            await page.close()
            login_video_path = await page.video.path()
            print("登录流程视频:", login_video_path)
        except Exception as e:
            print("登录流程视频路径获取失败:", e)

        # 关闭旧上下文
        await context.close()

        # 创建新上下文并加载登录状态（仅在已保存时）
        try:
            new_context = await browser.new_context(
                storage_state="baiyun_state.json",
                record_video_dir="videos",
                record_video_size={"width": 1280, "height": 720}
            )
            new_page = await new_context.new_page()
            await new_page.goto("https://www.baiyuncloud.cc/console")
            content = await new_page.content()
            print("控制台页面内容长度:", len(content))
            await new_page.wait_for_timeout(3000)
            # 关闭页面并输出视频
            try:
                await new_page.close()
                console_video_path = await new_page.video.path()
                print("控制台访问视频:", console_video_path)
            except Exception as e:
                print("控制台访问视频路径获取失败:", e)

            await new_context.close()
        except Exception:
            pass
            

if __name__ == "__main__":
    asyncio.run(main())
