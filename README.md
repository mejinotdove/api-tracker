# API Tracker

A [Waybar](https://github.com/Alexays/Waybar) custom module that tracks API usage and quota for AI providers, displaying real-time balance and consumption on your status bar.

## Features

- **DeepSeek** – account balance, monthly/today costs via platform API
- **Volcengine (ARK)** – Coding Plan quota usage (session / weekly / monthly) with remaining time display
- Displays as emoji or short label in Waybar
- Tooltip with detailed breakdown of each provider
- Color-coded status: `normal`, `warning` (error), `critical` (low balance)

## Screenshot

```
🐬 ￥88.88  🌋 12.3%/45.6%/78.9%
```

## Requirements

- Python 3.11+
- Waybar (for displaying the module)

## Installation

### 1. Clone the repository

```bash
git clone git@github.com:mejinotdove/api-tracker.git ~/.config/waybar/scripts/api-tracker
```

### 2. Set up venv and install dependencies

```bash
cd ~/.config/waybar/scripts/api-tracker
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium  # only needed for Volcengine auto-login
```

### 3. Configure credentials

```bash
cp config.toml.example config.toml
```

Edit `config.toml` and fill in your credentials:

#### DeepSeek

1. Go to [platform.deepseek.com](https://platform.deepseek.com/usage)
2. Open browser DevTools → Network tab
3. Find any request to `platform.deepseek.com`
4. Copy the full `Authorization` header value (e.g. `Bearer xxx...`)
5. Set it as `platform_token` in the config

#### Volcengine

**Option A: Manual cookie**

1. Log in to [Volcengine ARK console](https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement)
2. Open browser DevTools → Network tab
3. Find any request to `console.volcengine.com` and copy the `Cookie` header
4. Save it to `~/.config/waybar/scripts/api-tracker/.volcengine_cookie`

**Option B: Auto-login (requires playwright)**

Set `auto_login_username` and `auto_login_password` in `config.toml` (or via env vars `VOLCENGINE_USERNAME` / `VOLCENGINE_PASSWORD`). The cookie will be fetched and refreshed automatically.

### 4. Add to Waybar config

Add the following block to your Waybar config (`~/.config/waybar/config.jsonc`):

```jsonc
"custom/api-tracker": {
    "exec": "~/.config/waybar/scripts/api-tracker/.venv/bin/python ~/.config/waybar/scripts/api-tracker/main.py 2>/dev/null",
    "interval": 30,
    "return-type": "json",
    "format": "{}",
    "max-length": 100
}
```

## Configuration

| Key | Description | Default |
|-----|-------------|---------|
| `general.interval` | Polling interval (seconds) | `30` |
| `providers.<name>.enabled` | Enable/disable provider | `true` |
| `providers.<name>.display_name` | Label shown in Waybar | emoji |
| `providers.deepseek.platform_token` | Bearer token for DeepSeek API | — |
| `providers.volcengine.cookie_file` | Path to cookie file | `~/.config/waybar/.../cookie` |

## Provider Development

Implement your own provider by extending `BaseProvider` in `providers/`:

```python
from providers.base import BaseProvider, UsageInfo

class MyProvider(BaseProvider):
    def get_usage(self) -> UsageInfo:
        # return UsageInfo(...)
```

Then register it in `main.py`:

```python
PROVIDER_MAP = {
    "my_provider": "providers.my_provider.MyProvider",
}
```

## License

GNU General Public License v3.0