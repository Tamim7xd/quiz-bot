import os
import sqlite3
import random
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
name TEXT,
points INTEGER DEFAULT 0,
messages INTEGER DEFAULT 0,
title TEXT DEFAULT '🌱 عضو جديد',
locked INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS active_q (
user_id INTEGER PRIMARY KEY,
answer TEXT
)
""")

conn.commit()

# ================= STATE =================
state = {}
publish_log = []

# ================= TITLES (50) =================
TITLES = [
"🌱 مبتدئ","🌿 متعلم","⚡ نشيط","🔥 متفاعل","🚀 متقدم",
"🎯 محترف","⭐ مميز","🏅 بطل","🥇 نجم","👑 قائد",
"💎 خبير","🏆 أسطورة","⚔️ محارب","🛡️ حارس","🌟 سوبر",
"💥 خارق","🎮 لاعب","🧠 ذكي","📚 مثقف","🌍 رحّالة",
"💠 أسطورة عليا","🔥 Legend","⚡ Elite","👑 King","💎 Diamond",
"🚀 Pro","🎯 Sharp","⭐ Star","🏅 Hero","🥇 Champion",
"🧠 Genius","🔥 Master","⚔️ Fighter","🛡 Defender","🌟 Ultra",
"💥 Beast","🎮 Gamer","📚 Scholar","🌍 Explorer","💠 Myth",
"👑 Emperor","💎 Titan","🚀 Rocket","⚡ Flash","🔥 Omega",
"🏆 Supreme","🌟 Apex","💥 Ultra Pro","🎯 Final Boss","👑 God Mode"
]

# ================= QUESTIONS =================
QUESTIONS = [
("ما عاصمة العراق؟","بغداد"),
("ما عاصمة فرنسا؟","باريس"),
("ما أكبر دولة؟","روسيا"),
("ما أصغر دولة؟","الفاتيكان"),
("ما أطول نهر؟","النيل"),
("ما أكبر كوكب؟","المشتري"),
("ما غاز التنفس؟","الأكسجين"),
("كم عدد القارات؟","7"),
("ما قبلة المسلمين؟","الكعبة"),
("من أول نبي؟","آدم")
]

def get_question():
    return random.choice(QUESTIONS)

# ================= LEVEL =================
def get_level(points):
    return points // 200

def get_progress(points):
    return points % 200

def get_title(points):
    lvl = get_level(points)
    if lvl >= len(TITLES):
        return TITLES[-1]
    return TITLES[lvl]

def progress_bar(points):
    p = get_progress(points)
    bar = "█" * (p // 20) + "░" * (10 - p // 20)
    return f"[{bar}] {p}/200"

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?)", (uid, update.effective_user.first_name, 0, 0, "🌱 عضو جديد", 0))
        conn.commit()

    await update.message.reply_text("👋 أهلاً بك في البوت")

# ================= QUESTIONS =================
async def handle_question(update, context):
    uid = update.effective_user.id
    text = update.message.text

    if text in ["سؤال","سوال"]:
        q, a = get_question()
        c.execute("REPLACE INTO active_q VALUES (?,?)", (uid,a))
        conn.commit()
        await update.message.reply_text(f"❓ {q}")
        return

    # answer check
    c.execute("SELECT answer FROM active_q WHERE user_id=?", (uid,))
    row = c.fetchone()

    add = 1
    if row:
        if text.lower() == row[0].lower():
            add = 5
            await update.message.reply_text("✅ صحيح +5")
        else:
            await update.message.reply_text(f"❌ خطأ الإجابة {row[0]}")

        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

    # update user
    c.execute("SELECT points,messages,title,locked,name FROM users WHERE user_id=?", (uid,))
    p,m,t,l,name = c.fetchone()

    old = get_title(p)

    p += add
    m += 1

    new = get_title(p) if l==0 else t

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?", (p,m,new,uid))
    conn.commit()

    await update.message.reply_text(f"""
💰 نقاط: {p}
🎖 {new}
📊 {progress_bar(p)}
""")

    if old != new:
        await update.message.reply_text(f"🎉 ترقية: {new}")

# ================= ADMIN PANEL =================
async def admin(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("📢 نشر", callback_data="publish")],
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")]
    ]

    await update.message.reply_text("لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= PUBLISH =================
async def publish_panel(update, context):
    q = update.callback_query
    await q.answer()

    kb = [
        [InlineKeyboardButton("📝 نص", callback_data="p_text")],
        [InlineKeyboardButton("🖼 صورة", callback_data="p_photo")]
    ]

    await q.message.reply_text("📢 النشر", reply_markup=InlineKeyboardMarkup(kb))

# ================= TEXT PUBLISH =================
async def text_start(update, context):
    q = update.callback_query
    await q.answer()

    state[ADMIN_ID] = "text"
    await q.message.reply_text("✍️ أرسل النص")

# ================= HANDLE =================
async def handle(update, context):
    uid = update.effective_user.id
    text = update.message.text

    if uid == ADMIN_ID and ADMIN_ID in state:

        if state[ADMIN_ID] == "text":
            msg = await context.bot.send_message(GROUP_ID, f"📢 {text}")

            kb = [
                [InlineKeyboardButton("📌 تثبيت", callback_data=f"pin|{msg.message_id}")],
                [InlineKeyboardButton("➖ بدون", callback_data="nopin")]
            ]

            await update.message.reply_text("تم الإرسال", reply_markup=InlineKeyboardMarkup(kb))

            publish_log.append(text)
            state.pop(ADMIN_ID)
            return

    await handle_question(update, context)

# ================= PIN =================
async def pin(update, context):
    q = update.callback_query
    await q.answer()

    if q.data.startswith("pin"):
        msg_id = int(q.data.split("|")[1])

        await context.bot.pin_chat_message(GROUP_ID, msg_id)

        await q.message.reply_text("📌 تم التثبيت")

    else:
        await q.message.reply_text("✔ بدون تثبيت")

# ================= ROUTER =================
async def router(update, context):
    q = update.callback_query
    d = q.data

    if d == "publish":
        await publish_panel(update, context)

    if d == "p_text":
        await text_start(update, context)

    if d.startswith("pin") or d == "nopin":
        await pin(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING")
app.run_polling()
