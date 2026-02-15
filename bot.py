#!/usr/bin/env python3
"""VPS 到期提醒 Telegram Bot"""

import os, json, subprocess
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN = int(os.getenv("ADMIN_ID", "0"))
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

def load_data():
    try:
        with open(DATA_FILE) as f: return json.load(f)
    except: return {"vps": [], "remind_days": [1, 3, 7]}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def parse_date(text):
    """解析日期简写: 0315 -> 2026-03-15, 3-15 -> 2026-03-15"""
    text = text.strip().replace("/", "-").replace(".", "-")
    year = datetime.now().year
    if len(text) == 4 and text.isdigit():
        return f"{year}-{text[:2]}-{text[2:]}"
    if len(text) in [3,4] and "-" in text:
        parts = text.split("-")
        return f"{year}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
    if len(text) == 10:
        return text
    return text

def days_left(d):
    return (datetime.strptime(d, "%Y-%m-%d") - datetime.now()).days

def ping_host(ip):
    try:
        r = subprocess.run(["ping", "-c", "1", "-W", "2", ip], capture_output=True, timeout=5)
        return r.returncode == 0
    except: return False

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 VPS列表", callback_data="list")],
        [InlineKeyboardButton("➕ 添加", callback_data="add"), InlineKeyboardButton("✏️ 编辑", callback_data="edit"), InlineKeyboardButton("🗑 删除", callback_data="del")],
        [InlineKeyboardButton("📡 Ping全部", callback_data="ping"), InlineKeyboardButton("🔔 测试", callback_data="test"), InlineKeyboardButton("⚙️ 设置", callback_data="settings")]
    ])

def back_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回", callback_data="back")]])

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🖥 *VPS 到期提醒*", parse_mode="Markdown", reply_markup=main_kb())

async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    
    if data == "back":
        await q.edit_message_text("🖥 *VPS 到期提醒*", parse_mode="Markdown", reply_markup=main_kb())
    
    elif data == "list":
        d = load_data()
        vps = d.get("vps", [])
        if not vps:
            await q.edit_message_text("📭 暂无VPS", reply_markup=back_kb())
            return
        groups = {}
        for v in vps:
            p = v.get("provider", "未知")
            if p not in groups: groups[p] = []
            groups[p].append(v)
        msg = "📋 *VPS 列表*\n"
        for provider, items in groups.items():
            msg += f"\n🏢 *{provider}*\n"
            for v in sorted(items, key=lambda x: days_left(x["date"])):
                dl = days_left(v["date"])
                if dl < 0:
                    icon, dl_text = "⚫", f"已过期{-dl}天"
                elif dl <= 3:
                    icon, dl_text = "🔴", f"{dl}天"
                elif dl <= 7:
                    icon, dl_text = "🟡", f"{dl}天"
                else:
                    icon, dl_text = "🟢", f"{dl}天"
                msg += f"{icon} {v['name']} - {v['date']} ({dl_text})\n"
        await q.edit_message_text(msg, parse_mode="Markdown", reply_markup=back_kb())
    
    elif data == "settings":
        d = load_data()
        days = d.get("remind_days", [1, 3, 7])
        kb = [[InlineKeyboardButton(f"{'✅' if i in days else '⬜'} {i}天", callback_data=f"toggle_{i}") for i in [1, 3, 7]],
              [InlineKeyboardButton(f"{'✅' if i in days else '⬜'} {i}天", callback_data=f"toggle_{i}") for i in [14, 30]],
              [InlineKeyboardButton("🔙 返回", callback_data="back")]]
        await q.edit_message_text(f"⚙️ 提醒天数设置\n当前: {days}", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data.startswith("toggle_"):
        day = int(data.split("_")[1])
        d = load_data()
        days = d.get("remind_days", [1, 3, 7])
        if day in days: days.remove(day)
        else: days.append(day)
        days.sort()
        d["remind_days"] = days
        save_data(d)
        kb = [[InlineKeyboardButton(f"{'✅' if i in days else '⬜'} {i}天", callback_data=f"toggle_{i}") for i in [1, 3, 7]],
              [InlineKeyboardButton(f"{'✅' if i in days else '⬜'} {i}天", callback_data=f"toggle_{i}") for i in [14, 30]],
              [InlineKeyboardButton("🔙 返回", callback_data="back")]]
        await q.edit_message_text(f"⚙️ 提醒天数设置\n当前: {days}", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "edit":
        d = load_data()
        vps = d.get("vps", [])
        if not vps:
            await q.edit_message_text("📭 暂无VPS", reply_markup=back_kb())
            return
        kb = [[InlineKeyboardButton(f"✏️ {v['name']}", callback_data=f"editvps_{i}")] for i, v in enumerate(vps)]
        kb.append([InlineKeyboardButton("🔙 返回", callback_data="back")])
        await q.edit_message_text("选择要编辑的VPS:", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data.startswith("editvps_"):
        idx = int(data.split("_")[1])
        ctx.user_data["edit_idx"] = idx
        d = load_data()
        v = d["vps"][idx]
        kb = [
            [InlineKeyboardButton("📝 名称", callback_data="ed_name"), InlineKeyboardButton("🏢 商家", callback_data="ed_provider")],
            [InlineKeyboardButton("🌐 IP", callback_data="ed_ip"), InlineKeyboardButton("📅 日期", callback_data="ed_date")],
            [InlineKeyboardButton("💰 价格", callback_data="ed_price"), InlineKeyboardButton("🔄 周期", callback_data="ed_cycle")],
            [InlineKeyboardButton("🔙 返回", callback_data="edit")]
        ]
        msg = f"✏️ 编辑 *{v['name']}*\n\n"
        msg += f"🏢 商家: {v.get('provider','')}\n"
        msg += f"🌐 IP: {v.get('ip','无')}\n"
        msg += f"📅 日期: {v.get('date','')}\n"
        msg += f"💰 价格: {v.get('price','无')}\n"
        msg += f"🔄 周期: {v.get('cycle','')}"
        await q.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data.startswith("ed_"):
        field = data.split("_")[1]
        ctx.user_data["edit_field"] = field
        names = {"name":"名称","provider":"商家","ip":"IP","date":"日期","price":"价格","cycle":"周期"}
        await q.edit_message_text(f"请输入新的{names.get(field,field)}:")
    
    elif data == "del":
        d = load_data()
        vps = d.get("vps", [])
        if not vps:
            await q.edit_message_text("📭 暂无VPS", reply_markup=back_kb())
            return
        kb = [[InlineKeyboardButton(f"🗑 {v['name']}", callback_data=f"delvps_{i}")] for i, v in enumerate(vps)]
        kb.append([InlineKeyboardButton("🔙 返回", callback_data="back")])
        await q.edit_message_text("选择要删除的VPS:", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data.startswith("delvps_"):
        idx = int(data.split("_")[1])
        d = load_data()
        if 0 <= idx < len(d["vps"]):
            removed = d["vps"].pop(idx)
            save_data(d)
            await q.edit_message_text(f"✅ 已删除: {removed['name']}", reply_markup=back_kb())
    
    elif data == "test":
        d = load_data()
        vps = d.get("vps", [])
        if not vps:
            await q.edit_message_text("📭 暂无VPS可测试", reply_markup=back_kb())
            return
        v = min(vps, key=lambda x: days_left(x["date"]))
        dl = days_left(v["date"])
        msg = f"🔔 *测试提醒*\n\n{v['name']} ({v['provider']})\n📅 {v['date']} (还剩 {dl} 天)"
        await q.message.reply_text(msg, parse_mode="Markdown")
        await q.edit_message_text("✅ 测试提醒已发送", reply_markup=back_kb())
    
    elif data == "ping":
        d = load_data()
        vps = [v for v in d.get("vps", []) if v.get("ip")]
        if not vps:
            await q.edit_message_text("📭 没有可ping的VPS", reply_markup=back_kb())
            return
        await q.edit_message_text("📡 正在检测...")
        msg = "📡 *Ping 结果*\n\n"
        for v in vps:
            ok = ping_host(v["ip"])
            msg += f"{'🟢' if ok else '🔴'} {v['name']} - `{v['ip']}`\n"
        await q.edit_message_text(msg, parse_mode="Markdown", reply_markup=back_kb())
    
    elif data == "add":
        ctx.user_data["step"] = "name"
        await q.edit_message_text("📝 请输入 VPS 名称:")

async def handle_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    step = ctx.user_data.get("step")
    text = update.message.text.strip()
    
    # 编辑模式
    if ctx.user_data.get("edit_field"):
        idx = ctx.user_data.get("edit_idx", 0)
        field = ctx.user_data["edit_field"]
        d = load_data()
        if field == "date":
            text = parse_date(text)
        d["vps"][idx][field] = text
        save_data(d)
        ctx.user_data.clear()
        await update.message.reply_text("✅ 已更新", reply_markup=main_kb())
        return
    
    if step == "name":
        ctx.user_data["name"] = text
        ctx.user_data["step"] = "provider"
        await update.message.reply_text("🏢 请输入商家名称:")
    elif step == "provider":
        ctx.user_data["provider"] = text
        ctx.user_data["step"] = "ip"
        await update.message.reply_text("🌐 请输入 IP (没有输入 0):")
    elif step == "ip":
        ctx.user_data["ip"] = None if text == "0" else text
        ctx.user_data["step"] = "cycle"
        await update.message.reply_text("🔄 付款周期 (月/季/年):")
    elif step == "cycle":
        ctx.user_data["cycle"] = text
        ctx.user_data["step"] = "date"
        await update.message.reply_text("📅 到期日期 (YYYY-MM-DD):")
    elif step == "date":
        ctx.user_data["date"] = text
        ctx.user_data["step"] = "price"
        await update.message.reply_text("💰 价格 (如 /月，没有输入 0):")
    elif step == "price":
        ctx.user_data["price"] = None if text == "0" else text
        d = load_data()
        d["vps"].append({
            "name": ctx.user_data["name"],
            "provider": ctx.user_data["provider"],
            "ip": ctx.user_data["ip"],
            "cycle": ctx.user_data["cycle"],
            "date": ctx.user_data["date"],
            "price": ctx.user_data["price"]
        })
        save_data(d)
        ctx.user_data.clear()
        await update.message.reply_text(f"✅ 已添加: {ctx.user_data.get('name', 'VPS')}", reply_markup=main_kb())

async def check_expire(ctx: ContextTypes.DEFAULT_TYPE):
    d = load_data()
    remind_days = d.get("remind_days", [1, 3, 7])
    for v in d.get("vps", []):
        dl = days_left(v["date"])
        if dl in remind_days:
            msg = f"⏰ *到期提醒*\n\n{v['name']} ({v['provider']})\n📅 {v['date']} (还剩 {dl} 天)"
            await ctx.bot.send_message(ADMIN, msg, parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.job_queue.run_daily(check_expire, time=datetime.strptime("09:00", "%H:%M").time())
    print("Bot 启动")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
