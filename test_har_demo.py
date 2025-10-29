from playwright.sync_api import sync_playwright


def test_har_record_and_replay():
    """
    小测试：
    1) 在上下文中录制一次对 POST /get_user 的请求（生成 network.har）
    2) 在新页面中从 HAR 回放相同请求，验证响应与录制一致
    """
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)

    # 1) 录制阶段：生成 network.har
    context_record = browser.new_context(record_har_path="network.har", record_har_mode="full")
    page_record = context_record.new_page()
    # 先进入同源页面以避免浏览器的 CORS 限制
    page_record.goto("http://localhost:8000")

    recorded_text = page_record.evaluate(
        """
        async () => {
          const res = await fetch('http://localhost:8000/get_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // 为了保证 HAR 匹配成功，回放时使用完全相同的请求体
            body: JSON.stringify({ name: 'har-demo' })
          });
          return await res.text();
        }
        """
    )
    # 关闭录制上下文以写出 HAR 文件
    context_record.close()

    # 2) 回放阶段：从 HAR 返回响应，不触达真实网络
    context_replay = browser.new_context()
    page_replay = context_replay.new_page()
    # 只对匹配到的 /get_user 使用 HAR；未录到的请求走真实网络（fallback）
    page_replay.route_from_har("network.har", url="**/get_user", not_found="fallback")

    # 回放阶段也进入同源页面再发起请求
    page_replay.goto("http://localhost:8000")
    replay_text = page_replay.evaluate(
        """
        async () => {
          const res = await fetch('http://localhost:8000/get_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: 'har-demo' })
          });
          return await res.text();
        }
        """
    )

    print("录制阶段响应:\n", recorded_text)
    print("回放阶段响应:\n", replay_text)
    assert replay_text == recorded_text

    # 结束
    context_replay.close()
    browser.close()
    p.stop()
