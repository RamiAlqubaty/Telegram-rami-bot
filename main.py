from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import random
import os

# =========================
# إعدادات المطور
# =========================
DEVELOPER_NAME = "المطور"
DEVELOPER_USERNAME = "@R_BF4"
DEVELOPER_LINK = "https://t.me/R_BF4"

# =========================
# دوال تحميل الملفات
# =========================

def load_list_file(filename: str):
    """تحميل ملف يحتوي على قائمة أسئلة (سطر لكل سؤال)"""
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def load_general_questions(filename: str):
    """تحميل ملف الأسئلة العامة بصيغة: سؤال|إجابة"""
    if not os.path.exists(filename):
        return []
    data = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if "|" in line:
                q, a = line.strip().split("|", 1)
                data.append((q, a))
    return data

def load_wyr(filename: str):
    """تحميل أسئلة لو خيروك"""
    return load_list_file(filename)

# =========================
# تحميل ملفات الأسئلة
# =========================

KT_QUESTIONS = load_list_file("questions.txt")
GENERAL_RIDDLES = load_general_questions("general_riddles.txt")
WOULD_YOU_RATHER = load_wyr("would_you_rather.txt")

# قوائم افتراضية إذا لم توجد ملفات
if not KT_QUESTIONS:
    KT_QUESTIONS = ["كم عمرك؟", "ما هي هواياتك؟", "هل أنت شخص اجتماعي؟"]

if not GENERAL_RIDDLES:
    GENERAL_RIDDLES = [("ما عاصمة فرنسا؟", "باريس")]

if not WOULD_YOU_RATHER:
    WOULD_YOU_RATHER = ["لو خيروك تعيش غني أو فقير مع من تحب؟"]

# =========================
# ردود تلقائية
# =========================
AUTO_REPLIES = {
    "سلام": "وعليكم السلام ورحمة الله وبركاته 🌿",
    "السلام عليكم": "وعليكم السلام ورحمة الله وبركاته 🤍",
    "مرحبا": "مرحبا بك نورت 🌟",
    "اهلا": "أهلاً وسهلاً 🙌",
    "هلا": "هلا فيك 🤍",
    "شلونك": "تمام دامك بخير 🌿",
    "كيفكم": "تمام الحمدلله وانت؟ 😊",
    "كرستيانو": "عمك الدون",
    "عائشة": "فراشة القروب 🦋",
    "عائشه": "فراشة القروب 🦋",
    "رامي": "محور الكون",
    "جنى": "ام هوشات",
    "جنو": "ام هوشات",
    "هبه": "صغنونه القروب ",
    "زينب": " لطيفة القروب 💫",


}

# =========================
# دوال مساعدة
# =========================
def normalize_text(text: str) -> str:
    t = text.strip().lower()
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ة", "ه")
    return t

def is_answer_word(text: str):
    t = normalize_text(text)
    return t in ["اجابه", "الاجابه", "جواب"]

# =========================
# أوامر البوت
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "مرحبًا بك في بوت الأسئلة 👋\n\n"
        "الأوامر:\n"
        "- كتت → سؤال صراحة\n"
        "- عام → سؤال عام أو لغز\n"
        "- لو → سؤال لو خيروك\n"
        "- اجابة → لإظهار حل آخر سؤال عام\n\n"
        "يعمل البوت في القروبات بدون منشن."
    )
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "الأوامر:\nكتت - عام - لو - اجابة\n"
        "الردود التلقائية: سلام، مرحبا، هلا… إلخ"
    )

async def developer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"معلومات المطور:\n{DEVELOPER_NAME}\n{DEVELOPER_USERNAME}\n{DEVELOPER_LINK}"
    )

# =========================
# استقبال الرسائل
# =========================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_data = context.user_data

    # إزالة المنشن في القروبات
    if "@" in text:
        text = text.split("@")[0].strip()

    # ======================
    # الردود التلقائية
    normalized = normalize_text(text)
    for key in AUTO_REPLIES:
        if normalized.startswith(normalize_text(key)):
            await update.message.reply_text(AUTO_REPLIES[key])
            return

    # ======================
    # كتت
    if text == "كتت":
        q = random.choice(KT_QUESTIONS)
        await update.message.reply_text(q)
        return

    # ======================
    # عام
    if text == "عام":
        q, a = random.choice(GENERAL_RIDDLES)
        user_data["last_general_question"] = q
        user_data["last_general_answer"] = a
        await update.message.reply_text(q)
        return

    # ======================
    # لو
    if text == "لو":
        q = random.choice(WOULD_YOU_RATHER)
        await update.message.reply_text(q)
        return

    # ======================
    # اجابة
    if is_answer_word(text):
        if "last_general_answer" in user_data:
            q = user_data["last_general_question"]
            a = user_data["last_general_answer"]
            await update.message.reply_text(f"السؤال كان:\n{q}\n\nالإجابة:\n{a}")
        else:
            await update.message.reply_text("لا يوجد سؤال عام محفوظ.")
        return

    # ======================
    # التحقق من الإجابة
    if "last_general_answer" in user_data:
        if normalize_text(text) == normalize_text(user_data["last_general_answer"]):
            await update.message.reply_text("✔ إجابتك صحيحة!")
            return

    # ======================
    # رد افتراضي

# =========================
# تشغيل البوت
# =========================
app = ApplicationBuilder().token("8332331263:AAGMD6a5MoGkZ8s1OVeLqsY6x58OnM_Z2bc").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("developer", developer_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
