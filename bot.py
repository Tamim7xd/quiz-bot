import os
import sqlite3
import random
import requests
import html

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ================= ENV =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

if not TOKEN:
    raise Exception("BOT_TOKEN is missing")

# ================= DB =================
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
    q TEXT,
    a TEXT
)
""")

conn.commit()

# ================= TITLES (50 LEVELS) =================
def get_title(msg):
    if msg <= 149:
        return "🌱 جديد"

    level = (msg - 150) // 100

    titles = [
        "🌿 مبتدئ","⚡ متعلم","🔥 نشيط","🚀 متفاعل","🎯 متقدم",
        "⭐ مميز","🏅 محترف","🥇 نجم","👑 قائد","💎 خبير",
        "🏆 أسطورة","⚔️ محارب","🛡️ حارس","🌟 سوبر ستار","💥 خارق",
        "🎮 لاعب","🧩 محلل","📚 مثقف","🌍 رحّالة","⚙️ عبقري",
        "🧿 نادر","👑 ملك","💠 أسطورة عليا"
    ]

    return titles[level] if level < len(titles) else "💠 أسطورة"

# ================= SAFE API QUESTION =================
def get_question():
    try:
        url = "https://opentdb.com/api.php?amount=1&type=multiple"
        r = requests.get(url, timeout=5).json()

        data = r["results"][0]
        q = html.unescape(data["question"])
        a = html.unescape(data["correct_answer"])

        return q, a

    except:
        return "ما هي عاصمة العراق؟", "بغداد"

# ================= MAIN =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك في البوت")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    name = user.first_name
    text = update.message.text

    # get user
    c.execute("SELECT points,messages,title FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()

    if not row:
        points, messages, title = 0, 0, "🌱 جديد"
        c.execute("INSERT INTO users VALUES (?,?,0,0,'🌱 جديد')", (uid,name))
        conn.commit()
    else:
        points, messages, title = row

    # ================= INFO =================
    if text == "معلوماتي":
        await update.message.reply_text(
f"""👤 معلوماتك
🔢 نقاط: {points}
💬 رسائل: {messages}
🏅 لقب: {title}"""
        )
        return

    # ================= QUESTION =================
    if text in ["سؤال", "سوال"]:
        q, a = get_question()

        c.execute("REPLACE INTO active_q VALUES (?,?,?)",(uid,q,a))
        conn.commit()

        await update.message.reply_text(f"❓ {q}")
        return

    # ================= ANSWER =================
    c.execute("SELECT a FROM active_q WHERE user_id=?", (uid,))
    active = c.fetchone()

    if active:
        correct = active[0]

        if text.lower() == correct.lower():
            points += 5
            await update.message.reply_text("✅ صحيح +5")
        else:
            await update.message.reply_text(f"❌ خطأ\nالإجابة: {correct}")

        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

    # ================= UPDATE STATS =================
    old_title = title

    messages += 1
    points += 1

    new_title = get_title(messages)

    c.execute("""
        UPDATE users
        SET points=?, messages=?, title=?
        WHERE user_id=?
    """, (points, messages, new_title, uid))

    conn.commit()

    # ================= LEVEL UP ANNOUNCE =================
    if new_title != old_title:
        try:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"""🎉 ترقية جديدة!

👤 {name}
🏅 {new_title}
💬 {messages} رسالة"""
            )
        except:
            pass

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🚀 BOT RUNNING")
app.run_polling()
