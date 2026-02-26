import os
import json
import telebot
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
    if "users" not in data:
        data["users"] = {}
    data["users"][str(user_id)] = {
        "bot_token": token,
        "bot_username": username
    }
    save_data(data)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    data = load_data()

    # agar hali ownerlar ro'yxati bo'sh bo'lsa, birinchi /start bosgan odam egaga aylanadi
    if not data["owners"]:
        data["owners"].append(user_id)
        save_data(data)

    kb = InlineKeyboardMarkup()
    user_bot = get_user_bot(user_id)

    if is_owner(user_id):
        text = (
            "Salom, egam!\n"
            "Siz botga /Admin buyrug‘i orqali kirishingiz mumkin."
        )
    else:
        text = (
            "Ushbu bot Kanaldan yuklab olish uchun maxsus bot.\n"
        )

    # pastdagi tugmalar: Bot haqida, Bot yaratish / Mening botim
    kb.add(
        InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")
    )

    if user_bot:
        kb.add(
            InlineKeyboardButton("🤖 Mening botim", callback_data="my_bot")
        )
    else:
        kb.add(
            InlineKeyboardButton("🆕 Bot yaratish", callback_data="create_bot")
        )

    bot.send_message(message.chat.id, text, reply_markup=kb)

@bot.message_handler(commands=['Admin', 'admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return bot.reply_to(message, "Bu bo‘lim faqat egaga tegishli.")

    # Admin panel tugmalari (reply keyboard emas, inline emas — lekin hozircha inline bilan boshlaymiz,
    # keyin xohlasang ReplyKeyboardMarkup qilib beraman)
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("1️⃣ Habar qo‘shish", callback_data="admin_add_media"))
    kb.row(
        InlineKeyboardButton("2️⃣ Habar yuborish", callback_data="admin_send"),
        InlineKeyboardButton("3️⃣ Yaratilgan botlar", callback_data="admin_bots"),
    )
    kb.row(
        InlineKeyboardButton("4️⃣ Statistika", callback_data="admin_stats"),
        InlineKeyboardButton("5️⃣ Tizim sozlamalari", callback_data="admin_settings"),
    )

    bot.send_message(
        message.chat.id,
        "Admin paneliga xush kelibsiz.",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda c: c.data in ["about", "create_bot", "my_bot"])
def main_menu_callbacks(call):
    user_id = call.from_user.id
    data = load_data()
    user_bot = get_user_bot(user_id)

    if call.data == "about":
        text = (
            "Bu bot kanallardan yuklab olish uchun maxsus tizim boshqaruvchisi.\n"
            "Yangi bot yaratib, o‘zingizga yuklovchi bot ochishingiz mumkin."
        )
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.id
        )

    elif call.data == "create_bot":
        if user_bot:
            # allaqachon bot bor
            text = (
                "Sizda limit to‘lgan 1/1.\n"
                f"Bot: @{user_bot['bot_username']}\n\n"
                "Quyidagi tugmalar orqali boshqarishingiz mumkin."
            )
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("🟢 Bot holati", callback_data="bot_status"),
                InlineKeyboardButton("🗑 O‘chirish", callback_data="bot_delete"),
            )
            kb.add(
                InlineKeyboardButton("📤 Habar yuborish", callback_data="bot_broadcast")
            )
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                reply_markup=kb
            )
        else:
            # hali bot yo'q — yangi yaratish jarayonini boshlaymiz
            text = (
                "Salom! @BotFather’ga o‘ting va /newbot buyrug‘i orqali o‘z botingizni yarating.\n"
                "Agar qila olmasangiz, pastdagi video orqali o‘rganishingiz mumkin.\n\n"
                "Bot tokenini tayyorlaganingizdan so‘ng, shu yerga yuboring."
            )
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.id
            )
            # bu yerda keyingi bosqichda: foydalanuvchidan token qabul qilish logikasini qo‘shamiz

    elif call.data == "my_bot":
        if not user_bot:
            bot.answer_callback_query(call.id, "Sizda hali bot yo‘q.")
            return
        text = (
            f"Sizning botingiz: @{user_bot['bot_username']}\n"
            "Quyidagi tugmalar orqali boshqarishingiz mumkin."
        )
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("🟢 Bot holati", callback_data="bot_status"),
            InlineKeyboardButton("🗑 O‘chirish", callback_data="bot_delete"),
        )
        kb.add(
            InlineKeyboardButton("📤 Habar yuborish", callback_data="bot_broadcast")
        )
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            reply_markup=kb
        )

bot.polling()
