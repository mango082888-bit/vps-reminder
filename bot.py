#!/usr/bin/env python3
"""VPS 到期提醒 Telegram Bot"""

import os, json, asyncio, subprocess
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN = int(os.getenv("ADMIN_ID", "0"))
DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE) as f: return json.load(f)
    except: return {"vps": [], "remind_days": [1, 3, 7]}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def days_left(d):
    return (datetime.strptime(d, "%Y-%m-%d") - datetime.now()).days

def ping_host(ip):
    try:
        r = subprocess.run(["ping", "-c", "1", "-W", "2", ip], capture_output=True, timeout=5)
        return r.returncode == 0
    except: return False

# 主菜单
async def start(update: Update, ctx):
    kb = [[InlineKeyboardButton("📋 VPS列表", callback_data="list")],
          [InlineKeyboardButton("➕ 添加", callback_data="add"), InlineKeyboardButton("🗑 删除", callback_data="del")],
          [InlineKeyboardButton("📡 Ping全部", callback_data="ping"), InlineKeyboardButton("⚙️ 设置", callback_data="settings")]]
    await update.message.reply_text("🖥 *VPS 到期提醒*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def back_main(u, c):
    kb = [[InlineKeyboardButton("📋 VPS列表", callback_data="list")],
          [InlineKeyboardButton("➕ 添加", callback_data="add"), InlineKeyboardButton("🗑 删除", callback_data="del")],
          [InlineKeyboardButton("📡 Ping全部", callback_data="ping"), InlineKeyboardButton("⚙️ 设置", callback_data="settings")]]
    await u.callback_query.edit_message_text("🖥 *VPS 到期提醒*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

# 设置菜单
async def settings_menu(u, c):
    data = load_data()
    days = data.get("remind_days", [1, 3, 7])
    kb = [[InlineKeyboardButton(f"{'✅' if d in days else '⬜'} {d}天", callback_data=f"toggle_{d}") for d in [1, 3, 7]],
          [InlineKeyboardButton(f"{'✅' if d in days else '⬜'} {d}天", callback_data=f"toggle_{d}") for d in [14, 30]],
          [InlineKeyboardButton("🔙 返回", callback_data="back")]]
    await u.callback_query.edit_message_text(f"⚙️ 提醒天数设置\n当前: {days}", reply_markup=InlineKeyboardMarkup(kb))

async def toggle_day(u, c):
    day = int(u.callback_query.data.split("_")[1])
    data = load_data()
    days = data.get("remind_days", [1, 3, 7])
    if day in days: days.remove(day)
    else: days.append(day)
    days.sort()
    data["remind_days"] = days
    save_data(data)
    await settings_menu(u, c)

# VPS 列表
async def show_list(u, c):
    data = load_data()
    vps_list = data.get("vps", [])
    if not vps_list:
        await u.callback_query.edit_message_text("📭 暂无VPS", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回", callback_data="back")]]))
        return
    msg = "📋 *VPS 列表*\n\n"
    for v in sorted(vps_list, key=lambda x: days_left(x['expire'])):
        d = days_left(v['expire'])
        icon = "🔴" if d <= 3 else "🟡" if d <= 7 else "🟢"
        msg += f"{icon} *{v['name']}* ({v['provider']})\n"
        msg += f"   📅 {v['expire']} ({d}天)\n"
        if v.get('ip'): msg += f"   🌐 `{v['ip']}`\n"
        if v.get('price'): msg += f"   💰 {v['price']}\n"
        msg += "\n"
    await u.callback_query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回", callback_data="back")]]))

# 添加 VPS 会话
NAME, PROVIDER, IP, CYCLE, EXPIRE, PRICE = range(6)

async def add_start(u, c):
    await u.callback_query.edit_message_text("📝 请输入 VPS 名称:")
    return NAME

async def add_name(u, c):
    c.user_data['name'] = u.message.text
    await u.message.reply_text("🏢 请输入商家名称:")
    return PROVIDER

async def add_provider(u, c):
    c.user_data['provider'] = u.message.text
    await u.message.reply_text("🌐 请输入 IP (没有输入 0):")
    return IP

async def add_ip(u, c):
    ip = u.message.text
    c.user_data['ip'] = None if ip == "0" else ip
    await u.message.reply_text("🔄 付款周期 (月/季/年):")
    return CYCLE

async def add_cycle(u, c):
    c.user_data['cycle'] = u.message.text
    await u.message.reply_text("📅 到期日期 (YYYY-MM-DD):")
    return EXPIRE

async def add_date(u, c):
    c.user_data['expire'] = u.message.text
    await u.message.reply_text("💰 价格 (如 $5/月，没有输入 0):")
    return PRICE

async def add_price(u, c):
    price = u.message.text
    c.user_data['price'] = None if price == "0" else price
    data = load_data()
    data['vps'].append({
        'name': c.user_data['name'],
        'provider': c.user_data['provider'],
        'ip': c.user_data['ip'],
        'cycle': c.user_data['cycle'],
        'expire': c.user_data['expire'],
        'price': c.user_data['price']
    })
    save_data(data)
    await u.message.reply_text(f"✅ 已添加: {c.user_data['name']}")
    return ConversationHandler.END

# 删除 VPS
async def vps_del_start(u, c):
    data = load_data()
    vps_list = data.get("vps", [])
    if not vps_list:
        await u.callback_query.edit_message_text("📭 暂无VPS")
        return
    kb = [[InlineKeyboardButton(f"🗑 {v['name']}", callback_data=f"delvps_{i}")] for i, v in enumerate(vps_list)]
    kb.append([InlineKeyboardButton("🔙 返回", callback_data="back")])
    await u.callback_query.edit_message_text("选择要删除的VPS:", reply_markup=InlineKeyboardMarkup(kb))

async def vps_del_confirm(u, c):
    idx = int(u.callback_query.data.split("_")[1])
    data = load_data()
    if 0 <= idx < len(data['vps']):
        removed = data['vps'].pop(idx)
        save_data(data)
        await u.callback_query.edit_message_text(f"✅ 已删除: {removed['name']}", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回", callback_data="back")]]))

# Ping 全部
async def ping_all(u, c):
    data = load_data()
    vps_list = [v for v in data.get("vps", []) if v.get('ip')]
    if not vps_list:
        await u.callback_query.edit_message_text("📭 没有可ping的VPS")
        return
    await u.callback_query.edit_message_text("📡 正在检测...")
    msg = "📡 *Ping 结果*\n\n"
    for v in vps_list:
        ok = ping_host(v['ip'])
        msg += f"{'🟢' if ok else '🔴'} {v['name']} - `{v['ip']}`\n"
    await u.callback_query.edit_message_text(msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回", callback_data="back")]]))

# 定时检查到期
async def check_expire(ctx):
    data = load_data()
    remind_days = data.get("remind_days", [1, 3, 7])
    for v in data.get("vps", []):
        d = days_left(v['expire'])
        if d in remind_days:
            await ctx.bot.send_message(ADMIN, f"⏰ *到期提醒*\n\n{v['name']} ({v['provider']})\n📅 {v['expire']} (还剩 {d} 天)", parse_mode="Markdown")

async def cancel(u, c):
    await u.message.reply_text("已取消")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    
    # 添加VPS会话
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_start, pattern="^add$")],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            PROVIDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_provider)],
            IP: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_ip)],
            CYCLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_cycle)],
            EXPIRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_date)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(add_conv)
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back$"))
    app.add_handler(CallbackQueryHandler(settings_menu, pattern="^settings$"))
    app.add_handler(CallbackQueryHandler(toggle_day, pattern="^toggle_"))
    app.add_handler(CallbackQueryHandler(show_list, pattern="^list$"))
    app.add_handler(CallbackQueryHandler(vps_del_start, pattern="^del$"))
    app.add_handler(CallbackQueryHandler(vps_del_confirm, pattern="^delvps_"))
    app.add_handler(CallbackQueryHandler(ping_all, pattern="^ping$"))
    
    # 每天早上9点检查
    app.job_queue.run_daily(check_expire, time=datetime.strptime("09:00", "%H:%M").time())
    
    print("Bot 启动")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
