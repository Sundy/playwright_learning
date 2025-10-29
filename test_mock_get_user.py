import time
from playwright.sync_api import sync_playwright


def test_mock_append_line_keeps_browser_open():
    p = sync_playwright().start()
    # 打开真实浏览器，并减慢动作便于观察
    browser = p.chromium.launch(headless=False, slow_mo=200)
    page = browser.new_page()

    # 拦截 /get_user 请求，基于真实响应再追加一行 "sundy, 30"
    def handle(route):
        resp = route.fetch()  # 先获取真实接口返回
        original_text = resp.text()
        mocked_text = original_text + "\nsundy, 30"
        route.fulfill(
            status=200,
            body=mocked_text,
            headers={"Content-Type": "text/plain"},
        )

    page.route("**/get_user", handle)

    # 加载一个带悬浮按钮的页面，点击后发出请求
    page.goto("http://www.baidu.com")
    page.set_content(
        """
        <!doctype html>
        <html>
        <head>
          <meta charset=\"utf-8\">
          <title>Mock Get User Test</title>
          <style>
            #mock-btn {
              position: fixed;
              left: 120px;
              top: 120px;
              padding: 12px 16px;
              background: #1677ff;
              color: #fff;
              border: none;
              border-radius: 8px;
              box-shadow: 0 6px 16px rgba(0,0,0,0.15);
              cursor: pointer;
              z-index: 9999;
            }
            #output {
              position: fixed;
              right: 20px;
              bottom: 70px;
              background: rgba(0,0,0,0.75);
              color: #fff;
              padding: 10px;
              border-radius: 8px;
              white-space: pre-wrap;
              max-width: 50vw;
              max-height: 40vh;
              overflow: auto;
              font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            }
          </style>
        </head>
        <body>
          <button id=\"mock-btn\">发送请求</button>
          <pre id=\"output\"></pre>
          <script>
            async function sendRequest() {
              try {
                const res = await fetch('http://localhost:8000/get_user', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ name: '秦始皇' })
                });
                const text = await res.text();
                document.getElementById('output').textContent = text;
                return text;
              } catch (e) {
                document.getElementById('output').textContent = '请求失败: ' + e;
                throw e;
              }
            }
            document.getElementById('mock-btn').addEventListener('click', () => {
              sendRequest();
            });
          </script>
        </body>
        </html>
        """
    )

    # 等待结果显示并获取内容
    page.wait_for_function("() => (document.querySelector('#output')?.textContent || '').includes('sundy, 30')")
    result = page.text_content("#output") or ""

    # 断言追加行存在
    assert "sundy, 30" in result
    print("响应内容如下:\n", result)
    page.wait_for_timeout(60000)
    # 保持浏览器窗口打开，不主动关闭
