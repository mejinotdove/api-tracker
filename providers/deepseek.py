from datetime import date
from typing import Optional

import requests

from .base import BaseProvider, UsageInfo, Item

CALL_API_TIMEOUT = 10

PLATFORM_BASE = "https://platform.deepseek.com"
SUMMARY_ENDPOINT = "/api/v0/users/get_user_summary"
COST_ENDPOINT = "/api/v0/usage/cost"

def get_request_header(bearer: str) -> dict:
    """根据传入的 bearer token 生成并返回请求头字典。"""
    return {
        "Authorization": bearer,
        "Origin": "https://platform.deepseek.com",
        "Referer": "https://platform.deepseek.com/usage",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    }


class DeepSeekProvider(BaseProvider):
    def get_usage(self) -> UsageInfo:
        platform_token = self.config.get("platform_token", "")
        if not platform_token:
            return UsageInfo(0, 0, error="platform_token not configured")

        data = self._fetch_summary(platform_token)
        if data is None:
            return UsageInfo(0, 0, error="failed to fetch user summary")

        biz_data = data.get("data", {}).get("biz_data", {})

        balance = float(biz_data.get("normal_wallets", [{}])[0].get("balance", 0))
        monthly_cost = float(biz_data.get("monthly_costs", [{}])[0].get("amount", 0))

        today_cost = self._fetch_today_cost(platform_token)

        items = [
            Item(name="帐户余额", used=0, total=balance, unit="￥"),
            Item(name="本月消费", used=monthly_cost, total=0, unit="￥"),
        ]
        if today_cost is not None:
            items.append(Item(name="今日消费", used=today_cost, total=0, unit="￥"))

        return UsageInfo(
            balance=balance,
            total=balance,
            today_usage=monthly_cost,
            currency="CNY",
            items=items,
        )

    def _fetch_summary(self, platform_token: str) -> Optional[dict]:
        bearer = platform_token
        if not bearer.startswith("Bearer "):
            bearer = f"Bearer {bearer}"
        try:
            resp = requests.get(
                f"{PLATFORM_BASE}{SUMMARY_ENDPOINT}",
                headers=get_request_header(bearer),
                timeout=CALL_API_TIMEOUT
            )
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError):
            return None

    def _fetch_today_cost(self, platform_token: str) -> Optional[float]:
        bearer = platform_token
        if not bearer.startswith("Bearer "):
            bearer = f"Bearer {bearer}"
        today = date.today()
        try:
            resp = requests.get(
                f"{PLATFORM_BASE}{COST_ENDPOINT}",
                params={"month": str(today.month), "year": str(today.year)},
                headers=get_request_header(bearer),
                timeout=CALL_API_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError):
            return None

        biz_data = data.get("data", {}).get("biz_data", [{}])
        first = biz_data[0] if isinstance(biz_data, list) and biz_data else {}
        days = first.get("days", [])
        today_str = today.isoformat()
        today_entry = next((d for d in days if d.get("date") == today_str), None)
        if not today_entry:
            return 0.0

        total = 0.0
        for entry in today_entry.get("data", []):
            for u in entry.get("usage", []):
                t = u.get("type", "")
                if t in ("PROMPT_CACHE_HIT_TOKEN", "PROMPT_CACHE_MISS_TOKEN", "RESPONSE_TOKEN"):
                    total += float(u.get("amount", 0))
        return round(total, 4)
