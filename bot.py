import os
import time
import random
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN", "PUT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = os.getenv("GROUP_ID", None)
GROUP_ID = int(GROUP_ID) if GROUP_ID else None

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
name TEXT,
money INTEGER DEFAULT 0,
messages INTEGER DEFAULT 0,
title TEXT DEFAULT '🌱 عضو',
start_time INTEGER,
last_time INTEGER,
locked INTEGER DEFAULT 0,
rewards INTEGER DEFAULT 0,
warnings INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS questions(
user_id INTEGER PRIMARY KEY,
answer TEXT
)
""")

conn.commit()

# ================= TITLES =================
TITLES = [
"🌱 مبتدئ","🌿 ناشئ","⚡ نشيط","🔥 متفاعل","🚀 متقدم",
"🎯 محترف","⭐ مميز","🏅 بطل","🥇 نجم","👑 قائد",
"💎 خبير","🏆 أسطورة","⚔️ محارب","🛡️ حارس","🌟 سوبر",
"💥 قوي","🎮 لاعب","🧠 ذكي","📚 مثقف","🌍 رحّال",
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

def level(m):
    return m // 200

def get_title(m):
    return TITLES[min(level(m), len(TITLES)-1)]

# ================= REGISTER =================
def reg(u):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (u.id,))
    if not c.fetchone():
        c.execute("""
        INSERT INTO users VALUES (?,?,?,?,?,?,?,0,0,0)
        """, (u.id, u.first_name, 0, 0, "🌱 عضو", now(), now()))
        conn.commit()

# ================= GROUP MSG =================
async def group(msg):
    if GROUP_ID:
        try:
            await app.bot.send_message(GROUP_ID, msg)
        except:
            pass

# ================= START =================
async def start(update: Update, context):
    reg(update.effective_user)
    await update.message.reply_text("💰 البوت شغال الآن (ULTRA MONEY PRO)")

# ================= QUESTIONS =================
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

    c.execute("REPLACE INTO questions VALUES (?,?)", (u.id,a))
    conn.commit()

    await update.message.reply_text(f"❓ {q}")

# ================= GET USER =================
def get(uid):
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return c.fetchone()

# ================= INFO =================
async def info(update: Update, context):
    u = update.effective_user
    reg(u)
    d = get(u.id)

    txt = f"""
📊 معلوماتك
━━━━━━━━━━
👤 {d[1]}
💰 فلوس: {d[2]}
💬 رسائل: {d[3]}
🏅 لقب: {d[4]}
⏱ ساعات: {hours(d[5])}
🔥 مستوى: {level(d[2])}
━━━━━━━━━━
"""
    await update.message.reply_text(txt)

# ================= HANDLE =================
async def handle(update: Update, context):
    u = update.effective_user
    text = update.message.text.lower()
    reg(u)

    c.execute("""
    UPDATE users 
    SET messages=messages+1,
        money=money+1,
        last_time=?
    WHERE user_id=?
    """, (now(), u.id))
    conn.commit()

    d = get(u.id)

    # title update
    if d[7] == 0:
        c.execute("UPDATE users SET title=? WHERE user_id=?", (get_title(d[2]), u.id))
        conn.commit()

    # QUESTION CHECK
    c.execute("SELECT answer FROM questions WHERE user_id=?", (u.id,))
    q = c.fetchone()

    if q:
        if text.strip() == q[0].lower():
            c.execute("UPDATE users SET money=money+5,rewards=rewards+1 WHERE user_id=?", (u.id,))
            await update.message.reply_text("✅ صحيح +5 فلوس")
            await group(f"🎁 مكافأة: {u.first_name} أجاب صحيح")
        else:
            await update.message.reply_text(f"❌ خطأ: {q[0]}")
        c.execute("DELETE FROM questions WHERE user_id=?", (u.id,))
        conn.commit()

    # COMMANDS
    if any(x in text for x in ["فلوسي","فلوس","راتبي","راتب","mymoney"]):
        await update.message.reply_text(f"💰 {d[2]}")

    if any(x in text for x in ["معلوماتي","info"]):
        await info(update, context)

    if any(x in text for x in ["رسائلي","رسالاتي"]):
        await update.message.reply_text(f"💬 {d[3]}")

    if any(x in text for x in ["ساعاتي","وقت","نشاطي"]):
        await update.message.reply_text(f"⏱ {hours(d[5])} ساعة")

    if "سوال" in text or "سؤال" in text:
        await ask(update, context)

    await group(f"📌 نشاط: {u.first_name} 💰{d[2]} 🏅{d[4]}")

# ================= ADMIN =================
async def admin(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("❓ سؤال", callback_data="ask")]
    ]

    await update.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= CALLBACK =================
async def cb(update: Update, context):
    q = update.callback_query
    await q.answer()

    if q.data == "users":
        c.execute("SELECT name,money FROM users ORDER BY money DESC LIMIT 10")
        rows = c.fetchall()

        txt = "👥 الأعضاء\n"
        for i,r in enumerate(rows,1):
            txt += f"{i}- {r[0]} | 💰 {r[1]}\n"

        await q.message.reply_text(txt)

    if q.data == "stats":
        c.execute("SELECT SUM(money),SUM(messages),COUNT(*),SUM(rewards) FROM users")
        s = c.fetchone()

        await q.message.reply_text(f"""
📊 إحصائيات
💰 {s[0]}
💬 {s[1]}
👥 {s[2]}
🎁 {s[3]}
""")

    if q.data == "ask":
        q2,a = get_q()
        await q.message.reply_text(f"❓ {q2}")

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("سوال", ask))
app.add_handler(CommandHandler("سؤال", ask))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(cb))

print("ULTRA MONEY PRO FIXED RUNNING 🚀")
app.run_polling()
