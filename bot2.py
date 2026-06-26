# ==================== BOT2: Ikkinchi Bot ====================
import os
import time
import threading
import requests
import telebot
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==================== TOKEN & SETTINGS ====================
TOKEN = os.getenv("BOT2_TOKEN")
BOT_USERNAME = os.getenv("BOT2_USERNAME")
ADMIN_ID = 7797502113  # o'z admin ID'ingizni qo'ying
PORT = 10001  # Bot1 10000, Bot2 10001

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ==================== FLASK SERVER ====================
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
    while True:
        try:
            requests.get(f"https://yuklovchi-bot-5kne.onrender.com")
        except:
            pass
        time.sleep(60)

threading.Thread(target=keep_alive, daemon=True).start()

# ==================== BOT HANDLERLARI ====================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, f"Salom! Men {BOT_USERNAME} botman! 👋")

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "Bu yordam xabari.")

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.reply_to(message, f"Siz yozdingiz: {message.text}")

# ==================== RUN ====================
def start_bot():
    print(f"✅ {BOT_USERNAME} port {PORT} da ishga tushmoqda...")
    app.run(host="0.0.0.0", port=PORT)
