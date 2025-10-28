import re
from playwright.sync_api import Page, expect

def test_login_and_save_state(page: Page):
    # 打开登录页面
    page.goto("https://www.baiyuncloud.cc/login")

    # 等待页面加载完成
    page.wait_for_load_state("networkidle")

    # 定位邮箱与密码输入框并填入信息
    email_input = page.get_by_placeholder("输入邮箱")
    email_input.wait_for(state="visible")
    email_input.fill("183683266@qq.com")

    password_input = page.get_by_placeholder("输入密码")
    password_input.wait_for(state="visible")
    password_input.fill("004321-abcdef")

    # 点击登录按钮
    page.get_by_role("button", name="登录").click()

    # 等待跳转到控制台页
    try:
        page.wait_for_url("**/console", timeout=60000)
    except Exception:
        page.wait_for_load_state("networkidle")

    # 检查登录凭据（cookies 或 localStorage token）
    cookies = page.context.cookies()
    ls_keys = page.evaluate("Object.keys(localStorage)")
    has_token_like = any(k.lower() in [
        "token", "access_token", "authorization", "auth_token"
    ] for k in ls_keys)

    if not cookies and not has_token_like:
        page.screenshot(path="login_failed.png")
        assert False, "未检测到登录凭据（cookies 或 token），可能登录未成功。"

    # 保存登录状态到本地文件（包含 cookies/localStorage）
    page.context.storage_state(path="baiyun_state.json")

    # 断言控制台页可见（URL包含 console）
    expect(page).to_have_url(re.compile("console"))
