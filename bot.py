import os
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
name TEXT,
points INTEGER DEFAULT 0,
messages INTEGER DEFAULT 0,
title TEXT DEFAULT '🌱 مبتدئ',
title_locked INTEGER DEFAULT 0
)""")
conn.commit()

# ================= TITLES =================
TITLES = [
"🌱 مبتدئ","⚡ نشيط","🔥 متفاعل","🚀 متقدم","🎯 محترف",
"⭐ مميز","🏅 بطل","🥇 نجم","👑 قائد","💎 خبير",
"🏆 أسطورة","⚔️ محارب","🛡️ حارس","🌟 خارق","💥 قوي",
"🎮 لاعب","🧠 ذكي","📚 مثقف","🌍 رحّال","💠 أسطورة",
"👑 ملك","🤴 أمير","🦁 أسد","🐉 تنين","🦅 صقر",
"⚡ برق","🌪️ عاصفة","🔥 نار","❄️ جليد","🧿 محظوظ",
"💰 غني","🪙 ثري","🎯 قناص","🚁 طيار","🧩 محلل",
"🔬 عالم","🎨 مبدع","🎧 فنان","⚙️ مهندس","📡 مخترق",
"👽 فضائي","🤖 روبوت","⚔️ مقاتل","🏹 رامٍ","🐺 ذئب",
"☠️ قاتل","🌌 أسطورة الكون","👑 ملك الملوك","💀 نخبة","🏆 بطل مطلق"
]

def level(p): return p // 200

def get_title(p):
    if p < 200:
        return "🌱 مبتدئ"
    l = level(p)
    return TITLES[l] if l < len(TITLES) else "👑 أسطورة"

# ================= ADMIN TEMP =================
admin_state = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        kb = [[InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="admin")]]
        await update.message.reply_text("🔥 الأدمن", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text("👋 أهلاً بك")

# ================= ADMIN PANEL =================
async def admin(update, context):
    q = update.callback_query
    await q.answer()

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("🎁 نقاط للجميع", callback_data="all_points")]
    ]

    await q.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= USERS LIST =================
async def users(update, context):
    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name,points,title FROM users ORDER BY points DESC LIMIT 30")
    rows = c.fetchall()

    kb = [
        [InlineKeyboardButton(f"{n} | {p} | {t}", callback_data=f"u_{uid}")]
        for uid,n,p,t in rows
    ]

    await q.message.reply_text("👥 اختر عضو:", reply_markup=InlineKeyboardMarkup(kb))

# ================= USER CONTROL PANEL =================
async def user_panel(update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    kb = [
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data=f"add_{uid}")],
        [InlineKeyboardButton("➖ خصم نقاط", callback_data=f"sub_{uid}")],
        [InlineKeyboardButton("🎯 تعيين نقاط", callback_data=f"set_{uid}")],
        [InlineKeyboardButton("🏅 تعديل لقب", callback_data=f"title_{uid}")],
        [InlineKeyboardButton("🔒 قفل/فتح اللقب", callback_data=f"lock_{uid}")]
    ]

    await q.message.reply_text("⚙️ إدارة العضو", reply_markup=InlineKeyboardMarkup(kb))

# ================= ACTION STATES =================
async def add(update, context):
    q = update.callback_query
    await q.answer()
    admin_state[ADMIN_ID] = ("add", int(q.data.split("_")[1]))
    await q.message.reply_text("أرسل النقاط")

async def sub(update, context):
    q = update.callback_query
    await q.answer()
    admin_state[ADMIN_ID] = ("sub", int(q.data.split("_")[1]))
    await q.message.reply_text("أرسل الخصم")

async def setp(update, context):
    q = update.callback_query
    await q.answer()
    admin_state[ADMIN_ID] = ("set", int(q.data.split("_")[1]))
    await q.message.reply_text("أرسل القيمة الجديدة")

async def title(update, context):
    q = update.callback_query
    await q.answer()
    admin_state[ADMIN_ID] = ("title", int(q.data.split("_")[1]))
    await q.message.reply_text("أرسل لقب جديد")

async def lock(update, context):
    q = update.callback_query
    uid = int(q.data.split("_")[1])

    c.execute("SELECT title_locked FROM users WHERE user_id=?", (uid,))
    l = c.fetchone()[0]

    new = 0 if l == 1 else 1
    c.execute("UPDATE users SET title_locked=? WHERE user_id=?", (new, uid))
    conn.commit()

    await q.answer("تم التبديل")

# ================= ALL USERS POINTS =================
async def all_points(update, context):
    q = update.callback_query
    await q.answer()

    admin_state[ADMIN_ID] = ("all", 0)
    await q.message.reply_text("أرسل النقاط للجميع")

# ================= HANDLE =================
async def handle(update, context):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    text = update.message.text.strip()

    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",(uid,name,0,0,"🌱 مبتدئ",0))
        conn.commit()

    # ADMIN ACTIONS
    if uid == ADMIN_ID and ADMIN_ID in admin_state:
        action,target = admin_state[ADMIN_ID]

        if action == "add":
            c.execute("UPDATE users SET points=points+? WHERE user_id=?",(int(text),target))

        elif action == "sub":
            c.execute("UPDATE users SET points=points-? WHERE user_id=?",(int(text),target))

        elif action == "set":
            c.execute("UPDATE users SET points=? WHERE user_id=?",(int(text),target))

        elif action == "title":
            c.execute("UPDATE users SET title=? WHERE user_id=?",(text,target))

        elif action == "all":
            c.execute("UPDATE users SET points=points+?", (int(text),))

        conn.commit()
        admin_state.pop(ADMIN_ID)
        await update.message.reply_text("✅ تم التنفيذ")
        return

    # REGISTER DEFAULT UPDATE
    c.execute("SELECT points,messages,title_locked FROM users WHERE user_id=?", (uid,))
    p,m,l = c.fetchone()

    old = get_title(p)
    p += 1
    m += 1
    new = get_title(p) if l == 0 else old

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",(p,m,new,uid))
    conn.commit()

    if new != old:
        await update.message.reply_text(f"🎉 ترقية: {new}")

# ================= ROUTER =================
async def cb(update, context):
    q = update.callback_query
    data = q.data
    await q.answer()

    if data == "admin":
        await admin(update, context)

    elif data == "users":
        await users(update, context)

    elif data.startswith("u_"):
        await user_panel(update, context)

    elif data.startswith("add_"):
        await add(update, context)

    elif data.startswith("sub_"):
        await sub(update, context)

    elif data.startswith("set_"):
        await setp(update, context)

    elif data.startswith("title_"):
        await title(update, context)

    elif data.startswith("lock_"):
        await lock(update, context)

    elif data == "all_points":
        await all_points(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(cb))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING")
app.run_polling()
