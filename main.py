from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import random
import os
import time

# =============================
# إعدادات المطور
# =============================
DEVELOPER_NAME = "المطور"
DEVELOPER_USERNAME = "@R_BF4"
DEVELOPER_LINK = "https://t.me/R_BF4"


# =============================
# نص قائمة الألعاب
# =============================
GAMES_HELP_TEXT = (
    "🎮 *قائمة الألعاب الموجودة في البوت:*\n\n"
    "1️⃣ *كتت*\n"
    "لعبة أسئلة شخصية ممتعة.\n"
    "الأمر المستخدم: `كتت`\n\n"
    "2️⃣ *عام*\n"
    "أسئلة عامة وألغاز، ويمكنك طلب الإجابة بكتابة كلمة (اجابة).\n"
    "الأمر المستخدم: `عام`\n\n"
    "3️⃣ *لو*\n"
    "لعبة لو خيروك، أسئلة اختيار بين شيئين.\n"
    "الأمر المستخدم: `لو`\n\n"
    "4️⃣ *من*\n"
    "أسئلة من هو؟ مثل: من أكثر شخص يعجبك بالقروب؟\n"
    "الأمر المستخدم: `من`\n\n"
    "5️⃣ *جريمة*\n"
    "لعبة جريمة غامضة، يعطيك القصة وتحاول تحلها.\n"
    "الأمر المستخدم: `جريمة`\n\n"
    "6️⃣ *حل الجريمة*\n"
    "تستخدمها بعد ما يعطيك البوت جريمة، عشان يجيب لك الحل.\n"
    "الأوامر: `حل الجريمة` أو `حل` أو `اجابة الجريمة`\n\n"
    "7️⃣ *حقائق*\n"
    "لعبة الحقائق: يرسل لك حقيقة عشوائية.\n"
    "الأمر المستخدم: `حقائق`\n\n"
    "✨ لعرض القائمة من جديد: اكتب (العاب) أو (الالعاب)."
)


# =============================
# تحميل الردود التلقائية
# =============================
def load_auto_replies(filename="autoreplies.txt"):
    replies = {}
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
# دوال تحميل الملفات
# =============================
def load_list_file(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_general_questions(filename):
    if not os.path.exists(filename):
        return []
    data = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                q, a = line.strip().split("|", 1)
                data.append((q, a))
    return data


# =============================
# تحميل الملفات
# =============================
KT_QUESTIONS = load_list_file("questions.txt")
GENERAL_RIDDLES = load_general_questions("general_riddles.txt")
WOULD_YOU_RATHER = load_list_file("would_you_rather.txt")
WHO_QUESTIONS = load_list_file("who.txt")
CRIMES = load_list_file("crimes.txt")
FACTS = load_list_file("facts.txt")

# قوائم افتراضية
if not KT_QUESTIONS:
    KT_QUESTIONS = ["كم عمرك؟", "ما هي هواياتك؟"]

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


# =============================
# حفظ الأسئلة المستخدمة
# =============================
def load_used(filename):
    if not os.path.exists(filename):
        return set()
    with open(filename, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_used(filename, value):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(value + "\n")


USED_KT = load_used("used_kt.txt")
USED_GENERAL = load_used("used_general.txt")
USED_WYR = load_used("used_wyr.txt")
USED_WHO = load_used("used_who.txt")
USED_CRIMES = load_used("used_crimes.txt")
USED_FACTS = load_used("used_facts.txt")


# =============================
# تجاهل الرسائل القديمة
# =============================
BOT_START_TIME = time.time()


# =============================
# دوال مساعدة
# =============================
def normalize_text(t):
    t = t.strip().lower()
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه")
    return t


def is_answer_word(text):
    return normalize_text(text) in ["اجابه", "الاجابه", "جواب"]


# =============================
# أوامر البوت
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_START_TIME
    BOT_START_TIME = time.time()
    await update.message.reply_text(
        "تم تفعيل البوت 👋\n"
        "الأوامر:\nكتت - عام - لو - من - جريمة - حقائق - حل الجريمة - العاب"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("الأوامر: كتت - عام - لو - من - جريمة - حقائق - حل الجريمة - العاب")


async def developer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"المطور:\n{DEVELOPER_NAME}\n{DEVELOPER_USERNAME}\n{DEVELOPER_LINK}"
    )


async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        GAMES_HELP_TEXT,
        parse_mode="Markdown"
    )


# =============================
# استقبال الرسائل
# =============================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message_time = update.message.date.timestamp()
    text = update.message.text.strip()
    user_data = context.user_data

    if message_time < BOT_START_TIME:
        return

    if "@" in text:
        text = text.split("@")[0].strip()

    normalized = normalize_text(text)

    # ===== الردود التلقائية =====
    for key, reply in AUTO_REPLIES.items():
        if normalized.startswith(normalize_text(key)):
            await update.message.reply_text(reply)
            return

    # ===== قائمة الألعاب =====
    if normalized in ["العاب", "الالعاب"]:
        await update.message.reply_text(
            GAMES_HELP_TEXT,
            parse_mode="Markdown"
        )
        return

    # ===== كتت =====
    if text == "كتت":
        remaining = [q for q in KT_QUESTIONS if q not in USED_KT]
        if not remaining:
            USED_KT.clear(); open("used_kt.txt", "w").close(); remaining = KT_QUESTIONS.copy()
        q = random.choice(remaining)
        USED_KT.add(q); save_used("used_kt.txt", q)
        await update.message.reply_text(q)
        return

    # ===== عام =====
    if text == "عام":
        remaining = [(q, a) for (q, a) in GENERAL_RIDDLES if q not in USED_GENERAL]
        if not remaining:
            USED_GENERAL.clear(); open("used_general.txt", "w").close(); remaining = GENERAL_RIDDLES.copy()
        q, a = random.choice(remaining)
        USED_GENERAL.add(q); save_used("used_general.txt", q)
        user_data["last_general_question"] = q
        user_data["last_general_answer"] = a
        await update.message.reply_text(q)
        return

    # ===== لو =====
    if text == "لو":
        remaining = [q for q in WOULD_YOU_RATHER if q not in USED_WYR]
        if not remaining:
            USED_WYR.clear(); open("used_wyr.txt", "w").close(); remaining = WOULD_YOU_RATHER.copy()
        q = random.choice(remaining)
        USED_WYR.add(q); save_used("used_wyr.txt", q)
        await update.message.reply_text(q)
        return

    # ===== من =====
    if text == "من":
        remaining = [q for q in WHO_QUESTIONS if q not in USED_WHO]
        if not remaining:
            USED_WHO.clear(); open("used_who.txt", "w").close(); remaining = WHO_QUESTIONS.copy()
        q = random.choice(remaining)
        USED_WHO.add(q); save_used("used_who.txt", q)
        await update.message.reply_text(q)
        return

    # ===== جريمة =====
    if text == "جريمة":
        remaining = [c for c in CRIMES if c not in USED_CRIMES]
        if not remaining:
            USED_CRIMES.clear(); open("used_crimes.txt", "w").close(); remaining = CRIMES.copy()

        crime = random.choice(remaining)
        USED_CRIMES.add(crime); save_used("used_crimes.txt", crime)

        if "|" in crime:
            story, solution = crime.split("|", 1)
            user_data["crime_story"] = story.strip()
            user_data["crime_solution"] = solution.strip()
            await update.message.reply_text(story.strip())
        else:
            await update.message.reply_text(crime)
        return

    # ===== حقائق =====
    if text == "حقائق":
        remaining = [f for f in FACTS if f not in USED_FACTS]

        if not remaining:
            USED_FACTS.clear()
            open("used_facts.txt", "w").close()
            remaining = FACTS.copy()

        fact = random.choice(remaining)
        USED_FACTS.add(fact)
        save_used("used_facts.txt", fact)

        await update.message.reply_text(f"🧠 حقيقة:\n{fact}")
        return

    # ===== حل الجريمة =====
    if normalized in ["حل الجريمة", "حل", "اجابة الجريمة"]:
        if "crime_solution" in user_data:
            await update.message.reply_text(
                f"🔍 حل الجريمة:\n{user_data['crime_solution']}"
            )
        else:
            await update.message.reply_text("لا توجد جريمة لحلها الآن.")
        return

    # ===== اجابة =====
    if is_answer_word(text):
        if "last_general_answer" in user_data:
            await update.message.reply_text(
                f"السؤال كان:\n{user_data['last_general_question']}\n\n"
                f"الإجابة:\n{user_data['last_general_answer']}"
            )
        else:
            await update.message.reply_text("لا يوجد سؤال سابق.")
        return

    # ===== التحقق من إجابة لعبة عام =====
    if "last_general_answer" in user_data:
        if normalize_text(text) == normalize_text(user_data["last_general_answer"]):
            await update.message.reply_text("✔ إجابتك صحيحة!")
        return


# =============================
# تشغيل البوت
# =============================
app = ApplicationBuilder().token("8332331263:AAGMD6a5MoGkZ8s1OVeLqsY6x58OnM_Z2bc").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("developer", developer_command))
app.add_handler(CommandHandler("games", games_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
