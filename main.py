from importlib import import_module
from pathlib import Path
from typing import Optional
import html
import json
import tomllib

from providers.base import BaseProvider, UsageInfo


CONFIG_PATH = Path.home() / ".config" / "waybar" / "scripts" / "api-tracker" / "config.toml"

PROVIDER_MAP: dict[str, str] = {
    "deepseek": "providers.deepseek.DeepSeekProvider",
    "volcengine": "providers.volcengine.VolcengineProvider",
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        UsageInfo(0, 0, error=f"config not found: {CONFIG_PATH}")
        return {}

    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def build_provider(name: str, cfg: dict) -> Optional[BaseProvider]:
    module_path = PROVIDER_MAP.get(name)
    if not module_path:
        return None

    mod_name, cls_name = module_path.rsplit(".", 1)
    try:
        mod = import_module(mod_name)
    except ImportError:
        return None

    cls = getattr(mod, cls_name)
    return cls(cfg)


def format_text(entries: list[tuple[str, UsageInfo]]) -> str:
    if not entries:
        return "no providers enabled"

    parts: list[str] = []
    for name, info in entries:
        label = name
        if info.error:
            parts.append(f"{label}:err")
        else:
            if info.currency == "%":
                item_parts = [f"{item.used:g}%" for item in info.items]
                parts.append(f"{label}:{'/'.join(item_parts)}")
            else:
                parts.append(f"{label}:\u00a5{info.balance:.2f}")
    return " ".join(parts)


def format_tooltip(entries: list[tuple[str, UsageInfo]]) -> str:
    lines: list[str] = []
    for name, info in entries:
        lines.append(f"--- {name} ---")
        if info.error:
            lines.append(f"\u26a0 ERR: {info.error}")
        else:
            if info.currency == "%":
                if info.items:
                    for item in info.items:
                        line = f"  {item.name}: {item.used:5.1f}%"
                        if item.note:
                            line += f" | {item.note}"
                        lines.append(line)
            else:
                if info.items:
                    for item in info.items:
                        if item.unit == "￥":
                            lines.append(f"  {item.name}:\t￥{item.used if item.used else item.total:.2f}")
                        else:
                            val = item.total if item.total else item.used
                            lines.append(f"  {item.name}:\t{val:,}")
        lines.append("")
    return "\n".join(lines).strip()


def main() -> None:
    cfg = load_config()
    providers_cfg = cfg.get("providers", {})

    entries: list[tuple[str, UsageInfo]] = []
    for pname, pcfg in providers_cfg.items():
        if not pcfg.get("enabled", False):
            continue
        provider = build_provider(pname, pcfg)
        if provider is None:
            continue
        info = provider.get_usage()
        entries.append((pcfg.get("display_name", pname), info))

    text = format_text(entries)
    tooltip = format_tooltip(entries)

    css_class = "normal"
    for _, info in entries:
        if info.error:
            css_class = "warning"
        elif info.balance < 1.0 and not info.error:
            css_class = "critical"

    output = {
        "text": text,
        "tooltip": html.escape(tooltip),
        "class": css_class,
    }
    print(json.dumps(output), flush=True)


if __name__ == "__main__":
    main()
