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
state = {}

# ================= TITLES (50) =================
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
"🏆 Supreme","🌟 Apex","💥 Ultra","🎯 Boss","👑 GOD"
]

# ================= QUESTIONS =================
QUESTIONS = [
("ما عاصمة العراق؟","بغداد"),
("ما عاصمة فرنسا؟","باريس"),
("ما أكبر دولة؟","روسيا"),
("ما أصغر دولة؟","الفاتيكان"),
("ما أكبر كوكب؟","المشتري"),
("ما غاز التنفس؟","الأكسجين"),
("كم عدد القارات؟","7"),
("ما قبلة المسلمين؟","الكعبة"),
("من أول نبي؟","آدم"),
("ما أطول نهر؟","النيل"),
("ليش السمك ما يدرس؟","لأنه يعيش بالمدرسة 😂"),
("ليش القمر ما ينام؟","لأنه يدور 😂")
]

# ================= SYSTEM =================
def level(points):
    return points // 200

def progress(points):
    return points % 200

def title(points):
    l = level(points)
    return TITLES[l] if l < len(TITLES) else TITLES[-1]

def bar(points):
    p = progress(points)
    fill = int(p / 20)
    return "█"*fill + "░"*(10-fill)

# ================= REGISTER =================
def register(uid, name):
    c.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)", (uid, name, 0, 0, "🌱 عضو جديد", 0))
        conn.commit()

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text("👋 أهلاً بك")

# ================= QUESTIONS =================
def get_q():
    return random.choice(QUESTIONS)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text

    register(uid, update.effective_user.first_name)

    # ================= QUESTION =================
    if text in ["سؤال","سوال"]:
        q, a = get_q()
        c.execute("REPLACE INTO active_q VALUES (?,?)", (uid,a))
        conn.commit()
        await update.message.reply_text(f"❓ {q}")
        return

    # ================= ANSWER CHECK =================
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

    # ================= UPDATE =================
    c.execute("SELECT points,messages,title,locked FROM users WHERE user_id=?", (uid,))
    p,m,t,l = c.fetchone()

    old = title(p)

    p += add
    m += 1

    new = title(p) if l == 0 else t

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
              (p,m,new,uid))
    conn.commit()

    await update.message.reply_text(f"""
💰 النقاط: {p}
🎖 اللقب: {new}
📊 {bar(p)} {progress(p)}/200
""")

    if old != new:
        await update.message.reply_text(f"🎉 ترقية: {new}")

# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📢 نشر", callback_data="publish")]
    ]

    await update.message.reply_text("لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= PUBLISH =================
async def publish(update: Update, context):
    q = update.callback_query
    await q.answer()

    msg = await q.message.reply_text("✍️ أرسل النص")

    state[ADMIN_ID] = "publish"

# ================= HANDLE ADMIN =================
async def admin_handle(update: Update, context):

    uid = update.effective_user.id
    text = update.message.text

    if uid == ADMIN_ID and ADMIN_ID in state:

        if state[ADMIN_ID] == "publish":

            msg = await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"📢 إعلان\n\n{text}"
            )

            kb = [
                [InlineKeyboardButton("📌 تثبيت", callback_data=f"pin|{msg.message_id}")],
                [InlineKeyboardButton("➖ بدون", callback_data="nopin")]
            ]

            await update.message.reply_text("تم الإرسال", reply_markup=InlineKeyboardMarkup(kb))

            state.pop(ADMIN_ID)
            return

# ================= PIN =================
async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data.startswith("pin"):
        msg_id = int(q.data.split("|")[1])

        await context.bot.pin_chat_message(GROUP_ID, msg_id)

        await q.message.reply_text("📌 تم التثبيت")
    else:
        await q.message.reply_text("✔ بدون تثبيت")

# ================= ROUTER =================
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query

    if q.data == "publish":
        await publish(update, context)

    if q.data.startswith("pin") or q.data == "nopin":
        await pin(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handle))

print("BOT RUNNING FULL SYSTEM")
app.run_polling()
