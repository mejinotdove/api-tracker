from pathlib import Path
import time
from typing import Optional

import requests

from .base import BaseProvider, UsageInfo, Item


VOLC_API = "https://console.volcengine.com/api/top/ark/cn-beijing/2024-01-01/GetCodingPlanUsage"

LEVEL_NAMES = {
    "session": "5小时",
    "weekly": "1  周",
    "monthly": "1  月",
}


def _fmt_remaining(ts: int) -> str:
    remaining = ts - int(time.time())
    if remaining <= 0:
        return "0s"
    days = remaining // 86400
    hours = (remaining % 86400) // 3600
    minutes = (remaining % 3600) // 60
    seconds = remaining % 60
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分")
    parts.append(f"{seconds}秒")
    return "".join(parts)


class VolcengineProvider(BaseProvider):
    def get_usage(self) -> UsageInfo:
        cookie_str = self.config.get("cookie", "")
        cookie_file = self.config.get("cookie_file", "")

        if not cookie_str and cookie_file:
            try:
                cookie_str = Path(cookie_file).expanduser().read_text().strip()
            except OSError:
                return UsageInfo(0, 0, error=f"cannot read cookie_file: {cookie_file}")

        if not cookie_str:
            return UsageInfo(0, 0, error="cookie not configured")

        data = self._fetch_usage(cookie_str)
        if data is None:
            return UsageInfo(0, 0, error="failed to fetch Coding Plan usage")

        quota_usage = data.get("Result", {}).get("QuotaUsage", [])

        session_pct = 0.0
        weekly_pct = 0.0
        monthly_pct = 0.0
        items = []
        for q in quota_usage:
            level = q.get("Level", "")
            percent = float(q.get("Percent", 0))
            reset_ts = int(q.get("ResetTimestamp", 0))
            remaining_str = _fmt_remaining(reset_ts) if reset_ts else ""
            name = LEVEL_NAMES.get(level, level)
            items.append(
                Item(
                    name=LEVEL_NAMES.get(level, level),
                    used=round(percent, 1),
                    total=100,
                    unit="%",
                    note=f"下次刷新: {remaining_str}",
                    level=level,
                )
            )
            if level == "session":
                session_pct = round(percent, 1)
            elif level == "weekly":
                weekly_pct = round(percent, 1)
            elif level == "monthly":
                monthly_pct = round(percent, 1)

        return UsageInfo(
            balance=session_pct,
            total=100,
            today_usage=weekly_pct or 0,
            currency="%",
            items=items,
            models=[],
        )

    def _fetch_usage(self, cookie_str: str) -> Optional[dict]:
        session = requests.Session()

        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" not in part:
                continue
            key, _, val = part.partition("=")
            try:
                val.encode("latin-1")
            except UnicodeEncodeError:
                continue
            session.cookies.set(key.strip(), val.strip(), domain=".volcengine.com")

        headers = {
            "Content-Type": "application/json",
            "Origin": "https://console.volcengine.com",
            "Referer": "https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:151.0) Gecko/20100101 Firefox/151.0",
        }

        for cookie in session.cookies:
            if cookie.name == "csrfToken":
                headers["X-Csrf-Token"] = cookie.value
                break

        resp = session.post(VOLC_API, headers=headers, json={}, timeout=15)

        if resp.status_code == 200:
            return resp.json()

        csrf_token = resp.headers.get("X-Need-Token")
        if csrf_token:
            headers["X-Csrf-Token"] = csrf_token
            session.cookies.set("csrfToken", csrf_token, domain=".volcengine.com")
            resp = session.post(VOLC_API, headers=headers, json={}, timeout=15)
            if resp.status_code == 200:
                return resp.json()

        return None
