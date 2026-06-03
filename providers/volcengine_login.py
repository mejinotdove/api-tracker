from pathlib import Path

from playwright.sync_api import sync_playwright


LOGIN_URL = "https://console.volcengine.com/auth/login"
TARGET_URL = "https://console.volcengine.com/home"
COOKIE_DOMAIN = ".volcengine.com"


def login_and_get_cookies(username: str, password: str, cookie_file: Path) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        page = context.new_page()

        page.goto(LOGIN_URL, wait_until="networkidle")

        page.get_by_role("textbox", name="请输入账号名/账号ID").fill(username)
        page.get_by_role("textbox", name="请输入登录密码").fill(password)
        page.get_by_role("button", name="登录").click()

        page.wait_for_url(TARGET_URL, timeout=30000)

        all_cookies = context.cookies()
        browser.close()

    volc_cookies = [
        c for c in all_cookies
        if c["domain"] in (COOKIE_DOMAIN, "console.volcengine.com")
    ]
    cookie_str = "; ".join(f'{c["name"]}={c["value"]}' for c in volc_cookies)

    cookie_file.parent.mkdir(parents=True, exist_ok=True)
    cookie_file.write_text(cookie_str)

    return cookie_str
