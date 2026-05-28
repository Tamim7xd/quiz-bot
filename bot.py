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

# ================= TITLES (50 ثابت) =================
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

# ================= QUESTIONS (بدون تغيير) =================
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
        c.execute("INSERT INTO users VALUES (?,?,?,?,?)",
                  (uid, name, 0, 0, "🌱 عضو جديد"))
        conn.commit()

# ================= START =================
async def start(update: Update, context):
    register(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text("👋 أهلاً بك")

# ================= ADMIN =================
async def admin(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📢 تنبيه جماعي", callback_data="mass_alert")],
        [InlineKeyboardButton("💰 نقاط للجميع", callback_data="all_points")]
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

# ================= PROFILE =================
async def profile(update: Update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT name,points,title FROM users WHERE user_id=?", (uid,))
    name,p,t = c.fetchone()

    kb = [
        [InlineKeyboardButton("➕ مكافأة", callback_data=f"reward_{uid}")],
        [InlineKeyboardButton("🎖 لقب", callback_data=f"title_{uid}")],
        [InlineKeyboardButton("📢 تنبيه", callback_data=f"alert_{uid}")]
    ]

    await q.message.reply_text(f"👤 {name}\n💰 {p}\n🏅 {t}", reply_markup=InlineKeyboardMarkup(kb))

# ================= REWARD =================
async def reward(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("reward", int(q.data.split("_")[1]))
    await q.message.reply_text("💰 أرسل النقاط + اسم المكافأة (اختياري)")

# ================= TITLE =================
async def title_set(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("title", int(q.data.split("_")[1]))
    await q.message.reply_text("🎖 أرسل اللقب")

# ================= ALERT =================
async def alert(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("alert", int(q.data.split("_")[1]))
    await q.message.reply_text("📢 أرسل سبب التنبيه")

# ================= MASS ALERT =================
async def mass_alert(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("mass", 0)
    await q.message.reply_text("📢 أرسل رسالة جماعية")

# ================= ALL POINTS =================
async def all_points(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("all_points", 0)
    await q.message.reply_text("💰 أرسل عدد النقاط للجميع")

# ================= HANDLE =================
async def handle(update: Update, context):

    uid = update.effective_user.id
    text = update.message.text
    name = update.effective_user.first_name

    register(uid, name)

    # ================= QUESTIONS =================
    if text in ["سؤال","سوال"]:
        q,a = get_question()
        await update.message.reply_text(f"❓ {q}")
        return

    # ================= ADMIN ACTION =================
    if uid != ADMIN_ID or "a" not in state:
        return

    action,target = state["a"]

    # ================= REWARD =================
    if action == "reward":
        parts = text.split(" ",1)
        points = int(parts[0])
        reason = parts[1] if len(parts)>1 else "🎁 مكافأة"

        c.execute("SELECT name,points FROM users WHERE user_id=?", (target,))
        uname,p = c.fetchone()

        p += points
        c.execute("UPDATE users SET points=? WHERE user_id=?", (p,target))
        conn.commit()

        await context.bot.send_message(
            GROUP_ID,
            f"🎁 مكافأة\n👤 {uname}\n💰 +{points}\n📝 {reason}"
        )

    # ================= TITLE =================
    elif action == "title":
        c.execute("UPDATE users SET title=? WHERE user_id=?", (text,target))
        conn.commit()

        await context.bot.send_message(GROUP_ID, f"🏅 لقب جديد: {text}")

    # ================= ALERT =================
    elif action == "alert":
        await context.bot.send_message(target, f"📢 تنبيه: {text}")
        await context.bot.send_message(GROUP_ID, f"📢 تنبيه تم إرساله")

    # ================= MASS =================
    elif action == "mass":
        c.execute("SELECT user_id FROM users")
        users = c.fetchall()

        for u in users:
            try:
                await context.bot.send_message(u[0], f"📢 {text}")
            except:
                pass

        await context.bot.send_message(GROUP_ID, f"📢 إعلان جماعي: {text}")

    # ================= ALL POINTS =================
    elif action == "all_points":
        amount = int(text)

        c.execute("SELECT user_id FROM users")
        users = c.fetchall()

        for u in users:
            c.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount,u[0]))

        conn.commit()

        await context.bot.send_message(
            GROUP_ID,
            f"💰 نقاط جماعية\n➕ {amount} لكل الأعضاء"
        )

    state.pop("a")

# ================= ROUTER =================
async def router(update: Update, context):

    q = update.callback_query
    d = q.data

    if d == "users":
        await users(update,context)

    elif d.startswith("user_"):
        await profile(update,context)

    elif d.startswith("reward_"):
        await reward(update,context)

    elif d.startswith("title_"):
        await title_set(update,context)

    elif d.startswith("alert_"):
        await alert(update,context)

    elif d == "mass_alert":
        await mass_alert(update,context)

    elif d == "all_points":
        await all_points(update,context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT V8 RUNNING")
app.run_polling()
