# VPS 到期提醒 Bot

Telegram Bot，用于管理 VPS 到期提醒。

## 功能

- 📋 VPS 列表管理
- ⏰ 自动到期提醒（1/3/7/14/30天）
- 📡 批量 Ping 检测
- ⚙️ 自定义提醒天数

## 安装

```bash
# 克隆
git clone https://github.com/mango082888-bit/vps-reminder.git
cd vps-reminder

# 安装依赖
pip install python-telegram-bot python-dotenv

# 配置
cp .env.example .env
# 编辑 .env 填入 BOT_TOKEN 和 ADMIN_ID

# 运行
python bot.py
```

## Systemd 服务

```bash
cat > /etc/systemd/system/vps-reminder.service << EOF
[Unit]
Description=VPS Reminder Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/vps-reminder
ExecStart=/opt/vps-reminder/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable --now vps-reminder
```
