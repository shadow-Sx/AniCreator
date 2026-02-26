import os
import json
import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"owners": [], "users": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_owner(user_id: int) -> bool:
    data = load_data()
    return user_id in data.get("owners", [])

def get_user_bot(user_id: int):
    data = load_data()
    return data.get("users", {}).get(str(user_id))

def set_user_bot(user_id: int, token: str, username: str):
    data = load_data()
    data["users"][str(user_id)] = {
        "bot_token": token,
        "bot_username": username
    }
    save_data(data)

# TOKEN KUTISH HOLATI
waiting_for_token = {}

@bot.callback_query_handler(func=lambda c: c.data == "create_bot")
def create_bot(call):
    user_id = call.from_user.id
    user_bot = get_user_bot(user_id)

    if user_bot:
        text = (
            "Sizda limit to‘lgan 1/1.\n"
            f"Bot: @{user_bot['bot_username']}\n\n"
            "Agar yangisini ochmoqchi bo‘lsangiz — avval eski botni o‘chiring."
        )
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("🗑 O‘chirish", callback_data="bot_delete")
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.id, reply_markup=kb)
        return

    text = (
        "Salom!\n"
        "@BotFather’ga o‘ting va <b>/newbot</b> orqali yangi bot yarating.\n"
        "So‘ng tokenni shu yerga yuboring.\n\n"
        "Masalan:\n"
        "<code>123456:ABCDEF-ghijklmnop</code>"
    )

    waiting_for_token[user_id] = True

    bot.edit_message_text(text, call.message.chat.id, call.message.id)

@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_token)
def receive_token(message):
    user_id = message.from_user.id
    token = message.text.strip()

    # Token formatini tekshirish
    if ":" not in token:
        bot.reply_to(message, "Bu token emas. Iltimos, to‘g‘ri token yuboring.")
        return

    # API orqali tokenni tekshiramiz
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        r = requests.get(url).json()
    except:
        bot.reply_to(message, "Token tekshirishda xatolik. Qayta urinib ko‘ring.")
        return

    if not r.get("ok"):
        bot.reply_to(message, "❌ Token noto‘g‘ri. Iltimos, qayta yuboring.")
        return

    username = r["result"]["username"]

    # 1/1 limitni tekshiramiz
    if get_user_bot(user_id):
        bot.reply_to(message, "Sen dalbayobda allaqachon bot bor 😅\nAvval eski botni o‘chir.")
        return

    # Botni bazaga yozamiz
    set_user_bot(user_id, token, username)

    del waiting_for_token[user_id]

    # Foydalanuvchiga xabar
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            "Botga o‘tish",
            url=f"https://t.me/{username}?start=admin"
        )
    )

    bot.reply_to(
        message,
        f"Sizning @{username} botingiz tayyor!\n"
        "Admin panel uchun botga /admin yozing yoki pastdagi tugmani bosing.",
        reply_markup=kb
    )
