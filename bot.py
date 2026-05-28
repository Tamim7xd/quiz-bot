import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

# ================= DB =================
c.execute("""CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
name TEXT,
points INTEGER DEFAULT 0,
messages INTEGER DEFAULT 0,
title TEXT DEFAULT '🌱 عضو جديد',
locked INTEGER DEFAULT 0
)""")

c.execute("""CREATE TABLE IF NOT EXISTS logs(
text TEXT
)""")

conn.commit()

# ================= STATE =================
state = {}

# ================= TITLES =================
TITLES = ["🌱 مبتدئ","🌿 متعلم","⚡ نشيط","🔥 متفاعل","🚀 متقدم",
"🎯 محترف","⭐ مميز","🏅 بطل","🥇 نجم","👑 قائد",
"💎 خبير","🏆 أسطورة","⚔️ محارب","🛡️ حارس","🌟 سوبر",
"💥 خارق","🎮 لاعب","🧠 ذكي","📚 مثقف","🌍 رحّالة",
"💠 أسطورة","🔥 Legend","⚡ Elite","👑 King","💎 Diamond",
"🚀 Pro","🎯 Sharp","⭐ Star","🏅 Hero","🥇 Champ",
"🧠 Genius","🔥 Master","⚔️ Fighter","🛡 Defender","🌟 Ultra",
"💥 Beast","🎮 Gamer","📚 Scholar","🌍 Explorer","💠 Myth",
"👑 Emperor","💎 Titan","🚀 Rocket","⚡ Flash","🔥 Omega",
"🏆 Supreme","🌟 Apex","🎯 Boss","👑 GOD","💎 Final"]

# ================= UTIL =================
def level(p): return p // 200
def title(p): return TITLES[level(p)] if level(p) < len(TITLES) else TITLES[-1]

def register(uid, name):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",
                  (uid, name, 0, 0, "🌱 عضو جديد", 0))
        conn.commit()

# ================= START =================
async def start(update, context):
    register(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text("👋 أهلاً بك")

# ================= ADMIN PANEL =================
async def admin(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("📢 رسالة", callback_data="send")]
    ]

    await update.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= USERS =================
async def users(update, context):
    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name,points FROM users ORDER BY points DESC LIMIT 30")
    rows = c.fetchall()

    kb = [[InlineKeyboardButton(f"{n} | {p}", callback_data=f"user_{i}")] for i,n,p in rows]

    await q.message.reply_text("👥 الأعضاء", reply_markup=InlineKeyboardMarkup(kb))

# ================= USER PROFILE =================
async def user_profile(update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT name,points,title FROM users WHERE user_id=?", (uid,))
    name, points, t = c.fetchone()

    kb = [
        [InlineKeyboardButton("➕ نقاط", callback_data=f"add_{uid}")],
        [InlineKeyboardButton("➖ خصم", callback_data=f"sub_{uid}")],
        [InlineKeyboardButton("🎖 لقب", callback_data=f"title_{uid}")],
        [InlineKeyboardButton("📢 تنبيه", callback_data=f"alert_{uid}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="users")]
    ]

    await q.message.reply_text(f"""
👤 {name}
💰 {points}
🏅 {t}
""", reply_markup=InlineKeyboardMarkup(kb))

# ================= ADD / SUB =================
async def add(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("add", int(q.data.split("_")[1]))
    await q.message.reply_text("➕ أرسل الرقم")

async def sub(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("sub", int(q.data.split("_")[1]))
    await q.message.reply_text("➖ أرسل الرقم")

# ================= TITLE =================
async def set_title(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("title", int(q.data.split("_")[1]))
    await q.message.reply_text("🎖 أرسل اللقب")

# ================= ALERT =================
async def alert(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("alert", int(q.data.split("_")[1]))
    await q.message.reply_text("📢 أرسل التنبيه")

# ================= HANDLE =================
async def handle(update, context):

    uid = update.effective_user.id
    text = update.message.text
    register(uid, update.effective_user.first_name)

    if uid != ADMIN_ID or "a" not in state:
        return

    action, target = state["a"]

    c.execute("SELECT name,points FROM users WHERE user_id=?", (target,))
    name, points = c.fetchone()

    if action == "add":
        points += int(text)
        msg = f"➕ تم إضافة {text} لـ {name}"

    elif action == "sub":
        points -= int(text)
        if points < 0: points = 0
        msg = f"➖ تم خصم {text} من {name}"

    elif action == "title":
        c.execute("UPDATE users SET title=? WHERE user_id=?", (text, target))
        conn.commit()
        msg = f"🎖 تم تغيير لقب {name}"

    elif action == "alert":
        await context.bot.send_message(target, f"📢 تنبيه: {text}")
        msg = f"📢 تم إرسال تنبيه لـ {name}"

    if action in ["add","sub"]:
        c.execute("UPDATE users SET points=? WHERE user_id=?", (points, target))
        conn.commit()

        await context.bot.send_message(
            GROUP_ID,
            f"📊 {msg}\n💰 النقاط الآن: {points}"
        )

    state.pop("a")

    await update.message.reply_text("✅ تم")

# ================= ROUTER =================
async def router(update, context):

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

    elif d.startswith("title_"):
        await set_title(update, context)

    elif d.startswith("alert_"):
        await alert(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("ADMIN OS V5 RUNNING")
app.run_polling()
