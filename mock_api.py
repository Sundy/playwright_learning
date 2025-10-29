import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 拦截对本地API的请求，并返回固定的mock响应
        async def mock_get_user(route):
            if route.request.method == "POST":
                await route.fulfill(status=200, json={"name": "sundy", "age": 30})
            else:
                # 非POST请求，直接继续实际请求
                await route.continue_()

        await page.route("**/get_user", mock_get_user)

        # 触发一次接口调用，验证拦截是否生效
        await page.goto("about:blank")
        result = await page.evaluate(
            """
            async () => {
              const res = await fetch('http://localhost:8000/get_user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: '任意名字' })
              });
              return await res.json();
            }
            """
        )
        print("Mock返回:", result)  # 期望: { name: 'sundy', age: 30 }

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
