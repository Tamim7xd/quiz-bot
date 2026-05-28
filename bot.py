import os
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

# ================= DB =================
c.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
name TEXT,
points INTEGER DEFAULT 0,
messages INTEGER DEFAULT 0,
title TEXT DEFAULT '🌱 عضو جديد'
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS active_q(
user_id INTEGER PRIMARY KEY,
answer TEXT
)
""")

conn.commit()

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

def level(p): return p // 200
def get_title(p): return TITLES[level(p)] if level(p) < len(TITLES) else TITLES[-1]

# ================= QUESTIONS =================
QUESTIONS = [
("ما عاصمة العراق؟","بغداد"),
("ما عاصمة السعودية؟","الرياض"),
("ما أكبر كوكب؟","المشتري"),
("ما أطول نهر؟","النيل"),
("ما لغة القرآن؟","العربية"),
]

def get_question():
    return random.choice(QUESTIONS)

# ================= REGISTER =================
def register(uid, name):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,0,0,'🌱 عضو جديد')", (uid,name))
        conn.commit()

# ================= START =================
async def start(update: Update, context):
    register(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text("👋 أهلاً بك في البوت")

# ================= INFO (FIXED) =================
async def myinfo(update: Update, context):

    uid = update.effective_user.id
    name = update.effective_user.first_name

    c.execute("SELECT points,messages,title FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()

    if not row:
        await update.message.reply_text("❌ لا يوجد بيانات")
        return

    p,m,t = row

    await update.message.reply_text(
f"""📊 معلوماتك

👤 الاسم: {name}
💰 النقاط: {p}
💬 الرسائل: {m}
🏅 اللقب: {t}
📈 المستوى: {level(p)}
"""
    )

# ================= QUESTIONS =================
async def ask(update: Update, context):
    uid = update.effective_user.id

    q,a = get_question()
    c.execute("REPLACE INTO active_q VALUES (?,?)", (uid,a))
    conn.commit()

    await update.message.reply_text(f"❓ {q}")

# ================= HANDLE =================
async def handle(update: Update, context):

    uid = update.effective_user.id
    text = update.message.text
    name = update.effective_user.first_name

    register(uid,name)

    # ================= CHECK ANSWER =================
    c.execute("SELECT answer FROM active_q WHERE user_id=?", (uid,))
    row = c.fetchone()

    add = 1

    if row:
        correct = row[0]

        if text.lower() == correct.lower():
            add = 5
            await update.message.reply_text("✅ صحيح +5 نقاط")
        else:
            await update.message.reply_text(f"❌ خطأ الإجابة: {correct}")

        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

    # ================= UPDATE =================
    c.execute("SELECT points,messages FROM users WHERE user_id=?", (uid,))
    p,m = c.fetchone()

    p += add
    m += 1

    new_title = get_title(p)

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
              (p,m,new_title,uid))
    conn.commit()

# ================= ADMIN PANEL =================
async def admin(update: Update, context):

    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📢 تنبيه جماعي", callback_data="mass")],
        [InlineKeyboardButton("💰 نقاط للجميع", callback_data="all")]
    ]

    await update.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= USERS =================
async def users(update: Update, context):

    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name,points FROM users ORDER BY points DESC LIMIT 30")
    rows = c.fetchall()

    kb = [[InlineKeyboardButton(f"{n} | {p}", callback_data=f"user_{i}")] for i,n,p in rows]

    await q.message.reply_text("👥 الأعضاء", reply_markup=InlineKeyboardMarkup(kb))

# ================= ROUTER =================
async def router(update: Update, context):

    q = update.callback_query
    d = q.data

    if d == "users":
        await users(update,context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("معلوماتي", myinfo))
app.add_handler(CommandHandler("سؤال", ask))
app.add_handler(CommandHandler("سوال", ask))

app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT FIXED V9 RUNNING")
app.run_polling()
