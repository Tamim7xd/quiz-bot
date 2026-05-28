import os
import sqlite3
import random
from datetime import datetime

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
CREATE TABLE IF NOT EXISTS admins (
user_id INTEGER PRIMARY KEY
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS logs (
id INTEGER PRIMARY KEY AUTOINCREMENT,
text TEXT,
time TEXT
)
""")

conn.commit()

# ================= STATE =================
state = {}

# ================= TITLES =================
TITLES = [
"🌱 مبتدئ","🌿 متعلم","⚡ نشيط","🔥 متفاعل","🚀 متقدم",
"🎯 محترف","⭐ مميز","🏅 بطل","🥇 نجم","👑 قائد",
"💎 خبير","🏆 أسطورة","⚔️ محارب","🛡️ حارس","🌟 سوبر",
"💥 خارق","🎮 لاعب","🧠 ذكي","📚 مثقف","🌍 رحّالة",
"💠 أسطورة","🔥 Legend","⚡ Elite","👑 King","💎 Diamond",
"🚀 Pro","🎯 Sharp","⭐ Star","🏅 Hero","🥇 Champ",
"🧠 Genius","🔥 Master","⚔️ Fighter","🛡 Defender","🌟 Ultra",
"💥 Beast","🎮 Gamer","📚 Scholar","🌍 Explorer","💠 Myth",
"👑 Emperor","💎 Titan","🚀 Rocket","⚡ Flash","🔥 Omega",
"🏆 Supreme","🌟 Apex","🎯 Boss","👑 GOD","💎 Final"
]

# ================= SYSTEM =================
def register(uid, name):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",
                  (uid, name, 0, 0, "🌱 عضو جديد", 0))
        conn.commit()

def level(points):
    return points // 200

def progress(points):
    return points % 200

def title(points):
    lvl = level(points)
    return TITLES[lvl] if lvl < len(TITLES) else TITLES[-1]

def log(action):
    c.execute("INSERT INTO logs (text,time) VALUES (?,?)",
              (action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text("👋 أهلاً بك")

# ================= ADMIN CHECK =================
def is_admin(uid):
    return uid == ADMIN_ID

# ================= MAIN ADMIN PANEL =================
async def admin(update: Update, context):
    if not is_admin(update.effective_user.id):
        return

    kb = [
        [InlineKeyboardButton("👥 إدارة الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("📢 النشر", callback_data="publish")]
    ]

    await update.message.reply_text("🛠 لوحة الأدمن PRO", reply_markup=InlineKeyboardMarkup(kb))

# ================= USERS LIST =================
async def users(update: Update, context):
    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name,points FROM users ORDER BY points DESC LIMIT 25")
    rows = c.fetchall()

    kb = [
        [InlineKeyboardButton(f"{n} | {p}", callback_data=f"user_{i}")]
        for i,n,p in rows
    ]

    kb.append([InlineKeyboardButton("🔙 رجوع", callback_data="back")])

    await q.message.reply_text("👥 الأعضاء", reply_markup=InlineKeyboardMarkup(kb))

# ================= PROFILE CARD =================
async def user_profile(update: Update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT name,points,title,locked FROM users WHERE user_id=?", (uid,))
    name, points, t, locked = c.fetchone()

    lvl = level(points)

    kb = [
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data=f"add_{uid}")],
        [InlineKeyboardButton("➖ خصم نقاط", callback_data=f"sub_{uid}")],
        [InlineKeyboardButton("🏅 تغيير لقب", callback_data=f"settitle_{uid}")],
        [InlineKeyboardButton("🔒 قفل/فتح", callback_data=f"lock_{uid}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="users")]
    ]

    await q.message.reply_text(f"""
👤 {name}

💰 النقاط: {points}
📊 المستوى: {lvl}
🏅 اللقب: {t}
🔒 الحالة: {"مقفل" if locked else "مفتوح"}
""", reply_markup=InlineKeyboardMarkup(kb))

# ================= ADD / SUB =================
async def add(update, context):
    q = update.callback_query
    await q.answer()
    state["action"] = ("add", int(q.data.split("_")[1]))
    await q.message.reply_text("➕ أرسل الرقم")

async def sub(update, context):
    q = update.callback_query
    await q.answer()
    state["action"] = ("sub", int(q.data.split("_")[1]))
    await q.message.reply_text("➖ أرسل الرقم")

# ================= LOCK TITLE =================
async def lock(update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT locked FROM users WHERE user_id=?", (uid,))
    l = c.fetchone()[0]

    new = 0 if l else 1

    c.execute("UPDATE users SET locked=? WHERE user_id=?", (new, uid))
    conn.commit()

    await q.message.reply_text("🔄 تم التبديل")

# ================= ADMIN INPUT =================
async def handle(update, context):

    uid = update.effective_user.id
    text = update.message.text

    register(uid, update.effective_user.first_name)

    if uid == ADMIN_ID and "action" in state:

        action, target = state["action"]

        c.execute("SELECT points,name FROM users WHERE user_id=?", (target,))
        points, name = c.fetchone()

        if action == "add":
            points += int(text)
            log(f"ADD {text} -> {name}")

        elif action == "sub":
            points -= int(text)
            if points < 0:
                points = 0
            log(f"SUB {text} -> {name}")

        c.execute("UPDATE users SET points=? WHERE user_id=?", (points, target))
        conn.commit()

        await update.message.reply_text(f"✅ تم تعديل {name} -> {points}")

        state.pop("action")

# ================= STATS =================
async def stats(update: Update, context):
    q = update.callback_query
    await q.answer()

    c.execute("SELECT COUNT(*),SUM(points) FROM users")
    users_count, total_points = c.fetchone()

    await q.message.reply_text(f"""
📊 الإحصائيات:

👥 المستخدمين: {users_count}
💰 مجموع النقاط: {total_points or 0}
""")

# ================= ROUTER (NESTED UI) =================
async def router(update: Update, context):
    q = update.callback_query
    d = q.data

    if d == "users":
        await users(update, context)

    elif d.startswith("user_"):
        await user_profile(update, context)

    elif d.startswith("add_"):
        await add(update, context)

    elif d.startswith("sub_"):
        await sub(update, context)

    elif d.startswith("lock_"):
        await lock(update, context)

    elif d == "stats":
        await stats(update, context)

    elif d == "back":
        await admin(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT PRO V3 RUNNING")
app.run_polling()
