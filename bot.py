import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
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
title TEXT DEFAULT '🌱 عضو جديد',
locked INTEGER DEFAULT 0
)
""")

conn.commit()

# ================= STATE =================
state = {}

# ================= REGISTER =================
def register(uid, name):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?)",
                  (uid, name, 0, "🌱 عضو جديد", 0))
        conn.commit()

# ================= TITLE SYSTEM =================
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

def level(points):
    return points // 200

def get_title(points):
    lv = level(points)
    return TITLES[lv] if lv < len(TITLES) else TITLES[-1]

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text("👋 أهلاً بك في البوت")

# ================= ADMIN PANEL =================
async def admin(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="stats")]
    ]

    await update.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= USERS LIST =================
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
    name, points, title = c.fetchone()

    kb = [
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data=f"add_{uid}")],
        [InlineKeyboardButton("➖ خصم نقاط", callback_data=f"sub_{uid}")],
        [InlineKeyboardButton("🎖 تعديل لقب", callback_data=f"title_{uid}")],
        [InlineKeyboardButton("🔒 قفل/فتح اللقب", callback_data=f"lock_{uid}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="users")]
    ]

    await q.message.reply_text(
        f"👤 {name}\n💰 {points}\n🏅 {title}",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= ACTIONS =================
async def add(update, context):
    q = update.callback_query
    await q.answer()
    state["action"] = ("add", int(q.data.split("_")[1]))
    await q.message.reply_text("➕ أرسل عدد النقاط")

async def sub(update, context):
    q = update.callback_query
    await q.answer()
    state["action"] = ("sub", int(q.data.split("_")[1]))
    await q.message.reply_text("➖ أرسل عدد الخصم")

async def title(update, context):
    q = update.callback_query
    await q.answer()
    state["action"] = ("title", int(q.data.split("_")[1]))
    await q.message.reply_text("🎖 أرسل اللقب الجديد")

async def lock(update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT locked FROM users WHERE user_id=?", (uid,))
    l = c.fetchone()[0]

    c.execute("UPDATE users SET locked=? WHERE user_id=?", (0 if l else 1, uid))
    conn.commit()

    await q.message.reply_text("🔄 تم التبديل")

# ================= GROUP DISCOUNT SYSTEM =================
async def group_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    text = update.message.text

    if not text.startswith("$خصم"):
        return

    if not update.message.reply_to_message:
        return

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        parts = text.split(" ", 2)
        amount = int(parts[1])
        reason = parts[2] if len(parts) > 2 else "بدون سبب"

        target = update.message.reply_to_message.from_user
        uid = target.id
        name = target.first_name

        c.execute("SELECT points FROM users WHERE user_id=?", (uid,))
        row = c.fetchone()

        if row:
            new_points = max(0, row[0] - amount)
            c.execute("UPDATE users SET points=? WHERE user_id=?", (new_points, uid))
            conn.commit()

        await context.bot.send_message(
            GROUP_ID,
            f"""
📉 خصم نقاط

👤 العضو: {name}
➖ المبلغ: {amount}
📝 السبب: {reason}
💰 المتبقي: {new_points}
"""
        )

    except:
        await update.message.reply_text("❌ خطأ في الخصم")

# ================= HANDLE ADMIN INPUT =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text

    register(uid, update.effective_user.first_name)

    # ===== GROUP DISCOUNT =====
    await group_discount(update, context)

    if uid != ADMIN_ID or "action" not in state:
        return

    action, target = state["action"]

    c.execute("SELECT name,points FROM users WHERE user_id=?", (target,))
    name, points = c.fetchone()

    old_title = get_title(points)

    if action == "add":
        points += int(text)
        msg = f"➕ إضافة {text} لـ {name}"

    elif action == "sub":
        points = max(0, points - int(text))
        msg = f"➖ خصم {text} من {name}"

    elif action == "title":
        c.execute("UPDATE users SET title=? WHERE user_id=?", (text, target))
        conn.commit()
        await update.message.reply_text("🎖 تم التعديل")
        state.pop("action")
        return

    c.execute("UPDATE users SET points=? WHERE user_id=?", (points, target))
    conn.commit()

    new_title = get_title(points)

    await context.bot.send_message(
        GROUP_ID,
        f"📊 تحديث\n👤 {name}\n{msg}\n💰 {points}"
    )

    if new_title != old_title:
        await context.bot.send_message(
            GROUP_ID,
            f"🎉 ترقية!\n👤 {name}\n🏅 {new_title}"
        )

    state.pop("action")

# ================= ROUTER =================
async def router(update: Update, context):

    q = update.callback_query
    d = q.data

    if d == "users":
        await users(update, context)

    elif d.startswith("user_"):
        await profile(update, context)

    elif d.startswith("add_"):
        await add(update, context)

    elif d.startswith("sub_"):
        await sub(update, context)

    elif d.startswith("title_"):
        await title(update, context)

    elif d.startswith("lock_"):
        await lock(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT FULL SYSTEM RUNNING")
app.run_polling()
