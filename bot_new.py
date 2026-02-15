#!/usr/bin/env python3
"""VPS 到期提醒 Telegram Bot"""

import os, json, subprocess
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
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
    text = text.strip().replace("/", "-").replace(".", "-")
    year = datetime.now().year
    if len(text) == 4 and text.isdigit():
        return f"{year}-{text[:2]}-{text[2:]}"
    if "-" in text and len(text) <= 5:
        parts = text.split("-")
        return f"{year}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
    return text

def days_left(d):
    return (datetime.strptime(d, "%Y-%m-%d") - datetime.now()).days

def ping_host(ip):
    try:
        r = subprocess.run(["ping", "-c", "1", "-W", "2", ip], capture_output=True, timeout=5)
        return r.returncode == 0
    except: return False
