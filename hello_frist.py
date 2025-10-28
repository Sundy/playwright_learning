from time import sleep
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False,slow_mo=50)
    page = browser.new_page()
    page.goto("http://www.baidu.com/")
    page.screenshot(path="baidu.png")
    # 鼠标移动到输入框
    input_box = page.locator('#kw')
    input_box.hover()
    input_box.screenshot(path="input_box.png")
    
    page.wait_for_timeout(3000)
    browser.close()
    
