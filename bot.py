import os
import sqlite3
import random

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
admin_state = {}

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

# ================= QUESTIONS =================
QUESTIONS = [
("ما عاصمة العراق؟","بغداد"),
("ما عاصمة فرنسا؟","باريس"),
("ما أكبر دولة؟","روسيا"),
("ما أصغر دولة؟","الفاتيكان"),
("ما أطول نهر؟","النيل"),
("ما غاز التنفس؟","الأكسجين"),
("كم عدد القارات؟","7"),
("ما قبلة المسلمين؟","الكعبة"),
("من أول نبي؟","آدم"),
("ما أكبر كوكب؟","المشتري")
]

# ================= FUNCTIONS =================
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

def get_title(points):
    lvl = level(points)
    return TITLES[lvl] if lvl < len(TITLES) else TITLES[-1]

def bar(points):
    p = progress(points)
    return "█" * (p // 20) + "░" * (10 - p // 20)

def get_question():
    return random.choice(QUESTIONS)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text("👋 أهلاً بك في البوت")

# ================= QUESTIONS + POINTS =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text

    register(uid, update.effective_user.first_name)

    # سؤال
    if text in ["سؤال", "سوال"]:
        q, a = get_question()
        c.execute("REPLACE INTO active_q VALUES (?,?)", (uid, a))
        conn.commit()
        await update.message.reply_text(f"❓ {q}")
        return

    # جواب
    c.execute("SELECT answer FROM active_q WHERE user_id=?", (uid,))
    row = c.fetchone()

    add = 1

    if row:
        if text.lower() == row[0].lower():
            add = 5
            await update.message.reply_text("✅ صحيح +5 نقاط")
        else:
            await update.message.reply_text(f"❌ خطأ: {row[0]}")

        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

    c.execute("SELECT points,messages,title,locked FROM users WHERE user_id=?", (uid,))
    p, m, t, l = c.fetchone()

    old = get_title(p)

    p += add
    m += 1

    new = get_title(p) if l == 0 else t

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
              (p, m, new, uid))
    conn.commit()

    await update.message.reply_text(f"""
💰 النقاط: {p}
🎖 اللقب: {new}
📊 {bar(p)} {progress(p)}/200
""")

    if old != new:
        await update.message.reply_text(f"🎉 ترقية: {new}")

# ================= ADMIN PANEL =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("👥 إدارة الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📢 نشر", callback_data="publish")]
    ]

    await update.message.reply_text(
        "🛠 لوحة الأدمن",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= USERS =================
async def users(update: Update, context):
    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name,points,title FROM users ORDER BY points DESC LIMIT 20")
    rows = c.fetchall()

    kb = []

    for uid, name, points, title in rows:
        kb.append([InlineKeyboardButton(f"{name} | {points} | {title}", callback_data=f"user_{uid}")])

    await q.message.reply_text("👥 الأعضاء:", reply_markup=InlineKeyboardMarkup(kb))

# ================= USER PANEL =================
async def user_panel(update: Update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT name,points,title,locked FROM users WHERE user_id=?", (uid,))
    name, points, title, locked = c.fetchone()

    lock_text = "🔒 قفل" if locked == 0 else "🔓 فتح"

    kb = [
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data=f"add_{uid}")],
        [InlineKeyboardButton("➖ خصم نقاط", callback_data=f"sub_{uid}")],
        [InlineKeyboardButton(lock_text, callback_data=f"lock_{uid}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="users")]
    ]

    await q.message.reply_text(f"""
👤 {name}
💰 {points}
🎖 {title}
""", reply_markup=InlineKeyboardMarkup(kb))

# ================= ADD/SUB =================
async def add(update: Update, context):
    q = update.callback_query
    await q.answer()
    admin_state["action"] = ("add", int(q.data.split("_")[1]))
    await q.message.reply_text("💰 أرسل الرقم")

async def sub(update: Update, context):
    q = update.callback_query
    await q.answer()
    admin_state["action"] = ("sub", int(q.data.split("_")[1]))
    await q.message.reply_text("➖ أرسل الرقم")

# ================= LOCK =================
async def lock(update: Update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT locked FROM users WHERE user_id=?", (uid,))
    locked = c.fetchone()[0]

    new = 0 if locked == 1 else 1

    c.execute("UPDATE users SET locked=? WHERE user_id=?", (new, uid))
    conn.commit()

    await q.message.reply_text("🔄 تم التغيير")

# ================= ADMIN INPUT =================
async def admin_input(update: Update, context):
    uid = update.effective_user.id
    text = update.message.text

    if uid != ADMIN_ID or "action" not in admin_state:
        return

    action, target = admin_state["action"]

    c.execute("SELECT points,name FROM users WHERE user_id=?", (target,))
    points, name = c.fetchone()

    if action == "add":
        points += int(text)
    else:
        points -= int(text)
        if points < 0:
            points = 0

    c.execute("UPDATE users SET points=? WHERE user_id=?", (points, target))
    conn.commit()

    await update.message.reply_text(f"✅ تم تعديل {name}\n💰 {points}")

    admin_state.pop("action")

# ================= PUBLISH =================
async def publish(update: Update, context):
    q = update.callback_query
    await q.answer()

    admin_state["publish"] = True
    await q.message.reply_text("📢 أرسل النص")

# ================= HANDLE PUBLISH =================
async def publish_handle(update: Update, context):
    uid = update.effective_user.id

    if uid == ADMIN_ID and "publish" in admin_state:

        msg = await context.bot.send_message(GROUP_ID, f"📢 {update.message.text}")

        kb = [
            [InlineKeyboardButton("📌 تثبيت", callback_data=f"pin_{msg.message_id}")],
            [InlineKeyboardButton("❌ بدون", callback_data="nopin")]
        ]

        await update.message.reply_text("تم الإرسال", reply_markup=InlineKeyboardMarkup(kb))

        admin_state.pop("publish")

# ================= PIN =================
async def pin(update: Update, context):
    q = update.callback_query
    await q.answer()

    if q.data.startswith("pin"):
        msg_id = int(q.data.split("_")[1])
        await context.bot.pin_chat_message(GROUP_ID, msg_id)
        await q.message.reply_text("📌 تم التثبيت")
    else:
        await q.message.reply_text("✔ بدون تثبيت")

# ================= ROUTER =================
async def router(update: Update, context):
    q = update.callback_query
    d = q.data

    if d == "users":
        await users(update, context)

    elif d.startswith("user_"):
        await user_panel(update, context)

    elif d.startswith("add_"):
        await add(update, context)

    elif d.startswith("sub_"):
        await sub(update, context)

    elif d.startswith("lock_"):
        await lock(update, context)

    elif d == "publish":
        await publish(update, context)

    elif d.startswith("pin") or d == "nopin":
        await pin(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_input))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, publish_handle))

print("BOT RUNNING")
app.run_polling()
