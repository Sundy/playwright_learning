import os
import time
from playwright.sync_api import sync_playwright, TimeoutError


STATE_PATH = "baiyun_manual_state.json"


def _poll_login_success(page, max_wait_seconds: int = 180) -> bool:
    for _ in range(max_wait_seconds):
        if "/console" in page.url:
            return True
        try:
            has_token = page.evaluate("() => !!window.localStorage.getItem('idcnlink-token')")
        except Exception:
            has_token = False
        if has_token:
            return True
        time.sleep(1)
    return False


def test_manual_login_baiyun():
    """
    优先复用已保存登录态（storage_state）；无效或不存在则引导手动登录并保存。
    后续访问可继续使用已登录状态。
    """
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False, slow_mo=100)

    reused = False
    if os.path.exists(STATE_PATH):
        # 尝试复用已保存的登录态
        context = browser.new_context(storage_state=STATE_PATH)
        page = context.new_page()
        page.goto("https://www.baiyuncloud.cc/#/console", wait_until="domcontentloaded")
        try:
            page.wait_for_url("**/#/console", timeout=5000)
            has_token = page.evaluate("() => !!window.localStorage.getItem('idcnlink-token')")
            if has_token:
                reused = True
                print("已复用登录态，直接进入控制台。")
        except TimeoutError:
            pass
        if not reused:
            context.close()

    if not reused:
        # 无法复用时，进行手动登录并保存状态
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.baiyuncloud.cc/#/login", wait_until="domcontentloaded")
        print("请在浏览器中手动输入账号密码并登录，脚本将自动检测登录成功…")

        login_ok = _poll_login_success(page, max_wait_seconds=180)
        if not login_ok:
            page.screenshot(path="manual_login_failed.png")
            context.close()
            browser.close()
            p.stop()
            raise AssertionError("未检测到登录成功（URL或令牌），已保存截图 manual_login_failed.png")

        context.storage_state(path=STATE_PATH)
        print(f"已保存登录会话到 {STATE_PATH}")

    # 到这里已保证有登录态，可继续访问受保护页面
    page.goto("https://www.baiyuncloud.cc/#/console", wait_until="domcontentloaded")
    time.sleep(15)

    context.close()
    browser.close()
    p.stop()
