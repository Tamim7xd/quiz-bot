import os
import sqlite3
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

if not TOKEN:
    raise Exception("BOT_TOKEN missing")

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
    title_locked INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS active_q (
    user_id INTEGER PRIMARY KEY,
    answer TEXT
)
""")

conn.commit()

# ================= QUESTIONS =================
QUESTIONS = [
    ("ما عاصمة العراق؟", "بغداد"),
    ("ما عاصمة السعودية؟", "الرياض"),
    ("ما أكبر قارة؟", "آسيا"),
    ("ما أصغر قارة؟", "أستراليا"),
    ("ما أطول نهر؟", "النيل"),
    ("ما أكبر كوكب؟", "المشتري"),
]

def get_question():
    return random.choice(QUESTIONS)

# ================= TITLES =================
def get_title(points):
    if points < 200:
        return "🌱 عضو جديد"

    level = points // 200

    titles = [
        "🌿 متعلم",
        "⚡ نشيط",
        "🔥 متفاعل",
        "🚀 متقدم",
        "🎯 محترف",
        "⭐ مميز",
        "🏅 بطل",
        "🥇 نجم",
        "👑 قائد",
        "💎 خبير",
        "🏆 أسطورة",
        "⚔️ محارب",
        "🛡️ حارس",
        "🌟 سوبر ستار",
        "💥 خارق",
        "🎮 لاعب",
        "🧩 محلل",
        "📚 مثقف",
        "🌍 رحّالة",
        "💠 أسطورة عليا",
        "🔥 ملك التفاعل",
        "⚡ سريع الرد",
        "🎯 دقيق",
        "🚀 صاروخ",
        "👑 ملك",
        "💎 الماسي",
        "🏆 بطل الأبطال",
        "⚔️ مقاتل",
        "🛡️ الحارس الأول",
        "🌟 نجم المجتمع",
        "💥 قوة",
        "🎮 محترف ألعاب",
        "🧠 ذكي",
        "📊 محلل بيانات",
        "🌍 عالمي",
        "💫 متألق",
        "🏅 مميز جداً",
        "🥇 ذهب",
        "👑 قائد الفريق",
        "💎 خبير كبير",
        "🏆 أسطورة حية",
        "⚡ سريع جداً",
        "🔥 نشيط جداً",
        "🎯 محترف جداً",
        "🚀 متقدم جداً",
        "👑 أسطورة مطلقة",
        "💎 نخبة",
        "🏆 VIP",
        "🌟 Legend",
        "💥 Ultimate"
    ]

    return titles[min(level, len(titles)-1)]

# ================= ADMIN MEMORY =================
admin_state = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        keyboard = [[InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="admin")]]
        await update.message.reply_text("🔥 أهلاً أدمن", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("👋 أهلاً بك")

# ================= ADMIN PANEL =================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
    ]

    await q.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= USERS =================
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name FROM users LIMIT 20")
    rows = c.fetchall()

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"user_{uid}")]
        for uid, name in rows
    ]

    await q.message.reply_text("👥 الأعضاء:", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= USER MENU =================
async def user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    keyboard = [
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data=f"add_{uid}")],
        [InlineKeyboardButton("➖ خصم نقاط", callback_data=f"sub_{uid}")],
        [InlineKeyboardButton("✏️ لقب", callback_data=f"title_{uid}")],
        [InlineKeyboardButton("🔒 قفل/فتح اللقب", callback_data=f"lock_{uid}")],
        [InlineKeyboardButton("📢 إرسال للقناة + تثبيت", callback_data=f"pin_{uid}")]
    ]

    await q.message.reply_text("⚙️ إدارة المستخدم", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= POINTS =================
async def add_points(update, context):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("_")[1])
    admin_state[ADMIN_ID] = ("add", uid)
    await q.message.reply_text("➕ ارسل عدد النقاط")

async def sub_points(update, context):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("_")[1])
    admin_state[ADMIN_ID] = ("sub", uid)
    await q.message.reply_text("➖ ارسل عدد النقاط")

# ================= LOCK =================
async def lock_title(update, context):
    q = update.callback_query
    await q.answer()
    uid = int(q.data.split("_")[1])

    c.execute("SELECT title_locked FROM users WHERE user_id=?", (uid,))
    r = c.fetchone()

    new = 0 if r and r[0] == 1 else 1

    c.execute("UPDATE users SET title_locked=? WHERE user_id=?", (new, uid))
    conn.commit()

    await q.message.reply_text("🔒 تم القفل" if new == 1 else "🔓 تم الفتح")

# ================= PIN MESSAGE =================
async def pin_msg(update, context):
    q = update.callback_query
    await q.answer()

    await q.message.reply_text("📢 ارسل الرسالة التي تريد نشرها في القناة")

    admin_state[ADMIN_ID] = ("pin", None)

# ================= HANDLE =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    name = update.effective_user.first_name

    # register
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,0,0,'🌱 عضو جديد',0)", (uid, name))
        conn.commit()

    # admin actions
    if uid == ADMIN_ID and ADMIN_ID in admin_state:
        action, target = admin_state[ADMIN_ID]

        if action in ["add", "sub"]:
            amount = int(text)

            c.execute("SELECT points FROM users WHERE user_id=?", (target,))
            p = c.fetchone()[0]

            if action == "add":
                p += amount
                msg = "➕ تم إضافة النقاط"
            else:
                p -= amount
                msg = "➖ تم خصم النقاط"

            c.execute("UPDATE users SET points=? WHERE user_id=?", (p, target))
            conn.commit()

            await update.message.reply_text(msg)
            admin_state.pop(ADMIN_ID)
            return

        if action == "pin":
            await context.bot.send_message(chat_id=GROUP_ID, text=text)
            await update.message.reply_text("📢 تم الإرسال للقناة")
            admin_state.pop(ADMIN_ID)
            return

    # question
    if text == "سؤال":
        q, a = get_question()
        c.execute("REPLACE INTO active_q VALUES (?,?)", (uid, a))
        conn.commit()
        await update.message.reply_text(q)
        return

    # points system
    c.execute("SELECT points,messages,title_locked,title FROM users WHERE user_id=?", (uid,))
    p, m, locked, old_title = c.fetchone()

    if text:
        m += 1
        p += 1

    if locked == 0:
        new_title = get_title(p)
    else:
        new_title = old_title

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
              (p, m, new_title, uid))
    conn.commit()

# ================= ROUTER =================
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data

    if data == "admin":
        await admin_panel(update, context)
    elif data == "users":
        await users(update, context)
    elif data.startswith("user_"):
        await user_menu(update, context)
    elif data.startswith("add_"):
        await add_points(update, context)
    elif data.startswith("sub_"):
        await sub_points(update, context)
    elif data.startswith("lock_"):
        await lock_title(update, context)
    elif data.startswith("pin_"):
        await pin_msg(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING")
app.run_polling()
