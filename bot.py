import os
import sqlite3
import requests
import html

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= TOKEN =================
TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

if not TOKEN:
    raise Exception("BOT_TOKEN is missing")

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    title TEXT DEFAULT '🌱 جديد'
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS active_q (
    user_id INTEGER PRIMARY KEY,
    answer TEXT
)
""")

conn.commit()

# ================= TITLES =================
titles = [
    "🌿 مبتدئ",
    "⚡ متعلم",
    "🔥 نشيط",
    "🚀 متفاعل",
    "🎯 متقدم",
    "⭐ مميز",
    "🏅 محترف",
    "🥇 نجم",
    "👑 قائد",
    "💎 خبير",
    "🏆 أسطورة",
]

def get_title(messages):
    if messages <= 149:
        return "🌱 جديد"

    level = (messages - 150) // 100

    if level >= len(titles):
        return "💠 أسطورة عليا"

    return titles[level]

# ================= QUESTIONS =================
def get_question():
    try:
        url = "https://opentdb.com/api.php?amount=1&type=multiple"

        response = requests.get(url, timeout=5)
        data = response.json()

        result = data["results"][0]

        question = html.unescape(result["question"])
        answer = html.unescape(result["correct_answer"])

        return question, answer

    except:
        return "ما عاصمة العراق؟", "بغداد"

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك\n\n"
        "الأوامر:\n"
        "• معلوماتي\n"
        "• سؤال / سوال"
    )

# ================= MAIN =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    text = update.message.text

    if not text:
        return

    text = text.strip()

    user = update.effective_user
    uid = user.id
    name = user.first_name

    # ================= GET USER =================
    c.execute(
        "SELECT points,messages,title FROM users WHERE user_id=?",
        (uid,)
    )

    row = c.fetchone()

    if row:
        points, messages, title = row
    else:
        points = 0
        messages = 0
        title = "🌱 جديد"

        c.execute(
            "INSERT INTO users VALUES (?,?,?,?,?)",
            (uid, name, points, messages, title)
        )

        conn.commit()

    # ================= INFO =================
    if text == "معلوماتي":

        await update.message.reply_text(
            f"👤 اسمك: {name}\n"
            f"🔢 نقاطك: {points}\n"
            f"💬 رسائلك: {messages}\n"
            f"🏅 لقبك: {title}"
        )

        return

    # ================= QUESTION =================
    if text.lower() in ["سؤال", "سوال"]:

        question, answer = get_question()

        c.execute(
            "REPLACE INTO active_q VALUES (?,?)",
            (uid, answer)
        )

        conn.commit()

        await update.message.reply_text(
            f"❓ السؤال:\n\n{question}"
        )

        return

    # ================= CHECK ANSWER =================
    c.execute(
        "SELECT answer FROM active_q WHERE user_id=?",
        (uid,)
    )

    active = c.fetchone()

    if active:

        correct_answer = active[0]

        if text.lower() == correct_answer.lower():

            points += 5

            await update.message.reply_text(
                "✅ إجابة صحيحة +5 نقاط"
            )

        else:

            await update.message.reply_text(
                f"❌ إجابة خاطئة\n\n"
                f"✔ الجواب الصحيح: {correct_answer}"
            )

        c.execute(
            "DELETE FROM active_q WHERE user_id=?",
            (uid,)
        )

        conn.commit()

    # ================= UPDATE =================
    old_title = title

    messages += 1
    points += 1

    new_title = get_title(messages)

    c.execute("""
    UPDATE users
    SET points=?, messages=?, title=?, name=?
    WHERE user_id=?
    """, (points, messages, new_title, name, uid))

    conn.commit()

    # ================= LEVEL UP =================
    if new_title != old_title:

        if GROUP_ID != 0:

            try:
                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=
                    f"🎉 ترقية جديدة!\n\n"
                    f"👤 {name}\n"
                    f"🏅 اللقب: {new_title}\n"
                    f"💬 الرسائل: {messages}"
                )

            except:
                pass

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle
    )
)

print("🚀 BOT WORKING")

app.run_polling()
