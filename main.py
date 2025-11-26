# ============================================
# Telegram BOT (Webhook version for Render)
# ============================================

from typing import Any, Dict
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from flask import Flask, request, render_template_string
from datetime import datetime
import requests
import random
import os
import time
import asyncio

# =============================
# SETTINGS
# =============================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DASHBOARD_PASS = os.getenv("DASHBOARD_PASS", "Rami24545")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in Secrets!")

WEBHOOK_URL = os.getenv(
    "WEBHOOK_URL",
    "https://your-app.onrender.com/webhook",   # ضع رابط Render هنا
)

# =============================
# Flask App
# =============================
web_app = Flask(__name__)

# =============================
# Bot Statistics
# =============================
TOTAL_MESSAGES = 0
UNIQUE_USERS: set[int] = set()
UNIQUE_GROUPS: set[int] = set()
UNIQUE_PRIVATE_CHATS: set[int] = set()
ACTIVITY_BUCKETS: Dict[str, int] = {}

START_TIME = time.time()
BOT_START_TIME = START_TIME

# =============================
# Developer Info
# =============================
DEVELOPER_NAME = "المطور"
DEVELOPER_USERNAME = "@R_BF4"
DEVELOPER_LINK = "https://t.me/R_BF4"

# =============================
# Games List Text
# =============================
GAMES_HELP_TEXT = (
    "🎮 *قائمة الألعاب الموجودة في البوت:*\n\n"
    "1️⃣ *كتت*\n"
    "2️⃣ *عام*\n"
    "3️⃣ *لو*\n"
    "4️⃣ *من*\n"
    "5️⃣ *جريمة*\n"
    "6️⃣ *حل الجريمة*\n"
    "7️⃣ *حقائق*\n"
    "✨ لعرض القائمة: (العاب)"
)

# =============================
# File Loading Helpers
# =============================
def load_list_file(filename: str):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_general_questions(filename: str):
    if not os.path.exists(filename):
        return []
    data = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                q, a = line.strip().split("|", 1)
                data.append((q, a))
    return data


def load_used(filename: str):
    if not os.path.exists(filename):
        return set()
    with open(filename, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)


def save_used(filename: str, value: str):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(value + "\n")


# =============================
# Load Game Files
# =============================
KT_QUESTIONS = load_list_file("questions.txt") or ["كم عمرك؟", "ما هوايتك؟"]
GENERAL_RIDDLES = load_general_questions("general_riddles.txt") or [("ما عاصمة فرنسا؟","باريس")]
WOULD_YOU_RATHER = load_list_file("would_you_rather.txt") or ["لو خيروك تعيش غني أو فقير مع من تحب؟"]
WHO_QUESTIONS = load_list_file("who.txt") or ["من أكثر شخص يعجبك بالقروب؟"]
CRIMES = load_list_file("crimes.txt") or ["رجل مات في غرفة مغلقة | مات بسكتة قلبية"]
FACTS = load_list_file("facts.txt") or ["الحقيقة ليست دائمًا ما نراه."]

USED_KT = load_used("used_kt.txt")
USED_GENERAL = load_used("used_general.txt")
USED_WYR = load_used("used_wyr.txt")
USED_WHO = load_used("used_who.txt")
USED_CRIMES = load_used("used_crimes.txt")
USED_FACTS = load_used("used_facts.txt")

# =============================
# Helpers
# =============================
def normalize_text(t: str):
    return (
        t.strip()
        .lower()
        .replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ة", "ه")
    )


def is_answer_word(t: str):
    return normalize_text(t) in ["اجابه", "الاجابه", "جواب"]


# =============================
# Commands
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "تم تفعيل البوت 👋\nالأوامر:\nكتت - عام - لو - من - جريمة - حقائق - حل"
    )


async def developer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"المطور:\n{DEVELOPER_NAME}\n{DEVELOPER_USERNAME}\n{DEVELOPER_LINK}"
    )


async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(GAMES_HELP_TEXT, parse_mode="Markdown")


# =============================
# Message Handler
# =============================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_MESSAGES

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    normalized = normalize_text(text)

    # ============ Statistics ============
    user = update.message.from_user
    chat = update.message.chat

    TOTAL_MESSAGES += 1
    UNIQUE_USERS.add(user.id)

    if chat.type in ("group", "supergroup"):
        UNIQUE_GROUPS.add(chat.id)
    else:
        UNIQUE_PRIVATE_CHATS.add(chat.id)

    bucket = datetime.utcnow().strftime("%Y-%m-%d %H:00")
    ACTIVITY_BUCKETS[bucket] = ACTIVITY_BUCKETS.get(bucket, 0) + 1

    # ============ Games ============

    # الألعاب
    if normalized in ["العاب", "الالعاب"]:
        await update.message.reply_text(GAMES_HELP_TEXT, parse_mode="Markdown")
        return

    # كتت
    if text == "كتت":
        pool = [q for q in KT_QUESTIONS if q not in USED_KT]
        if not pool:
            USED_KT.clear()
            open("used_kt.txt", "w").close()
            pool = KT_QUESTIONS

        q = random.choice(pool)
        save_used("used_kt.txt", q)
        USED_KT.add(q)
        await update.message.reply_text(q)
        return

    # عام
    if text == "عام":
        pool = [(q, a) for (q, a) in GENERAL_RIDDLES if q not in USED_GENERAL]
        if not pool:
            USED_GENERAL.clear()
            open("used_general.txt", "w").close()
            pool = GENERAL_RIDDLES

        q, a = random.choice(pool)
        save_used("used_general.txt", q)
        USED_GENERAL.add(q)

        context.user_data["last_q"] = q
        context.user_data["last_a"] = a

        await update.message.reply_text(q)
        return

    if is_answer_word(text):
        if "last_q" in context.user_data:
            await update.message.reply_text(
                f"السؤال:\n{context.user_data['last_q']}\n\n"
                f"الإجابة:\n{context.user_data['last_a']}"
            )
        else:
            await update.message.reply_text("لا يوجد سؤال.")
        return

    # لو
    if text == "لو":
        pool = [q for q in WOULD_YOU_RATHER if q not in USED_WYR]
        if not pool:
            USED_WYR.clear()
            open("used_wyr.txt", "w").close()
            pool = WOULD_YOU_RATHER

        q = random.choice(pool)
        save_used("used_wyr.txt", q)
        USED_WYR.add(q)
        await update.message.reply_text(q)
        return

    # من
    if text == "من":
        pool = [q for q in WHO_QUESTIONS if q not in USED_WHO]
        if not pool:
            USED_WHO.clear()
            open("used_who.txt", "w").close()
            pool = WHO_QUESTIONS

        q = random.choice(pool)
        save_used("used_who.txt", q)
        USED_WHO.add(q)
        await update.message.reply_text(q)
        return

    # جريمة
    if text == "جريمة":
        pool = [c for c in CRIMES if c not in USED_CRIMES]
        if not pool:
            USED_CRIMES.clear()
            open("used_crimes.txt", "w").close()
            pool = CRIMES

        c = random.choice(pool)
        save_used("used_crimes.txt", c)
        USED_CRIMES.add(c)

        if "|" in c:
            story, sol = c.split("|", 1)
            context.user_data["crime_sol"] = sol.strip()
            await update.message.reply_text(story.strip())
        else:
            await update.message.reply_text(c)
        return

    # حل الجريمة
    if normalized in ["حل", "حل الجريمة"]:
        if "crime_sol" in context.user_data:
            await update.message.reply_text(
                f"🔍 حل الجريمة:\n{context.user_data['crime_sol']}"
            )
        else:
            await update.message.reply_text("لا توجد جريمة حالياً.")
        return

    # حقائق
    if text == "حقائق":
        pool = [f for f in FACTS if f not in USED_FACTS]
        if not pool:
            USED_FACTS.clear()
            open("used_facts.txt", "w").close()
            pool = FACTS

        f = random.choice(pool)
        save_used("used_facts.txt", f)
        USED_FACTS.add(f)
        await update.message.reply_text("🧠 حقيقة:\n" + f)
        return


# =============================
# Dashboard HTML
# =============================
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8" />
<title>لوحة تحكم البوت</title>
<style>
body { background:#0b0f19; color:white; font-family:Arial; padding:20px; }
.box { background:#111827; padding:20px; border-radius:12px; margin-bottom:20px; }
</style>
</head>
<body>
{% if not authorized %}
<form action="/dashboard">
<input type="password" name="key" placeholder="كلمة المرور" />
<button>دخول</button>
</form>
{% else %}
<h1>لوحة التحكم</h1>

<div class="box">المستخدمون: {{ unique_users }}</div>
<div class="box">الجروبات: {{ groups }}</div>
<div class="box">الخاص: {{ private_chats }}</div>
<div class="box">الرسائل: {{ messages }}</div>

{% endif %}
</body>
</html>
"""


@web_app.route("/")
def home():
    return "Bot is running via Webhook!"


@web_app.route("/dashboard")
def dashboard():
    key = request.args.get("key", "")
    if key != DASHBOARD_PASS:
        return render_template_string(DASHBOARD_TEMPLATE, authorized=False)

    return render_template_string(
        DASHBOARD_TEMPLATE,
        authorized=True,
        unique_users=len(UNIQUE_USERS),
        groups=len(UNIQUE_GROUPS),
        private_chats=len(UNIQUE_PRIVATE_CHATS),
        messages=TOTAL_MESSAGES,
    )


# =============================
# Telegram Webhook Receiver
# =============================
@web_app.route("/webhook", methods=["POST"])
def webhook_receiver():
    update_data = request.get_json()
    update = Update.de_json(update_data, app.bot)
    asyncio.get_event_loop().create_task(app.process_update(update))
    return "OK", 200


# =============================
# INIT BOT
# =============================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("developer", developer))
app.add_handler(CommandHandler("games", games))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# =============================
# SET WEBHOOK
# =============================
async def set_webhook():
    await app.bot.delete_webhook()
    await app.bot.set_webhook(url="https://telegram-rami-bot-1.onrender.com/webhook")

asyncio.run(set_webhook())


