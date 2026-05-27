import os
import sqlite3
import random
import traceback
import requests
import html

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

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

c.execute("""
CREATE TABLE IF NOT EXISTS used_questions (
    q TEXT PRIMARY KEY
)
""")

conn.commit()

# ================= TITLES (50 LEVELS) =================
def get_title_by_messages(msg):

    if msg <= 149:
        return "🌱 جديد"

    level = (msg - 150) // 100

    titles = [
        "🌿 مبتدئ","⚡ متعلم","🔥 نشيط","🚀 متفاعل","🎯 متقدم",
        "⭐ مميز","🏅 محترف","🥇 نجم","👑 قائد","💎 خبير",
        "🏆 أسطورة","⚔️ محارب","🛡️ حارس","🌟 سوبر ستار","💥 خارق",
        "🎮 لاعب","🧩 محلل","📚 مثقف","🌍 رحّالة","⚙️ عبقري",
        "🧿 نادر","👑 ملك","💠 أسطورة عليا","🔥 Legend X","⚡ Ultra Pro",
        "🚀 Elite","🏆 Titan","💎 Diamond","👑 King Pro","🌟 Mythic",
        "⚔️ Warrior X","🧠 Genius","💥 Destroyer","🎯 Sharp","🏅 Master Pro",
        "🥇 Gold Elite","💠 Crystal","🔥 Inferno","🚀 Rocket","⚡ Storm",
        "🌍 Explorer","👑 Supreme","🏆 Eternal","💎 Divine","🔥 God Mode",
        "🌟 Infinity","⚔️ Final Boss"
    ]

    if level < len(titles):
        return titles[level]
    else:
        return "💠 Ultimate Legend"

# ================= API QUESTION =================
def get_api_question():
    url = "https://opentdb.com/api.php?amount=1&type=multiple"
    r = requests.get(url).json()

    data = r["results"][0]

    question = html.unescape(data["question"])
    answer = html.unescape(data["correct_answer"])

    return question, answer

# ================= HELPERS =================
def get_user(uid, name):
    c.execute("SELECT points,messages,title FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()

    if not row:
        c.execute("INSERT INTO users VALUES (?,?,0,0,'🌱 جديد')", (uid,name))
        conn.commit()
        return 0,0,"🌱 جديد"

    return row

def save_user(uid, name, p, m, t):
    c.execute("UPDATE users SET name=?,points=?,messages=?,title=? WHERE user_id=?",
              (name,p,m,t,uid))
    conn.commit()

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = [[InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="panel")]]
        await update.message.reply_text("🔥 أهلاً أدمن", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text("👋 أهلاً بك\nاكتب: معلوماتي / سؤال")

# ================= CALLBACK =================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return

    if q.data == "panel":
        kb = [[InlineKeyboardButton("👥 الأعضاء", callback_data="users")]]
        await q.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= MAIN =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        uid = user.id
        name = user.first_name
        text = update.message.text

        points, messages, title = get_user(uid, name)

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

            while True:
                q, a = get_api_question()

                c.execute("SELECT q FROM used_questions WHERE q=?", (q,))
                if not c.fetchone():
                    break

            c.execute("INSERT INTO used_questions VALUES (?)", (q,))
            conn.commit()

            c.execute("REPLACE INTO active_q VALUES (?,?,?)",(uid,q,a))
            conn.commit()

            await update.message.reply_text(f"❓ {q}")
            return

        # ================= ANSWER =================
        c.execute("SELECT q,a FROM active_q WHERE user_id=?", (uid,))
        active = c.fetchone()

        if active:
            correct = active[1]

            if text.lower() == correct.lower():
                await update.message.reply_text("✅ صحيح +5")
                points += 5
            else:
                await update.message.reply_text(f"❌ خطأ: {correct}")

            c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
            conn.commit()

        # ================= UPDATE =================
        old = title

        points += 1
        messages += 1

        new = get_title_by_messages(messages)

        save_user(uid,name,points,messages,new)

        # ================= GLOBAL LEVEL UP =================
        if new != old:
            try:
                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=f"""🎉 ترقية جديدة!

👤 {name}
🏅 {new}
💬 {messages} رسالة"""
                )
            except:
                pass

    except Exception:
        print(traceback.format_exc())

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🚀 BOT FULL READY RUNNING")
app.run_polling()
