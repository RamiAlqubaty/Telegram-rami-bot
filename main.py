# ============================================
# Telegram Game Bot - Webhook + Dashboard + Broadcast + Truth/Dare Game
# For Render (gunicorn main:web_app)
# ============================================

from typing import Dict
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)
from telegram.request import HTTPXRequest
from flask import Flask, request, render_template_string
from datetime import datetime, timezone
import random
import os
import time
import asyncio
import json
# from dotenv import load_dotenv

# =============================
# SETTINGS
# =============================
# load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DASHBOARD_PASS = os.getenv("DASHBOARD_PASS", "Rami24545")
RUN_MODE = os.getenv("RUN_MODE", "polling").lower()

print("BOT_TOKEN loaded:", "****" if BOT_TOKEN else None)
print("RUN_MODE:", RUN_MODE)

if not BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN not found in Secrets!")

# غيّر هذا الرابط لو تغيّر اسم الخدمة في Render
WEBHOOK_URL = "https://telegram-rami-bot-1.onrender.com/webhook"

STATS_FILE = "stats.json"

# اسم المستخدم للمطور (بدون @)
DEVELOPER_USERNAME_RAW = "R_q1j"

# =============================
# Flask App
# =============================
web_app = Flask(__name__)

# =============================
# Bot Statistics (globals)
# =============================
TOTAL_MESSAGES = 0
UNIQUE_USERS: set[int] = set()
UNIQUE_GROUPS: set[int] = set()
UNIQUE_PRIVATE_CHATS: set[int] = set()
ACTIVITY_BUCKETS: Dict[str, int] = {}
BOT_START_TIME = time.time()

# =============================
# Developer Info
# =============================
DEVELOPER_NAME = "المطور"
DEVELOPER_USERNAME = "@R_q1j"
DEVELOPER_LINK = "https://t.me/R_q1j"

# =============================
# Games & Help Texts
# =============================
GAMES_HELP_TEXT = (
    "🎮 *قائمة الألعاب الموجودة في البوت:*\n\n"
    "1️⃣ *كتت* — أسئلة شخصية وللتعارف.\n"
    "    ⌨️ اكتب: `كتت`\n\n"
    "2️⃣ *عام* — أسئلة عامة وألغاز.\n"
    "    ⌨️ اكتب: `عام`\n"
    "    🧩 لعرض الإجابة بعد السؤال اكتب: `اجابة` أو `جواب`\n\n"
    "3️⃣ *لو* — لو خيروك (اختيارات صعبة).\n"
    "    ⌨️ اكتب: `لو`\n\n"
    "4️⃣ *من* — أسئلة (من هو؟) داخل القروب.\n"
    "    ⌨️ اكتب: `من`\n\n"
    "5️⃣ *جريمة* — قصة جريمة تحاولون تحلونها.\n"
    "    ⌨️ اكتب: `جريمة`\n"
    "    🕵 بعد التفكير اكتب: `حل` أو `حل الجريمة`\n\n"
    "6️⃣ *حقائق* — حقائق عشوائية.\n"
    "    ⌨️ اكتب: `حقائق`\n\n"
    "7️⃣ *تحدي أو صراحة* — لعبة جماعية بالأزرار.\n"
    "    ⌨️ اكتب: `تحدي` أو `صراحه` لبدء جلسة جديدة.\n\n"
    "✨ لعرض هذه القائمة اكتب: `العاب` أو استخدم الأمر: `/games`"
)

HELP_TEXT = (
    "👋 *مرحباً بك في بوت الألعاب!*\n\n"
    "البوت يقدم:\n"
    "• ألعاب ترفيهية للقروبات والخاص.\n"
    "• ألغاز وأسئلة عامة.\n"
    "• حقائق عشوائية.\n"
    "• لعبة تحدي/صراحة تفاعلية.\n\n"
    "📌 *الأوامر الرئيسية:*\n"
    "• `/start`  — رسالة الترحيب.\n"
    "• `/help`   — شرح تفصيلي.\n"
    "• `/games`  — عرض قائمة الألعاب.\n"
    "• `/developer` — معلومات المطور.\n\n"
    "🎮 *الألعاب:* \n"
    "استخدم الأوامر: `كتت`، `عام`، `لو`، `من`، `جريمة`، `حقائق`، `تحدي`، `صراحه`.\n\n"
    "للمزيد عن الألعاب استخدم `/games`."
)

# =============================
# Helpers (text & developer)
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
    return normalize_text(t) in ["اجابه", "جواب", "الاجابه"]


def is_developer(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    if not user.username:
        return False
    return user.username.lower() == DEVELOPER_USERNAME_RAW.lower()

# =============================
# File Helpers
# =============================
def load_list_file(filename: str):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]


def load_general_questions(filename: str):
    if not os.path.exists(filename):
        return []
    res = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                q, a = line.strip().split("|", 1)
                res.append((q, a))
    return res


def load_used(filename: str):
    if not os.path.exists(filename):
        return set()
    with open(filename, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)


def save_used(filename: str, value: str):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(value + "\n")


def load_autoreplies(filename: str) -> Dict[str, str]:
    """
    يحمّل ردود سريعة من ملف بالشكل:
    كلمة=الرد الكامل
    ويتم تخزين المفتاح بعد normalize_text كي يكون التطابق أسهل.
    """
    if not os.path.exists(filename):
        return {}

    data: Dict[str, str] = {}
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key_norm = normalize_text(key)
            data[key_norm] = value.strip()
    return data

# =============================
# Load Game Files
# =============================
KT_QUESTIONS = load_list_file("questions.txt") or ["كم عمرك؟", "ما هوايتك؟"]
GENERAL_RIDDLES = load_general_questions("general_riddles.txt") or [("ما عاصمة فرنسا؟", "باريس")]
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

AUTOREPLIES = load_autoreplies("autoreplies.txt")

# =============================
# Truth/Dare Game Files (جديدة)
# =============================
TRUTH_QUESTIONS = load_list_file("truth.txt") or [
    "ما هي أكثر صفة تحبها في نفسك؟",
    "ما هو أكثر موقف مضحك حصل لك؟",
    "لو تقدر ترجع بالزمن، أي سنة ترجع؟",
]

DARE_QUESTIONS = load_list_file("dare.txt") or [
    "غيّر اسمك في القروب لاسم مضحك لمدة 10 دقائق.",
    "ارسل آخر إيموجي استخدمته وقل لنا قصته 😹",
    "اكتب رسالة مدح لآخر واحد كتب في القروب.",
]

USED_TRUTH = load_used("used_truth.txt")
USED_DARE = load_used("used_dare.txt")


def choose_unique_question(pool, used_set, filename: str) -> str:
    """
    يختار سؤال بدون تكرار حتى تنتهي القائمة، بعدها يعيد ضبط الاستخدام.
    """
    if not pool:
        return "لا توجد أسئلة حالياً."

    available = [q for q in pool if q not in used_set]
    if not available:
        used_set.clear()
        try:
            open(filename, "w", encoding="utf-8").close()
        except Exception:
            pass
        available = pool

    q = random.choice(available)
    used_set.add(q)
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(q + "\n")
    except Exception:
        pass
    return q


def display_name_from_user(user) -> str:
    if user.username:
        return f"@{user.username}"
    return user.full_name or str(user.id)

# =============================
# Stats Persistence
# =============================
def load_stats():
    global TOTAL_MESSAGES, UNIQUE_USERS, UNIQUE_GROUPS, UNIQUE_PRIVATE_CHATS, ACTIVITY_BUCKETS
    if not os.path.exists(STATS_FILE):
        return
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        TOTAL_MESSAGES = data.get("total_messages", 0)
        UNIQUE_USERS = set(data.get("unique_users", []))
        UNIQUE_GROUPS = set(data.get("unique_groups", []))
        UNIQUE_PRIVATE_CHATS = set(data.get("unique_private_chats", []))
        ACTIVITY_BUCKETS.update(data.get("activity_buckets", {}))
    except Exception:
        pass


def save_stats():
    data = {
        "total_messages": TOTAL_MESSAGES,
        "unique_users": list(UNIQUE_USERS),
        "unique_groups": list(UNIQUE_GROUPS),
        "unique_private_chats": list(UNIQUE_PRIVATE_CHATS),
        "activity_buckets": ACTIVITY_BUCKETS,
    }
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


load_stats()

# =============================
# Bot Commands
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت الألعاب.\n\n"
        "استخدم `/help` لعرض الشرح الكامل.\n"
        "واكتب `العاب` أو استخدم `/games` لعرض قائمة الألعاب."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def developer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👨‍💻 المطور:\n{DEVELOPER_NAME}\n{DEVELOPER_USERNAME}\n{DEVELOPER_LINK}"
    )


async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(GAMES_HELP_TEXT, parse_mode="Markdown")


# ========= BroadCast (بودكاست) =========
async def podcast_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    هذا الأمر خاص بالمطور فقط.
    الفكرة: يكتب المطور /podcast نص الرسالة
    فيقوم البوت بإرسالها لكل الجروبات المسجلة في UNIQUE_GROUPS.
    """
    if not is_developer(update):
        await update.message.reply_text("هذه الميزة خاصة بالمطور فقط. 🚫")
        return

    # نص الرسالة بعد الأمر /podcast
    args_text = " ".join(context.args).strip()

    # لو ما كتب شيء بعد الأمر، نحاول نأخذ نص الرسالة اللي عامل لها رد
    if not args_text and update.message.reply_to_message:
        if update.message.reply_to_message.text:
            args_text = update.message.reply_to_message.text.strip()

    if not args_text:
        await update.message.reply_text(
            "اكتب الأمر بالشكل التالي:\n"
            "`/podcast نص الرسالة المراد إرسالها`\n"
            "أو رد /podcast على رسالة موجودة.",
            parse_mode="Markdown",
        )
        return

    if not UNIQUE_GROUPS:
        await update.message.reply_text("لا توجد أي جروبات مسجلة حالياً لإرسال الرسالة لها.")
        return

    sent = 0
    failed = 0

    for chat_id in list(UNIQUE_GROUPS):
        try:
            await context.bot.send_message(chat_id=chat_id, text=args_text)
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"✅ تم إرسال الرسالة إلى {sent} جروب.\n"
        f"❌ فشل الإرسال إلى {failed} (ربما البوت مطرود من بعضها)."
    )

# =============================
# Truth/Dare Game Logic (جديد)
# =============================
async def td_start_new_turn(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """
    يبدأ دور جديد: يختار لاعب عشوائي من المشاركين بدون تكرار
    حتى يمر على الجميع، ثم يعيد الدورة.
    """
    chat_data = context.chat_data
    game = chat_data.get("truth_dare_game")
    if not game or game.get("status") != "running":
        return

    participants = list(game.get("participants", {}).keys())
    if not participants:
        await context.bot.send_message(chat_id=chat_id, text="لا يوجد لاعبين في اللعبة.")
        game["status"] = "ended"
        return

    remaining = game.get("remaining_players")
    if not remaining:
        remaining = participants.copy()

    player_id = random.choice(remaining)
    remaining.remove(player_id)

    game["remaining_players"] = remaining
    game["current_player_id"] = player_id
    game["current_round"] = {
        "player_id": player_id,
        "final_choice": None,
        "switched": False,
    }

    player_info = game["participants"].get(player_id)
    mention = player_info.get("name") if player_info else str(player_id)
    if player_info and player_info.get("username"):
        mention = f"@{player_info['username']}"

    text = (
        f"🎯 الدور الآن على {mention}\n"
        "اختر: تحدي أو صراحة 👇"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔥 تحدي", callback_data="td_choose:dare"),
            InlineKeyboardButton("💬 صراحة", callback_data="td_choose:truth"),
        ]
    ])

    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)


async def td_close_join_phase(context: ContextTypes.DEFAULT_TYPE):
    """
    تُستدعى آلياً بعد دقيقة من بدء اللعبة لإغلاق الانضمام.
    """
    job = context.job
    chat_id = job.chat_id
    chat_data = context.chat_data
    game = chat_data.get("truth_dare_game")

    if not game or game.get("status") != "collecting":
        return

    participants = list(game.get("participants", {}).values())
    if not participants:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⏰ انتهى وقت الانضمام ولم ينضم أحد للعبة."
        )
        game["status"] = "ended"
        return

    game["status"] = "waiting_start"
    game["remaining_players"] = list(game["participants"].keys())

    lines = ["⏰ انتهى وقت الانضمام!\n", "اللاعبون المشاركون:"]
    for p in participants:
        if p.get("username"):
            lines.append(f"- @{p['username']}")
        else:
            lines.append(f"- {p['name']}")
    text = "\n".join(lines)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ بدء اللعبة", callback_data="td_start")]
    ])

    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)


async def td_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_data = context.chat_data
    game = chat_data.get("truth_dare_game")

    if not game or game.get("status") != "collecting":
        await query.answer("لا توجد لعبة مفتوحة للانضمام حالياً.", show_alert=True)
        return

    user = query.from_user
    participants = game.setdefault("participants", {})

    if user.id in participants:
        await query.answer("أنت منضم للعبة بالفعل ✅", show_alert=False)
        return

    participants[user.id] = {
        "id": user.id,
        "name": user.full_name,
        "username": user.username,
    }

    await query.answer("تم انضمامك للعبة 🎮", show_alert=False)

    try:
        count = len(participants)
        await query.message.edit_text(
            f"🕹 *جولة جديدة: تحدي أو صراحة*\n"
            f"عدد اللاعبين المنضمين حتى الآن: {count}\n"
            "اضغط على الزر بالأسفل للانضمام خلال دقيقة واحدة ⏱",
            reply_markup=query.message.reply_markup,
            parse_mode="Markdown",
        )
    except Exception:
        pass


async def td_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_data = context.chat_data
    game = chat_data.get("truth_dare_game")

    if not game or game.get("status") not in ("waiting_start", "collecting"):
        await query.answer("لا يمكن بدء اللعبة حالياً.", show_alert=True)
        return

    participants = list(game.get("participants", {}).keys())
    if len(participants) < 1:
        await query.answer("لا يوجد لاعبين كفاية لبدء اللعبة.", show_alert=True)
        game["status"] = "ended"
        return

    game["status"] = "running"

    await query.message.reply_text("✅ تم بدء لعبة تحدي/صراحة! لنبدأ 🔥")
    await td_start_new_turn(query.message.chat.id, context)


async def td_choose_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data  # مثال: "td_choose:dare"
    await query.answer()

    _, choice = data.split(":", 1)  # "truth" أو "dare"
    chat_data = context.chat_data
    game = chat_data.get("truth_dare_game")

    if not game or game.get("status") != "running":
        await query.answer("لا توجد لعبة نشطة حالياً.", show_alert=True)
        return

    user = query.from_user
    current_player_id = game.get("current_player_id")
    if user.id != current_player_id:
        await query.answer("هذا الدور ليس دورك 😅", show_alert=True)
        return

    round_state = game.get("current_round") or {}
    round_state["player_id"] = user.id
    round_state["final_choice"] = choice  # "truth" أو "dare"
    round_state["switched"] = False
    game["current_round"] = round_state

    player_display = display_name_from_user(user)

    if choice == "dare":
        q = choose_unique_question(DARE_QUESTIONS, USED_DARE, "used_dare.txt")
        text = f"🔥 *تحدي لـ {player_display}:*\n{q}"
        switch_button = InlineKeyboardButton("↩️ تحويل إلى صراحة", callback_data="td_switch:truth")
    else:
        q = choose_unique_question(TRUTH_QUESTIONS, USED_TRUTH, "used_truth.txt")
        text = f"💬 *صراحة لـ {player_display}:*\n{q}"
        switch_button = InlineKeyboardButton("↩️ تحويل إلى تحدي", callback_data="td_switch:dare")

    next_button = InlineKeyboardButton("🔁 لاعب جديد", callback_data="td_next")

    keyboard = InlineKeyboardMarkup([
        [switch_button],
        [next_button],
    ])

    await query.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def td_switch_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data  # مثال: "td_switch:truth"
    await query.answer()

    _, new_choice = data.split(":", 1)  # "truth" أو "dare"
    chat_data = context.chat_data
    game = chat_data.get("truth_dare_game")

    if not game or game.get("status") != "running":
        await query.answer("لا توجد لعبة نشطة حالياً.", show_alert=True)
        return

    user = query.from_user
    round_state = game.get("current_round")
    if not round_state or round_state.get("player_id") != user.id:
        await query.answer("هذا الخيار ليس دورك 😅", show_alert=True)
        return

    if round_state.get("switched"):
        await query.answer("لا يمكنك التحويل أكثر من مرة في نفس الدور.", show_alert=True)
        return

    round_state["final_choice"] = new_choice
    round_state["switched"] = True
    game["current_round"] = round_state

    player_display = display_name_from_user(user)

    if new_choice == "truth":
        q = choose_unique_question(TRUTH_QUESTIONS, USED_TRUTH, "used_truth.txt")
        text = (
            f"🔄 تم التحويل إلى *صراحة* لـ {player_display}:\n"
            f"{q}"
        )
    else:
        q = choose_unique_question(DARE_QUESTIONS, USED_DARE, "used_dare.txt")
        text = (
            f"🔄 تم التحويل إلى *تحدي* لـ {player_display}:\n"
            f"{q}"
        )

    next_button = InlineKeyboardButton("🔁 لاعب جديد", callback_data="td_next")
    keyboard = InlineKeyboardMarkup([[next_button]])

    await query.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def td_next_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_data = context.chat_data
    game = chat_data.get("truth_dare_game")

    if not game or game.get("status") != "running":
        await query.answer("لا توجد لعبة نشطة حالياً.", show_alert=True)
        return

    await td_start_new_turn(query.message.chat.id, context)

# =============================
# Message Handler (games, stats, autoreplies)
# =============================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_MESSAGES

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    normalized = normalize_text(text)

    # ===== Stats =====
    user = update.message.from_user
    chat = update.message.chat

    TOTAL_MESSAGES += 1
    UNIQUE_USERS.add(user.id)

    if chat.type in ("group", "supergroup"):
        UNIQUE_GROUPS.add(chat.id)
    else:
        UNIQUE_PRIVATE_CHATS.add(chat.id)

    bucket = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:00")
    ACTIVITY_BUCKETS[bucket] = ACTIVITY_BUCKETS.get(bucket, 0) + 1

    # حفظ الإحصائيات بعد كل رسالة
    save_stats()

    # ===== لعبة تحدي/صراحة - إنشاء جلسة جديدة =====
    if normalized in ["تحدي", "صراحه", "تحدي او صراحه", "تحدي ولا صراحه"]:
        game = context.chat_data.get("truth_dare_game")
        if game and game.get("status") in ("collecting", "running"):
            await update.message.reply_text("هناك لعبة تحدي/صراحة تعمل بالفعل في هذا القروب 🎮")
            return

        context.chat_data["truth_dare_game"] = {
            "status": "collecting",
            "starter_id": user.id,
            "participants": {},
            "remaining_players": [],
            "current_player_id": None,
            "current_round": None,
        }

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ انضمام للعبة", callback_data="td_join")]
        ])

        msg = await update.message.reply_text(
            "🕹 *جولة جديدة: تحدي أو صراحة*\n"
            "اضغط على الزر بالأسفل للانضمام للعبة خلال دقيقة واحدة ⏱",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

        context.chat_data["truth_dare_game"]["join_message_id"] = msg.message_id

        if context.job_queue:
            context.job_queue.run_once(
                td_close_join_phase,
                when=60,
                chat_id=chat.id,
                name=f"td_join_{chat.id}",
            )

        return

    # ===== نصوص معينة =====
    if normalized in ["العاب", "الالعاب"]:
        await update.message.reply_text(GAMES_HELP_TEXT, parse_mode="Markdown")
        return

    # ===== ردود سريعة من ملف autoreplies =====
    if AUTOREPLIES:
        reply = AUTOREPLIES.get(normalized)
        if reply:
            await update.message.reply_text(reply)
            return

    # ===== الألعاب =====

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

    # طلب إجابة
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
# Dashboard (Professional UI)
# =============================
DASHBOARD_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8" />
<title>لوحة تحكم البوت</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    padding: 20px;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: radial-gradient(circle at top, #1d2433, #020617);
    color: #e5e7eb;
}
.container { max-width: 1100px; margin: 0 auto; }
h1 {
    margin-bottom: 4px;
    font-size: 1.8rem;
    color: #60a5fa;
    text-shadow: 0 0 14px rgba(59,130,246,0.8);
}
.subtitle { color:#9ca3af; margin-bottom: 20px; }
.grid {
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
    gap:16px; margin-top:20px;
}
.card {
    background: linear-gradient(135deg, #020617, #0b1120);
    padding:16px;
    border-radius:18px;
    border:1px solid rgba(148,163,184,0.2);
    box-shadow:0 18px 40px rgba(15,23,42,0.8);
}
.card-title { color:#9ca3af; font-size:0.9rem; }
.card-value { font-size:1.7rem; margin-top:4px; font-weight:600; }
.badge {
    display:inline-block;
    padding:3px 10px;
    border-radius:999px;
    font-size:0.75rem;
    background:rgba(56,189,248,0.15);
    color:#38bdf8;
    border:1px solid rgba(56,189,248,0.4);
}
.chart-card {
    background:#020617;
    padding:20px;
    border-radius:18px;
    margin-top:26px;
    border:1px solid rgba(51,65,85,0.8);
    box-shadow:0 10px 35px rgba(15,23,42,0.9);
}
.login-box {
    max-width:350px;
    margin:160px auto;
    padding:25px;
    background:#020617;
    border-radius:16px;
    text-align:center;
    box-shadow:0 22px 60px rgba(15,23,42,0.95);
    border:1px solid rgba(55,65,81,0.9);
}
.login-title { margin-bottom:12px; color:#e5e7eb; font-size:1.3rem; }
.login-input {
    width:100%;
    padding:10px;
    border-radius:10px;
    border:1px solid #1f2937;
    background:#020617;
    color:#e5e7eb;
    margin-bottom:10px;
}
.login-btn {
    margin-top:4px;
    padding:10px;
    width:100%;
    border:none;
    border-radius:10px;
    background:linear-gradient(135deg,#2563eb,#38bdf8);
    color:white;
    cursor:pointer;
    font-weight:600;
}
.login-btn:hover {
    filter:brightness(1.05);
}
.footer {
    margin-top:26px;
    font-size:0.8rem;
    color:#6b7280;
    text-align:left;
}
.footer a { color:#93c5fd; text-decoration:none; }
.footer a:hover { text-decoration:underline; }
</style>
</head>
<body>

{% if not authorized %}
<div class="login-box">
    <div class="login-title">🔐 تسجيل الدخول للوحة التحكم</div>
    <form action="/dashboard">
        <input class="login-input" type="password" name="key" placeholder="كلمة المرور" />
        <button class="login-btn">دخول</button>
    </form>
</div>
{% else %}
<div class="container">
    <h1>لوحة تحكم البوت</h1>
    <div class="subtitle">
        مراقبة نشاط البوت والإحصائيات العامة. <span class="badge">LIVE</span>
    </div>

    <div class="grid">
        <div class="card">
            <div class="card-title">إجمالي الرسائل المستلمة</div>
            <div class="card-value">{{ messages }}</div>
        </div>
        <div class="card">
            <div class="card-title">عدد المستخدمين</div>
            <div class="card-value">{{ unique_users }}</div>
        </div>
        <div class="card">
            <div class="card-title">عدد الجروبات</div>
            <div class="card-value">{{ groups }}</div>
        </div>
        <div class="card">
            <div class="card-title">المحادثات الخاصة</div>
            <div class="card-value">{{ private_chats }}</div>
        </div>
        <div class="card">
            <div class="card-title">مدة التشغيل الحالية</div>
            <div class="card-value">{{ uptime }}</div>
        </div>
    </div>

    <div class="chart-card">
        <canvas id="chart"></canvas>
    </div>

    <div class="footer">
        المطور: <a href="https://t.me/R_q1j" target="_blank">@R_q1j</a>
    </div>
</div>

<script>
const labels = {{ labels | tojson }};
const dataPoints = {{ data | tojson }};

new Chart(document.getElementById("chart"), {
    type: 'line',
    data: {
        labels: labels,
        datasets: [{
            label: 'النشاط (عدد الرسائل لكل ساعة)',
            data: dataPoints,
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56,189,248,0.18)',
            borderWidth: 2,
            pointRadius: 3,
            tension: 0.35,
            fill: true,
        }]
    },
    options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
            x: { grid: { display:false } },
            y: { beginAtZero:true, grid:{ color:'rgba(55,65,81,0.6)' } }
        }
    }
});
</script>
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

    uptime_sec = int(time.time() - BOT_START_TIME)
    hours, rem = divmod(uptime_sec, 3600)
    mins, secs = divmod(rem, 60)
    uptime = f"{hours}h {mins}m {secs}s"

    # آخر 16 ساعة من النشاط
    buckets = sorted(ACTIVITY_BUCKETS.items())[-16:]
    labels = [b[0][-5:] for b in buckets]  # HH:00
    data = [b[1] for b in buckets]

    return render_template_string(
        DASHBOARD_TEMPLATE,
        authorized=True,
        unique_users=len(UNIQUE_USERS),
        groups=len(UNIQUE_GROUPS),
        private_chats=len(UNIQUE_PRIVATE_CHATS),
        messages=TOTAL_MESSAGES,
        uptime=uptime,
        labels=labels,
        data=data,
    )

# =============================
# INIT BOT (مشترك بين الوضعين)
# =============================
request_httpx = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)

app = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .request(request_httpx)
    .build()
)

# Register Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("developer", developer))
app.add_handler(CommandHandler("games", games))
app.add_handler(CommandHandler("podcast", podcast_broadcast))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === Truth/Dare Callback Handlers (جديدة) ===
app.add_handler(CallbackQueryHandler(td_join_callback, pattern="^td_join$"))
app.add_handler(CallbackQueryHandler(td_start_callback, pattern="^td_start$"))
app.add_handler(CallbackQueryHandler(td_choose_callback, pattern="^td_choose:"))
app.add_handler(CallbackQueryHandler(td_switch_callback, pattern="^td_switch:"))
app.add_handler(CallbackQueryHandler(td_next_callback, pattern="^td_next$"))

# =====================================================
# 🔵 Webhook Mode (للإنتاج على Render) - RUN_MODE=webhook
# =====================================================
if RUN_MODE == "webhook":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def init_and_set_webhook():
        await app.initialize()
        await app.start()
        await app.bot.delete_webhook()
        await app.bot.set_webhook(url=WEBHOOK_URL)

    loop.run_until_complete(init_and_set_webhook())

    @web_app.route("/webhook", methods=["POST"])
    def webhook_receiver():
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, app.bot)
        loop.run_until_complete(app.process_update(update))
        return "OK", 200

# =====================================================
# 🟢 Polling Mode (للتجربة محليًا) - RUN_MODE=polling
# =====================================================
if __name__ == "__main__" and RUN_MODE == "polling":
    print("▶️ Test Bot running with polling...")
    app.run_polling()

