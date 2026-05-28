import os
import sqlite3
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

# ================= DB =================
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
("ما عاصمة العراق؟","بغداد"),
("ما عاصمة السعودية؟","الرياض"),
("ما أكبر قارة؟","آسيا"),
("ما أصغر قارة؟","أستراليا"),
("ما أطول نهر؟","النيل"),
("ما أكبر دولة عربية؟","الجزائر"),
("ما لغة القرآن؟","العربية"),
]

def get_question():
    return random.choice(QUESTIONS)

# ================= TITLES (50 LEVELS) =================
TITLES = [
"🌱 عضو جديد","🌿 مبتدئ","⚡ نشيط","🔥 متفاعل","🚀 متقدم",
"🎯 محترف","⭐ مميز","🏅 بطل","🥇 نجم","👑 قائد",
"💎 خبير","🏆 أسطورة","⚔️ محارب","🛡️ حارس","🌟 سوبر ستار",
"💥 خارق","🎮 لاعب","🧠 ذكي","📚 مثقف","🌍 رحّالة",
"💠 ملك","👑 أسطورة عليا","🔥 Legend","⚡ Elite","💎 Pro Max",
"🏆 Titan","👑 King","🔥 Beast","⚡ Ultra","💎 Diamond",
"🏆 Master","👑 Lord","🔥 Hero","⚡ Genius","💎 Supreme",
"🏆 Omega","👑 Phantom","🔥 Ghost","⚡ Storm","💎 Nova",
"🏆 Cosmic","👑 Infinity","🔥 Divine","⚡ Myth","💎 Eternal",
"🏆 Ultra Legend","👑 Supreme King","🔥 Final Boss","⚡ GOD MODE","💎 LEGEND+"
]

# ================= MEMORY =================
admin_state = {}

# ================= LEVEL =================
def level(points):
    return points // 200

def progress(points):
    return points % 200

def bar(points):
    p = progress(points) // 20
    return "█" * p + "░" * (10 - p)

def get_title(points):
    return TITLES[min(level(points), len(TITLES)-1)]

# ================= START =================
async def start(update, context):
    await update.message.reply_text("👋 أهلاً بك")

# ================= ADMIN PANEL =================
async def panel(update, context):
    q = update.callback_query
    await q.answer()

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("➕ نقاط", callback_data="addall")],
        [InlineKeyboardButton("➖ خصم", callback_data="suball")],
        [InlineKeyboardButton("📢 إرسال للقناة", callback_data="pin")]
    ]

    await q.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= USERS =================
async def users(update, context):
    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name,points FROM users LIMIT 20")
    rows = c.fetchall()

    kb = [[InlineKeyboardButton(f"{n} ({p})", callback_data=f"user_{i}")] for i,n,p in rows]

    await q.message.reply_text("👥 المستخدمين", reply_markup=InlineKeyboardMarkup(kb))

# ================= USER MENU =================
async def user_menu(update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    kb = [
        [InlineKeyboardButton("➕ إضافة", callback_data=f"add_{uid}")],
        [InlineKeyboardButton("➖ خصم", callback_data=f"sub_{uid}")],
        [InlineKeyboardButton("🔒 قفل/فتح", callback_data=f"lock_{uid}")],
    ]

    await q.message.reply_text("⚙️ إدارة", reply_markup=InlineKeyboardMarkup(kb))

# ================= LOCK =================
async def lock(update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT title_locked FROM users WHERE user_id=?", (uid,))
    r = c.fetchone()

    new = 0 if r and r[0] == 1 else 1

    c.execute("UPDATE users SET title_locked=? WHERE user_id=?", (new, uid))
    conn.commit()

    await q.message.reply_text("🔒 تم القفل" if new else "🔓 تم الفتح")

# ================= ADMIN ACTION =================
async def action(update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])
    admin_state[ADMIN_ID] = (q.data.split("_")[0], uid)
    await q.message.reply_text("💰 أرسل الرقم")

# ================= PIN =================
async def pin(update, context):
    q = update.callback_query
    await q.answer()
    admin_state[ADMIN_ID] = ("pin", None)
    await q.message.reply_text("📢 ارسل الرسالة")

# ================= HANDLE =================
async def handle(update, context):
    uid = update.effective_user.id
    text = update.message.text.strip()
    name = update.effective_user.first_name

    # REGISTER
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,0,0,'🌱 عضو جديد',0)", (uid, name))
        conn.commit()

    # ================= ADMIN =================
    if uid == ADMIN_ID and ADMIN_ID in admin_state:
        action, target = admin_state[ADMIN_ID]

        # PIN
        if action == "pin":
            msg = await context.bot.send_message(GROUP_ID, text)

            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📌 تثبيت", callback_data=f"pin_yes_{msg.message_id}"),
                    InlineKeyboardButton("❌ بدون", callback_data=f"pin_no_{msg.message_id}")
                ]
            ])

            await context.bot.send_message(GROUP_ID, "هل تريد التثبيت؟", reply_markup=kb)

            admin_state.pop(ADMIN_ID)
            return

        amount = int(text)

        if action == "add":
            c.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, target))
        elif action == "sub":
            c.execute("UPDATE users SET points = points - ? WHERE user_id=?", (amount, target))

        conn.commit()
        admin_state.pop(ADMIN_ID)
        await update.message.reply_text("✅ تم التنفيذ")
        return

    # ================= $خصم بالرد =================
    if update.message.reply_to_message and text.startswith("$خصم"):
        parts = text.split(" ", 2)
        amount = int(parts[1])
        reason = parts[2] if len(parts) > 2 else "بدون سبب"

        target = update.message.reply_to_message.from_user

        c.execute("SELECT name,points FROM users WHERE user_id=?", (target.id,))
        row = c.fetchone()

        if not row:
            name_db = target.first_name
            points = 0
            c.execute("INSERT INTO users VALUES (?,?,0,0,'🌱 عضو جديد',0)", (target.id, name_db))
        else:
            name_db, points = row

        new = points - amount

        c.execute("UPDATE users SET points=? WHERE user_id=?", (new, target.id))
        conn.commit()

        await update.message.reply_text(
f"""⚠️ خصم نقاط

👤 {name_db}
💰 -{amount}
🧮 {new}
📝 {reason}
"""
        )
        return

    # ================= POINTS =================
    c.execute("SELECT points,messages,title_locked FROM users WHERE user_id=?", (uid,))
    p, m, locked = c.fetchone()

    old_level = level(p)

    p += 1
    m += 1

    new_level = level(p)

    if locked == 0:
        title = get_title(p)
    else:
        title = get_title(old_level * 200)

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
              (p, m, title, uid))
    conn.commit()

    # ================= LEVEL UP =================
    if new_level > old_level:
        await update.message.reply_text(
f"""🎉 ترقية!

🏆 {title}
📊 المستوى: {new_level}
📈 {bar(p)}
🔥 عاشت إيدك يا بطل 😂"""
        )

# ================= ROUTER =================
async def router(update, context):
    q = update.callback_query
    d = q.data

    if d == "admin": await panel(update, context)
    elif d == "users": await users(update, context)
    elif d.startswith("user_"): await user_menu(update, context)
    elif d.startswith("add_") or d.startswith("sub_"): await action(update, context)
    elif d.startswith("lock_"): await lock(update, context)
    elif d == "pin": await pin(update, context)

    elif d.startswith("pin_yes_"):
        await context.bot.pin_chat_message(GROUP_ID, int(d.split("_")[2]))
        await q.message.reply_text("📌 تم التثبيت")

    elif d.startswith("pin_no_"):
        await q.message.reply_text("❌ بدون تثبيت")

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING 🚀")
app.run_polling()
