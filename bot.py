# ============================
# AniCreatorBot - EgaBot platformasi
# Asosiy bosh bot: @AniCreatorBot
# ============================

import os
import json
import time
import requests
import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# ----------------------------
# 1. Asosiy sozlamalar
# ----------------------------

# Render / lokal uchun:
# Lokal sinovda: TOKEN = "123456:ABCDEF..."
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    # Lokal test uchun, xohlasang bu yerga tokenni qo'yib turishing mumkin
    # TOKEN = "123456:ABCDEF..."
    raise SystemExit("BOT_TOKEN o'rnatilmagan. Iltimos, environment variable sifatida qo'ying.")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "data.json"
MAIN_BOT_USERNAME = "AniCreatorBot"  # reklama va referal uchun


# ----------------------------
# 2. Yordamchi funksiyalar
# ----------------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "owners": [],
            "users": {},        # user_id: {bot_token, bot_username, created_at}
            "bots": {},         # bot_username: {owner_id, token, created_at}
            "stats": {
                "created_bots": []
            },
            "settings": {
                "force_sub": []  # keyin majburiy obuna uchun
            }
        }
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
    uid = str(user_id)

    if "users" not in data:
        data["users"] = {}
    if "bots" not in data:
        data["bots"] = {}
    if "stats" not in data:
        data["stats"] = {"created_bots": []}

    now_ts = int(time.time())

    data["users"][uid] = {
        "bot_token": token,
        "bot_username": username,
        "created_at": now_ts
    }

    data["bots"][username] = {
        "owner_id": user_id,
        "bot_token": token,
        "created_at": now_ts
    }

    data["stats"]["created_bots"].append({
        "owner_id": user_id,
        "bot_username": username,
        "created_at": now_ts,
        "bot_token": token
    })

    save_data(data)


def delete_user_bot(user_id: int):
    data = load_data()
    uid = str(user_id)
    user_bot = data.get("users", {}).get(uid)

    if not user_bot:
        return False

    username = user_bot.get("bot_username")

    # users dan o'chiramiz
    del data["users"][uid]

    # bots dan o'chiramiz
    if username in data.get("bots", {}):
        del data["bots"][username]

    save_data(data)
    return True


def format_timestamp(ts: int) -> str:
    # oddiy ko'rinish: 2026-02-26 15:23
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


# ----------------------------
# 3. /start handler
# ----------------------------

@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    data = load_data()

    # Agar owners bo'sh bo'lsa, birinchi /start bosgan odam egaga aylanadi
    if not data.get("owners"):
        data["owners"] = [user_id]
        save_data(data)

    user_bot = get_user_bot(user_id)

    kb = InlineKeyboardMarkup()

    # Bot haqida tugma
    kb.add(
        InlineKeyboardButton("ℹ️ Bot haqida", callback_data="about")
    )

    # Bot yaratish / Mening botim
    if user_bot:
        kb.add(
            InlineKeyboardButton("🤖 Mening botim", callback_data="my_bot")
        )
    else:
        kb.add(
            InlineKeyboardButton("🆕 Bot yaratish", callback_data="create_bot")
        )

    # Matn
    if is_owner(user_id):
        text = (
            "Salom, egam!\n\n"
            "Siz <b>@AniCreatorBot</b> platformasining egasisiz.\n"
            "Botni boshqarish uchun /admin buyrug‘idan foydalaning."
        )
    else:
        text = (
            "Ushbu bot <b>kanaldan yuklab olish uchun maxsus botlar</b> yaratish tizimi.\n\n"
            "Siz ham o‘zingizga yuklovchi bot ochishingiz mumkin."
        )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=kb
    )


# ----------------------------
# 4. /admin - EgaBot admin paneli (skeleton)
# ----------------------------

@bot.message_handler(commands=['admin', 'Admin'])
def cmd_admin(message):
    user_id = message.from_user.id

    if not is_owner(user_id):
        return bot.reply_to(message, "Bu bo‘lim faqat egaga tegishli.")

    # ReplyKeyboard emas, inline emas deganding, lekin hozircha inline bilan skeleton qilamiz.
    kb = InlineKeyboardMarkup()
    # 1 qatorda 1-tugma
    kb.add(InlineKeyboardButton("1️⃣ Habar qo‘shish", callback_data="admin_add_media"))
    # 2-qator: 2 va 3
    kb.row(
        InlineKeyboardButton("2️⃣ Habar yuborish", callback_data="admin_send"),
        InlineKeyboardButton("3️⃣ Yaratilgan botlar", callback_data="admin_bots")
    )
    # 3-qator: 4 va 5
    kb.row(
        InlineKeyboardButton("4️⃣ Statistika", callback_data="admin_stats"),
        InlineKeyboardButton("5️⃣ Tizim sozlamalari", callback_data="admin_settings")
    )

    bot.send_message(
        message.chat.id,
        "Admin paneliga xush kelibsiz.\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=kb
    )


# ----------------------------
# 5. Asosiy menyu callbacklari
# ----------------------------

# Token kutish holati
waiting_for_token = {}  # user_id: True


@bot.callback_query_handler(func=lambda c: c.data in ["about", "create_bot", "my_bot"])
def main_menu_callbacks(call):
    user_id = call.from_user.id
    user_bot = get_user_bot(user_id)

    if call.data == "about":
        text = (
            "<b>AniCreator</b> — Anime va media yuklovchi botlar yaratish platformasi.\n\n"
            "Siz bu yerda o‘zingizga maxsus yuklovchi bot ochishingiz, "
            "kanal va foydalanuvchilarga media tarqatishingiz mumkin."
        )
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.id
        )

    elif call.data == "create_bot":
        # Agar allaqachon bot bo'lsa — limit 1/1
        if user_bot:
            text = (
                "Sizda limit to‘lgan <b>1/1</b>.\n"
                f"Bot: @{user_bot['bot_username']}\n\n"
                "Agar yangisini ochmoqchi bo‘lsangiz — avval eski botni o‘chiring."
            )
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("🟢 Bot holati", callback_data="bot_status"),
                InlineKeyboardButton("🗑 O‘chirish", callback_data="bot_delete")
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
            return

        # Aks holda — yangi bot yaratish jarayonini boshlaymiz
        text = (
            "Salom!\n\n"
            "@BotFather’ga o‘ting va <b>/newbot</b> buyrug‘i orqali o‘z botingizni yarating.\n"
            "Agar qila olmasangiz, pastda bot ochish haqida video qo‘shish mumkin (keyin).\n\n"
            "Bot tokenini tayyorlaganingizdan so‘ng, shu yerga yuboring.\n\n"
            "Masalan:\n"
            "<code>123456789:ABCDEF-ghijklmnop</code>\n\n"
            "Cheklovlar:\n"
            "1. Har bir foydalanuvchi faqat <b>1 ta bot</b> yaratishi mumkin.\n"
            f"2. Yaratuvchi reklama matni o‘chirib bo‘lmaydi: "
            f"⚠️ Ushbu bot @{MAIN_BOT_USERNAME} orqali yaratilgan ❗"
        )

        waiting_for_token[user_id] = True

        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.id
        )

    elif call.data == "my_bot":
        if not user_bot:
            bot.answer_callback_query(call.id, "Sizda hali bot yo‘q.")
            return

        text = (
            f"Sizning botingiz: @{user_bot['bot_username']}\n\n"
            "Quyidagi tugmalar orqali boshqarishingiz mumkin."
        )
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("🟢 Bot holati", callback_data="bot_status"),
            InlineKeyboardButton("🗑 O‘chirish", callback_data="bot_delete")
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


# ----------------------------
# 6. Token qabul qilish va botni ro'yxatga olish
# ----------------------------

@bot.message_handler(func=lambda m: m.from_user.id in waiting_for_token)
def receive_token(message):
    user_id = message.from_user.id
    token = message.text.strip()

    # Token formatini tekshirish
    if ":" not in token:
        bot.reply_to(message, "Bu token emasga o‘xshaydi. Iltimos, to‘g‘ri token yuboring.")
        return

    # Agar foydalanuvchida allaqachon bot bo'lsa
    if get_user_bot(user_id):
        bot.reply_to(
            message,
            "Sen dalbayobda allaqachon bot bor 😅\n"
            "Agar yana ochmoqchi bo‘lsang, avval eski botingni o‘chir."
        )
        # holatni tozalab qo'yamiz
        waiting_for_token.pop(user_id, None)
        return

    # API orqali tokenni tekshiramiz
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        r = requests.get(url, timeout=10).json()
    except Exception:
        bot.reply_to(message, "Token tekshirishda xatolik yuz berdi. Qayta urinib ko‘ring.")
        return

    if not r.get("ok"):
        bot.reply_to(message, "❌ Token noto‘g‘ri. Iltimos, qayta yuboring.")
        return

    username = r["result"]["username"]

    # Botni bazaga yozamiz
    set_user_bot(user_id, token, username)

    # Endi bu foydalanuvchi token kutmaydi
    waiting_for_token.pop(user_id, None)

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
        f"Sizning @{username} botingiz tayyor!\n\n"
        "Admin panel uchun botingizga <b>/admin</b> so‘zini yozing "
        "yoki pastdagi tugma orqali o‘tishingiz mumkin.",
        reply_markup=kb
    )


# ----------------------------
# 7. "Mening botim" menyusidagi callbacklar (holat, o'chirish, habar yuborish skeleton)
# ----------------------------

@bot.callback_query_handler(func=lambda c: c.data in ["bot_status", "bot_delete", "bot_broadcast"])
def bot_manage_callbacks(call):
    user_id = call.from_user.id
    user_bot = get_user_bot(user_id)

    if not user_bot:
        bot.answer_callback_query(call.id, "Sizda hali bot yo‘q.")
        return

    if call.data == "bot_status":
        # Hozircha faqat skeleton: keyin real holat (webhook/polling) tekshiramiz
        text = (
            f"Sizning botingiz: @{user_bot['bot_username']}\n"
            "Holat: 🟢 Faol (skeleton)\n\n"
            "Keyingi bosqichda bu yerda real holat ko‘rsatiladi."
        )
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.id
        )

    elif call.data == "bot_delete":
        # Botni bazadan o'chiramiz
        ok = delete_user_bot(user_id)
        if ok:
            text = (
                "Sizning botingiz o‘chirildi.\n\n"
                "Endi yangi bot yaratishingiz mumkin."
            )
        else:
            text = "Sizda o‘chirish uchun bot topilmadi."

        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.id
        )

    elif call.data == "bot_broadcast":
        # Hozircha skeleton: keyin foydalanuvchi botiga habar yuborish tizimini qo‘shamiz
        text = (
            f"Siz @{user_bot['bot_username']} botingiz orqali foydalanuvchilarga habar yuborishingiz mumkin.\n\n"
            "Bu bo‘lim hozircha skeleton. Keyingi bosqichda:\n"
            "- Forward / Oddiy\n"
            "- Shaxsiy / Ommaviy / Kanal / Foydalanuvchilar / Har ikkisiga\n"
            "- Tugmali xabarlar\n"
            "tizimi qo‘shiladi."
        )
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.id
        )


# ----------------------------
# 8. Admin panel callback skeletonlari
# ----------------------------

@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_"))
def admin_callbacks(call):
    user_id = call.from_user.id

    if not is_owner(user_id):
        bot.answer_callback_query(call.id, "Bu bo‘lim faqat egaga tegishli.")
        return

    if call.data == "admin_add_media":
        text = (
            "📥 Habar qo‘shish bo‘limi (skeleton).\n\n"
            "Keyingi bosqichda bu yerda:\n"
            "- Media qabul qilish\n"
            "- 0.10 soniya farq bilan yuklash\n"
            "- \"✔️ TAMOM\" tugmasi\n"
            "tizimi qo‘shiladi."
        )
    elif call.data == "admin_send":
        text = (
            "📤 Habar yuborish bo‘limi (skeleton).\n\n"
            "Keyingi bosqichda bu yerda:\n"
            "- Forward / Oddiy\n"
            "- Shaxsiy / Ommaviy / Kanal / Foydalanuvchilar / Har ikkisiga\n"
            "- Tugmali xabarlar\n"
            "tizimi qo‘shiladi."
        )
    elif call.data == "admin_bots":
        data = load_data()
        created = data.get("stats", {}).get("created_bots", [])
        last10 = created[-10:]

        if not last10:
            text = "Hali birorta ham bot yaratilmagan."
        else:
            lines = ["Oxirgi 10 ta yaratilgan bot:"]
            for i, info in enumerate(last10, start=1):
                uname = info.get("bot_username")
                owner = info.get("owner_id")
                ts = info.get("created_at")
                token = info.get("bot_token", "")
                lines.append(
                    f"{i}. @{uname} | owner: <code>{owner}</code> | "
                    f"{format_timestamp(ts)} | Token: <code>{token}</code>"
                )
            text = "\n".join(lines)

        # Keyingi bosqichda: "Barchasini txt faylga chiqarish" tugmasini qo‘shamiz.
    elif call.data == "admin_stats":
        # Hozircha juda oddiy skeleton
        data = load_data()
        created = data.get("stats", {}).get("created_bots", [])
        total_bots = len(created)
        total_users = len(data.get("users", {}))

        text = (
            "📊 Bot statistikasi (skeleton):\n\n"
            f"Barcha yaratilgan botlar: <b>{total_bots}</b>\n"
            f"Barcha foydalanuvchilar: <b>{total_users}</b>\n\n"
            "Keyingi bosqichda bu yerda:\n"
            "- Bugun qo‘shilgan\n"
            "- Oxirgi 10 kun\n"
            "- Oxirgi 1 oy\n"
            "- Oxirgi 1 yil\n"
            "bo‘yicha to‘liq statistika bo‘ladi."
        )
    elif call.data == "admin_settings":
        text = (
            "⚙️ Tizim sozlamalari (skeleton).\n\n"
            "Bu yerda keyinchalik:\n"
            "- Majburiy obuna (3 xil turi)\n"
            "- Kanallar ro‘yxati\n"
            "- Tahrirlash\n"
            "- txt faylga chiqarish\n"
            "tizimi bo‘ladi."
        )
    else:
        text = "Noma’lum admin bo‘limi."

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.id
    )


# ----------------------------
# 9. Botni ishga tushirish
# ----------------------------

if __name__ == "__main__":
    print("AniCreatorBot ishga tushdi...")
    bot.infinity_polling(skip_pending=True)
