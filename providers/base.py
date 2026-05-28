from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Optional


@dataclass
class Item:
    name: str
    used: float
    total: float
    unit: str
    note: str = ""
    level: str = ""


@dataclass
class ModelUsage:
    name: str
    cost: float
    requests: int
    input_cached: int = 0
    input_uncached: int = 0
    output: int = 0


@dataclass
class UsageInfo:
    balance: float
    total: float
    today_usage: float = 0
    currency: str = "CNY"
    items: list[Item] = field(default_factory=list)
    models: list[ModelUsage] = field(default_factory=list)
    error: Optional[str] = None


class BaseProvider(ABC):
    def __init__(self, config: dict) -> None:
        self.config = config

    @property
    def display_name(self) -> str:
        return self.config.get("display_name", "?")

    @abstractmethod
    def get_usage(self) -> UsageInfo:
        ...