import os
import time
import random
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN", "PUT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
name TEXT,
points INTEGER DEFAULT 0,
messages INTEGER DEFAULT 0,
title TEXT DEFAULT '🌱 عضو جديد',
start_time INTEGER,
last_time INTEGER,
locked INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS active_q(
user_id INTEGER PRIMARY KEY,
answer TEXT
)
""")

conn.commit()

# ================= TITLES (50) =================
TITLES = [
"🌱 عضو جديد","🌿 مبتدئ","⚡ نشيط","🔥 متفاعل","🚀 متقدم",
"🎯 محترف","⭐ مميز","🏅 بطل","🥇 نجم","👑 قائد",
"💎 خبير","🏆 أسطورة","⚔️ محارب","🛡️ حارس","🌟 سوبر",
"💥 خارق","🎮 لاعب","🧠 ذكي","📚 مثقف","🌍 رحّالة",
"💠 Legend","🔥 Elite","⚡ Pro","👑 King","💎 Diamond",
"🚀 Boss","🎯 Sharp","⭐ Star","🏅 Hero","🥇 Champ",
"🧠 Genius","🔥 Master","⚔️ Fighter","🛡 Defender","🌟 Ultra",
"💥 Beast","🎮 Gamer","📚 Scholar","🌍 Explorer","💠 Myth",
"👑 Emperor","💎 Titan","🚀 Rocket","⚡ Flash","🔥 Omega",
"🏆 Supreme","🌟 Apex","🎯 LegendX","👑 GOD","💎 Final"
]

# ================= HELPERS =================
def now():
    return int(time.time())

def hours(start):
    if not start:
        return 0
    return round((now() - start) / 3600, 1)

def level(p):
    return p // 200

def get_title(p):
    return TITLES[min(level(p), len(TITLES)-1)]

# ================= USER =================
def reg(u):
    c.execute("SELECT * FROM users WHERE user_id=?", (u.id,))
    if not c.fetchone():
        c.execute("""
        INSERT INTO users VALUES (?,?,?,?,?,?,?,0)
        """, (u.id, u.first_name, 0, 0, "🌱 عضو جديد", now(), now()))
        conn.commit()

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reg(update.effective_user)
    await update.message.reply_text("👋 أهلاً بك في ULTRA PRO MAX")

# ================= QUESTION =================
QUESTIONS = [
("ما عاصمة العراق؟","بغداد"),
("ما أكبر كوكب؟","المشتري"),
("كم عدد القارات؟","7"),
("ما لغة القرآن؟","العربية")
]

def get_q():
    return random.choice(QUESTIONS)

async def ask(update: Update, context):
    u = update.effective_user
    q,a = get_q()

    c.execute("REPLACE INTO active_q VALUES (?,?)", (u.id,a))
    conn.commit()

    await update.message.reply_text(f"❓ {q}")

# ================= INFO =================
def get(u):
    c.execute("SELECT * FROM users WHERE user_id=?", (u,))
    return c.fetchone()

async def info(update: Update, context):
    u = update.effective_user
    reg(u)
    d = get(u.id)

    msg = f"""
📊 معلوماتك
━━━━━━━━━━
👤 {d[1]}
💰 {d[2]}
💬 {d[3]}
🏅 {d[4]}
⏱ {hours(d[5])} ساعة
🔥 مستوى {level(d[2])}
━━━━━━━━━━
"""
    await update.message.reply_text(msg)

# ================= HANDLE =================
async def handle(update: Update, context):
    u = update.effective_user
    text = update.message.text.lower()
    reg(u)

    c.execute("UPDATE users SET messages=messages+1, points=points+1, last_time=? WHERE user_id=?",
              (now(), u.id))
    conn.commit()

    # ================= QUESTION =================
    c.execute("SELECT answer FROM active_q WHERE user_id=?", (u.id,))
    q = c.fetchone()

    if q:
        if text.strip() == q[0].lower():
            c.execute("UPDATE users SET points=points+5 WHERE user_id=?", (u.id,))
            await update.message.reply_text("✅ صحيح +5 نقاط")
        else:
            await update.message.reply_text(f"❌ خطأ: {q[0]}")
        c.execute("DELETE FROM active_q WHERE user_id=?", (u.id,))
        conn.commit()

    # ================= SMART =================
    if "معلوماتي" in text or "info" in text:
        await info(update, context)

    if "نقاطي" in text:
        await update.message.reply_text(f"💰 {get(u.id)[2]}")

    if "رسائلي" in text:
        await update.message.reply_text(f"💬 {get(u.id)[3]}")

    if "ساعاتي" in text or "وقت" in text:
        await update.message.reply_text(f"⏱ {hours(get(u.id)[5])} ساعة")

    if "سوال" in text or "سؤال" in text:
        await ask(update, context)

    # ================= TITLE UPDATE =================
    d = get(u.id)
    if d[7] == 0:  # locked
        new = get_title(d[2])
        c.execute("UPDATE users SET title=? WHERE user_id=?", (new, u.id))
        conn.commit()

# ================= ADMIN =================
async def admin(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")]
    ]

    await update.message.reply_text("🛠 ULTRA ADMIN", reply_markup=InlineKeyboardMarkup(kb))

# ================= CALLBACK =================
async def cb(update: Update, context):
    q = update.callback_query
    await q.answer()

    if q.data == "users":
        c.execute("SELECT name,points FROM users ORDER BY points DESC LIMIT 10")
        rows = c.fetchall()

        msg = "👥 الأعضاء\n"
        for i,r in enumerate(rows,1):
            msg += f"{i}- {r[0]} | {r[1]}\n"

        await q.message.reply_text(msg)

    if q.data == "stats":
        c.execute("SELECT SUM(points),SUM(messages),COUNT(*) FROM users")
        s = c.fetchone()

        await q.message.reply_text(f"""
📊 إحصائيات
💰 {s[0]}
💬 {s[1]}
👥 {s[2]}
""")

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("سوال", ask))
app.add_handler(CommandHandler("سؤال", ask))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(cb))

print("ULTRA PRO MAX RUNNING 🚀")
app.run_polling()
