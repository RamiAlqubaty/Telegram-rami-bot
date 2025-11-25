from typing import Any, Dict, Optional
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask, request, render_template_string
from datetime import datetime, timezone
import threading
import requests
import random
import os
import time

# =============================
# Dashboard Login Password
# =============================
DASHBOARD_PASS = os.getenv("DASHBOARD_PASS", "Rami24545")  # كلمة المرور

# =============================
# Bot Statistics
# =============================
TOTAL_MESSAGES = 0
UNIQUE_USERS: set[int] = set()
UNIQUE_GROUPS: set[int] = set()
UNIQUE_PRIVATE_CHATS: set[int] = set()
ACTIVITY_BUCKETS: Dict[str, int] = {}  # النشاط لكل ساعة

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
    "لعبة أسئلة شخصية ممتعة.\n"
    "الأمر: `كتت`\n\n"
    "2️⃣ *عام*\n"
    "ألغاز وأسئلة عامة.\n"
    "الأمر: `عام`\n\n"
    "3️⃣ *لو*\n"
    "لو خيروك.\n"
    "الأمر: `لو`\n\n"
    "4️⃣ *من*\n"
    "أسئلة من هو؟\n"
    "الأمر: `من`\n\n"
    "5️⃣ *جريمة*\n"
    "قصة جريمة تحاول حلّها.\n"
    "الأمر: `جريمة`\n\n"
    "6️⃣ *حل الجريمة*\n"
    "الأوامر: `حل الجريمة` أو `حل`.\n\n"
    "7️⃣ *حقائق*\n"
    "حقائق عشوائية.\n"
    "الأمر: `حقائق`\n\n"
    "✨ لعرض القائمة: (العاب)"
)

# =============================
# Load Auto Replies
# =============================
def load_auto_replies(filename="autoreplies.txt"):
    replies: Dict[str, str] = {}
    if not os.path.exists(filename):
        return replies
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                k, v = line.strip().split("|", 1)
                replies[k.strip()] = v.strip()
    return replies

AUTO_REPLIES = load_auto_replies()

# =============================
# Load Files Helpers
# =============================
def load_list_file(filename: str):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def load_general_questions(filename: str):
    if not os.path.exists(filename):
        return []
    data: list[tuple[str, str]] = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                q, a = line.strip().split("|", 1)
                data.append((q, a))
    return data

# =============================
# Load Game Files
# =============================
KT_QUESTIONS = load_list_file("questions.txt")
GENERAL_RIDDLES = load_general_questions("general_riddles.txt")
WOULD_YOU_RATHER = load_list_file("would_you_rather.txt")
WHO_QUESTIONS = load_list_file("who.txt")
CRIMES = load_list_file("crimes.txt")
FACTS = load_list_file("facts.txt")

# Defaults
if not KT_QUESTIONS:
    KT_QUESTIONS = ["كم عمرك؟", "ما هوايتك؟"]

if not GENERAL_RIDDLES:
    GENERAL_RIDDLES = [("ما عاصمة فرنسا؟", "باريس")]

if not WOULD_YOU_RATHER:
    WOULD_YOU_RATHER = ["لو خيروك تعيش غني أو فقير مع من تحب؟"]

if not WHO_QUESTIONS:
    WHO_QUESTIONS = ["من أكثر شخص يعجبك بالقروب؟"]

if not CRIMES:
    CRIMES = ["رجل مات في غرفة مغلقة | مات بسكتة قلبية"]

if not FACTS:
    FACTS = ["الحقيقة ليست دائمًا ما نراه، بل ما نفهمه."]

# Used Questions Tracking
def load_used(filename: str):
    if not os.path.exists(filename):
        return set()
    with open(filename, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_used(filename: str, value: str):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(value + "\n")

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
    t = t.strip().lower()
    return (
        t.replace("أ", "ا")
         .replace("إ", "ا")
         .replace("آ", "ا")
         .replace("ة", "ه")
    )

def is_answer_word(t: str):
    return normalize_text(t) in ["اجابه", "الاجابه", "جواب"]

# =============================
# Bot Commands
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_START_TIME
    assert update.message is not None
    BOT_START_TIME = time.time()
    await update.message.reply_text(
        "تم تفعيل البوت 👋\n"
        "الأوامر:\nكتت - عام - لو - من - جريمة - حقائق - حل الجريمة - العاب"
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assert update.message is not None
    await update.message.reply_text("الأوامر:\nكتت - عام - لو - من - جريمة - حقائق")

async def developer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assert update.message is not None
    await update.message.reply_text(
        f"المطور:\n{DEVELOPER_NAME}\n{DEVELOPER_USERNAME}\n{DEVELOPER_LINK}"
    )

async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assert update.message is not None
    await update.message.reply_text(GAMES_HELP_TEXT, parse_mode="Markdown")

# =============================
# Handle Messages + Statistics
# =============================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            global TOTAL_MESSAGES, ACTIVITY_BUCKETS

            if update.message is None or update.message.text is None:
                return

            message_time = update.message.date.timestamp()
            if message_time < BOT_START_TIME:
                return

            assert context.user_data is not None
            user_data: Dict[str, Any] = context.user_data

            text = update.message.text.strip()

            # statistics
            TOTAL_MESSAGES += 1

            user = update.message.from_user
            chat = update.message.chat

            if user:
                UNIQUE_USERS.add(user.id)

            if chat.type in ("group", "supergroup"):
                UNIQUE_GROUPS.add(chat.id)
            else:
                UNIQUE_PRIVATE_CHATS.add(chat.id)

            # activity per hour
            bucket = datetime.utcnow().strftime("%Y-%m-%d %H:00")
            ACTIVITY_BUCKETS[bucket] = ACTIVITY_BUCKETS.get(bucket, 0) + 1

            # remove bot mentions
            if "@" in text:
                text = text.split("@")[0].strip()

            normalized = normalize_text(text)

            # auto replies
            for key, reply in AUTO_REPLIES.items():
                if normalized.startswith(normalize_text(key)):
                    await update.message.reply_text(reply)
                    return

            # games list
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

                user_data["last_riddle_q"] = q
                user_data["last_riddle_a"] = a

                await update.message.reply_text(q)
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
                    user_data["crime_story"] = story.strip()
                    user_data["crime_solution"] = sol.strip()
                    await update.message.reply_text(story.strip())
                else:
                    await update.message.reply_text(c)
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
                await update.message.reply_text(f"🧠 حقيقة:\n{f}")
                return

            # حل الجريمة
            if normalized in ["حل الجريمة", "حل", "اجابة الجريمة"]:
                if "crime_solution" in user_data:
                    await update.message.reply_text(f"🔍 حل الجريمة:\n{user_data['crime_solution']}")
                else:
                    await update.message.reply_text("لا توجد جريمة حالياً.")
                return

            # إجابة
            if is_answer_word(text):
                if "last_riddle_a" in user_data:
                    await update.message.reply_text(
                        f"السؤال:\n{user_data['last_riddle_q']}\n\n"
                        f"الإجابة:\n{user_data['last_riddle_a']}"
                    )
                else:
                    await update.message.reply_text("لا يوجد سؤال سابق.")
                return

            # Correct answer?
            if "last_riddle_a" in user_data:
                if normalize_text(text) == normalize_text(user_data["last_riddle_a"]):
                    await update.message.reply_text("✔ إجابتك صحيحة!")
                return



# =============================
# Dashboard HTML (Dark + Neon)
# =============================
DASHBOARD_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8" />
<title>لوحة تحكم البوت</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {
    background:#050816;
    color:#e0e7ff;
    font-family: "Segoe UI", Arial;
    padding:20px;
}
.container { max-width:1100px; margin:auto; }
h1 { color:#60a5fa; text-shadow:0 0 12px #38bdf8; }
.grid {
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
    gap:16px; margin-top:20px;
}
.card {
    background: radial-gradient(circle at top left,#0f172a,#020617);
    padding:16px;
    border-radius:18px;
    box-shadow:0 0 1px #2563eb,0 6px 20px rgba(0,0,0,0.6);
}
.card-title { color:#9ca3af; font-size:0.9rem; }
.card-value { font-size:1.7rem; margin-top:4px; }
.chart-card {
    background:#020617;
    padding:20px;
    border-radius:16px;
    margin-top:30px;
}
.login-box {
    max-width:350px;
    margin:140px auto;
    padding:25px;
    background:#0f172a;
    border-radius:14px;
    text-align:center;
    box-shadow:0 0 20px rgba(30,58,138,0.5);
}
.login-input {
    width:100%;
    padding:10px;
    border-radius:8px;
    border:1px solid #1e3a8a;
    background:#000814;
    color:white;
}
.login-btn {
    margin-top:10px;
    padding:10px;
    width:100%;
    border:none;
    border-radius:8px;
    background:#2563eb;
    color:white;
    cursor:pointer;
}
</style>
</head>
<body>

{% if not authorized %}
<div class="login-box">
    <h2>تسجيل الدخول</h2>
    <form action="/dashboard">
        <input class="login-input" type="password" name="key" placeholder="كلمة المرور" />
        <button class="login-btn">دخول</button>
    </form>
</div>
{% else %}

<div class="container">
<h1>لوحة تحكم البوت</h1>

<div class="grid">
    <div class="card">
        <div class="card-title">المستخدمون</div>
        <div class="card-value">{{ unique_users }}</div>
    </div>
    <div class="card">
        <div class="card-title">الجروبات</div>
        <div class="card-value">{{ groups }}</div>
    </div>
    <div class="card">
        <div class="card-title">الخاص</div>
        <div class="card-value">{{ private_chats }}</div>
    </div>
    <div class="card">
        <div class="card-title">الرسائل</div>
        <div class="card-value">{{ messages }}</div>
    </div>
    <div class="card">
        <div class="card-title">Uptime</div>
        <div class="card-value">{{ uptime }}</div>
    </div>
</div>

<div class="chart-card">
    <canvas id="chart"></canvas>
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
            label: 'النشاط',
            data: dataPoints,
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56,189,248,0.15)',
            tension: 0.4,
            fill: true
        }]
    },
    options: { scales:{ y:{ beginAtZero:true } } }
});
</script>

{% endif %}

</body>
</html>
"""

# =============================
# Dashboard Routes
# =============================
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running 24/7!"

@web_app.route("/dashboard")
def dashboard():
    key = request.args.get("key", "")

    if key != DASHBOARD_PASS:
        return render_template_string(DASHBOARD_TEMPLATE, authorized=False)

    uptime_sec = int(time.time() - BOT_START_TIME)
    hours, rem = divmod(uptime_sec, 3600)
    mins, secs = divmod(rem, 60)
    uptime = f"{hours}h {mins}m {secs}s"

    # Last 16 hours of activity
    buckets = sorted(ACTIVITY_BUCKETS.items())[-16:]
    labels = [b[0][-5:] for b in buckets]  # show HH:00
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
        data=data
    )


def run_web_server():
    web_app.run(host="0.0.0.0", port=8080)

def internal_keepalive():
    while True:
        try:
            requests.get("http://localhost:8080/")
        except:
            pass
        time.sleep(300)

# =============================
# BOT Runner
# =============================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in Secrets!")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("developer", developer))
app.add_handler(CommandHandler("games", games))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

threading.Thread(target=run_web_server, daemon=True).start()
threading.Thread(target=internal_keepalive, daemon=True).start()

app.run_polling()
