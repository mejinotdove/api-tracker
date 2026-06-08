# API Tracker

一个 [Waybar](https://github.com/Alexays/Waybar) 自定义模块，用于追踪 AI 提供商的 API 使用额度和余额，在状态栏实时显示。

## 功能

- **DeepSeek** – 通过平台 API 获取账户余额、本月/今日消费
- **Volcengine（火山引擎 ARK）** – 获取 Coding Plan 配额使用率（会话级 / 周级 / 月级），并显示剩余刷新时间
- 在 Waybar 中以 emoji 或短标签显示
- 鼠标悬停提示框展示详细数据
- 状态颜色：`normal`（正常）、`warning`（错误）、`critical`（余额不足）

## 截图

```
🐬 ￥88.88  🌋 12.3%/45.6%/78.9%
```

## 环境要求

- Python 3.11+
- Waybar（用于显示模块）

## 安装

### 1. 克隆仓库

```bash
git clone git@github.com:mejinotdove/api-tracker.git ~/.config/waybar/scripts/api-tracker
```

### 2. 创建 venv 并安装依赖

```bash
cd ~/.config/waybar/scripts/api-tracker
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium  # 仅火山引擎自动登录需要
```

### 3. 配置凭据

```bash
cp config.toml.example config.toml
```

编辑 `config.toml`，填入你的凭据：

#### DeepSeek

1. 访问 [platform.deepseek.com](https://platform.deepseek.com/usage)
2. 打开浏览器开发者工具 → Network 标签
3. 找到任意发往 `platform.deepseek.com` 的请求
4. 复制完整的 `Authorization` 请求头值（如 `Bearer xxx...`）
5. 填入配置中的 `platform_token` 字段

#### 火山引擎

**方式 A：手动获取 Cookie**

1. 登录[火山引擎 ARK 控制台](https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement)
2. 打开浏览器开发者工具 → Network 标签
3. 找到任意发往 `console.volcengine.com` 的请求，复制 `Cookie` 请求头
4. 保存到 `~/.config/waybar/scripts/api-tracker/.volcengine_cookie`

**方式 B：自动登录（需要 playwright）**

在 `config.toml` 中设置 `auto_login_username` 和 `auto_login_password`（也可通过环境变量 `VOLCENGINE_USERNAME` / `VOLCENGINE_PASSWORD` 传入），cookie 将自动获取并刷新。

### 4. 添加到 Waybar 配置

在 Waybar 配置文件（`~/.config/waybar/config.jsonc`）中添加：

```jsonc
"custom/api-tracker": {
    "exec": "~/.config/waybar/scripts/api-tracker/.venv/bin/python ~/.config/waybar/scripts/api-tracker/main.py 2>/dev/null",
    "interval": 30,
    "return-type": "json",
    "format": "{}",
    "max-length": 100
}
```

## 配置项

| 键 | 说明 | 默认值 |
|-----|------|--------|
| `general.interval` | 轮询间隔（秒） | `30` |
| `providers.<name>.enabled` | 启用/禁用提供商 | `true` |
| `providers.<name>.display_name` | 在 Waybar 中显示的标签 | emoji |
| `providers.deepseek.platform_token` | DeepSeek API 的 Bearer token | — |
| `providers.volcengine.cookie_file` | Cookie 文件路径 | `~/.config/waybar/.../cookie` |

## 开发自定义 Provider

继承 `BaseProvider` 即可实现自己的提供商：

```python
from providers.base import BaseProvider, UsageInfo

class MyProvider(BaseProvider):
    def get_usage(self) -> UsageInfo:
        # return UsageInfo(...)
```

然后在 `main.py` 中注册：

```python
PROVIDER_MAP = {
    "my_provider": "providers.my_provider.MyProvider",
}
```

## 许可证

GNU General Public License v3.0