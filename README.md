# VPS 到期提醒 Telegram Bot

一个简单的 Telegram Bot，用于管理和提醒 VPS 到期时间。

## 功能

- 📋 VPS 列表 — 按商家分组，颜色标记到期状态
- ➕ 添加 / ✏️ 编辑 / 🗑 删除 VPS
- 📡 Ping 全部 — 批量检测 VPS 在线状态
- 🔔 每日自动提醒 — 每天 09:00 检查到期推送
- ⚙️ 自定义提醒天数（1/3/7/14/30 天可选）
- 📅 日期简写支持（`0315` → `2026-03-15`）

## 安装

```bash
git clone https://github.com/mango082888-bit/vps-reminder.git
cd vps-reminder
chmod +x install.sh
./install.sh
```

## 配置

复制 `.env.example` 为 `.env`，填入你的 Bot Token 和 Telegram ID：

```bash
cp .env.example .env
```

```
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
```

## 使用

```bash
python3 bot.py
```

或使用 systemd 服务：

```bash
systemctl start vps-reminder
systemctl enable vps-reminder
```

## 截图

发送 `/start` 即可使用，全部通过 Inline 按钮操作。

## License

MIT
