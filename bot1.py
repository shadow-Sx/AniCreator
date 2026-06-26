# ==================== BOT1: XAnimelar Bot ====================
import os
import time
import random
import string
import threading
import requests
import telebot
from flask import Flask, request
from telebot.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from pymongo import MongoClient
from bson.objectid import ObjectId

import functions

# ==================== TOKEN & SETTINGS ====================
TOKEN = os.getenv("BOT1_TOKEN")  # Environment o'zgaruvchi nomi o'zgardi
BOT_USERNAME = os.getenv("BOT1_USERNAME")  # Environment o'zgaruvchi nomi o'zgardi
ADMIN_ID = 7797502113
PORT = 10000  # Har bir bot uchun alohida port (10000, 10001, 10002...)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
functions.set_bot_username(BOT_USERNAME)

# ==================== MONGO DB CONNECTION ====================
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

# Har bir bot o'z database'iga ega bo'lishi mumkin (yoki bir xil ham ishlaydi)
db = client["xanimelar_bot"]  # Bu botning o'z DB si
contents = db["contents"]
required_channels_collection = db["required_channels"]
optional_channels_collection = db["optional_channels"]
users_collection = db["users"]
referrals_collection = db["referrals"]
user_referrals_collection = db["user_referrals"]
bot_settings_collection = db["bot_settings"]
required_bots_collection = db["required_bots"]
join_requests_collection = db["join_requests"]
ads_collection = db["ads"]

# ==================== FLASK SERVER (har bir bot uchun alohida) ====================
app = Flask(__name__)

@app.route('/')
def home():
    return f"{BOT_USERNAME} is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    json_data = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "OK", 200

def keep_alive():
    """Bot o'zini o'zi uyg'otib turadi (kerak bo'lsa boshqa botni ham uyg'otishi mumkin)"""
    while True:
        try:
            requests.get(f"https://yuklovchi-bot-5kne.onrender.com")
        except:
            pass
        time.sleep(60)

threading.Thread(target=keep_alive, daemon=True).start()

# ... (QOLGAN HAMMA KOD SHU YERDA – o'zgartirishsiz) ...

# Faqat eng pastki qismini o'zgartiramiz:

# ==================== RUN SERVER ====================
def start_bot():
    """Botni ishga tushirish (main.py chaqiradi)"""
    print(f"✅ {BOT_USERNAME} port {PORT} da ishga tushmoqda...")
    app.run(host="0.0.0.0", port=PORT)
