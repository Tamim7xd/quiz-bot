import os
import sqlite3
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================= ENV =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

if not TOKEN:
    raise Exception("BOT_TOKEN is missing")

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    title TEXT DEFAULT '🌱 جديد',
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
    ("ما عاصمة فرنسا؟", "باريس"),
    ("ما عاصمة مصر؟", "القاهرة"),
    ("ما أكبر كوكب؟", "المشتري"),
    ("من مكتشف الجاذبية؟", "نيوتن"),
    ("ما أطول نهر في العالم؟", "النيل"),
    ("ما عاصمة السعودية؟", "الرياض"),
    ("ما لغة اليابان؟", "اليابانية"),
]

def get_question():
    return random.choice(QUESTIONS)

# ================= TITLES SYSTEM =================
def get_title(messages):

    if messages <= 149:
        return "🌱 جديد"

    level = (messages - 150) // 100

    titles = [
        "🌿 مبتدئ","⚡ متعلم","🔥 نشيط","🚀 متفاعل","🎯 متقدم",
        "⭐ مميز","🏅 محترف","🥇 نجم","👑 قائد","💎 خبير",
        "🏆 أسطورة","⚔️ محارب","🛡️ حارس","🌟 سوبر ستار","💥 خارق",
        "🎮 لاعب","🧩 محلل","📚 مثقف","🌍 رحّالة","⚙️ عبقري"
    ]

    return titles[level] if level < len(titles) else "💠 أسطورة"

# ================= ADMIN MEMORY =================
admin_state = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id == ADMIN_ID:

        keyboard = [
            [InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="admin_panel")]
        ]

        await update.message.reply_text(
            "🔥 أهلاً أدمن",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("👋 أهلاً بك في البوت")

# ================= ADMIN PANEL =================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")]
    ]

    await q.message.reply_text(
        "🛠 لوحة الأدمن",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= USERS LIST =================
async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name FROM users LIMIT 30")
    users = c.fetchall()

    keyboard = []

    for u in users:
        keyboard.append([
            InlineKeyboardButton(f"👤 {u[1]}", callback_data=f"user_{u[0]}")
        ])

    await q.message.reply_text(
        "👥 اختر عضو:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= USER MENU =================
async def user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    keyboard = [
        [InlineKeyboardButton("📊 معلومات العضو", callback_data=f"info_{uid}")],
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data=f"addp_{uid}")],
        [InlineKeyboardButton("🏅 تعديل لقب", callback_data=f"title_{uid}")],
        [InlineKeyboardButton("🔓 إرجاع تلقائي", callback_data=f"unlock_{uid}")]
    ]

    await q.message.reply_text(
        "⚙️ إدارة العضو:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= USER INFO =================
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT name,points,title FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()

    if row:
        name, points, title = row

        await q.message.reply_text(
            f"""👤 معلومات العضو

🧑 الاسم: {name}
💰 النقاط: {points}
🏅 اللقب: {title}
"""
        )

# ================= ADMIN ACTION MEMORY =================
# (action, target_id)
admin_state = {}

# ================= ADD POINTS =================
async def add_points(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    admin_state[ADMIN_ID] = ("points", uid)

    await q.message.reply_text("💰 ارسل عدد النقاط")

# ================= SET TITLE =================
async def set_title(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    admin_state[ADMIN_ID] = ("title", uid)

    await q.message.reply_text("🏅 ارسل اللقب الجديد")

# ================= UNLOCK TITLE =================
async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute(
        "UPDATE users SET title_locked=0 WHERE user_id=?",
        (uid,)
    )

    conn.commit()

    await q.message.reply_text("🔓 تم إعادة اللقب للنظام التلقائي")

# ================= HANDLE MESSAGES =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text.strip()
    name = update.effective_user.first_name

    # ================= ADMIN MODE =================
    if uid == ADMIN_ID and ADMIN_ID in admin_state:

        action, target = admin_state[ADMIN_ID]

        if action == "points":

            try:
                amount = int(text)

                c.execute("SELECT points FROM users WHERE user_id=?", (target,))
                row = c.fetchone()

                if row:
                    new_points = row[0] + amount

                    c.execute(
                        "UPDATE users SET points=? WHERE user_id=?",
                        (new_points, target)
                    )

                    conn.commit()

                await update.message.reply_text("✅ تم إضافة النقاط")

            except:
                await update.message.reply_text("❌ خطأ في الرقم")

            admin_state.pop(ADMIN_ID)
            return

        if action == "title":

            c.execute(
                "UPDATE users SET title=?, title_locked=1 WHERE user_id=?",
                (text, target)
            )

            conn.commit()

            await update.message.reply_text("🏅 تم تثبيت اللقب")

            admin_state.pop(ADMIN_ID)
            return

    # ================= REGISTER =================
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():

        c.execute(
            "INSERT INTO users VALUES (?,?,0,0,'🌱 جديد',0)",
            (uid, name)
        )

        conn.commit()

    # ================= INFO =================
    if text == "معلوماتي":

        c.execute("SELECT points,messages,title FROM users WHERE user_id=?", (uid,))
        row = c.fetchone()

        points, messages, title = row if row else (0,0,"🌱 جديد")

        await update.message.reply_text(
            f"""✨ ─── معلوماتك ─── ✨

👤 الاسم: {name}
💬 الرسائل: {messages}
💰 النقاط: {points}
🏅 اللقب: {title}
"""
        )
        return

    # ================= QUESTION =================
    if text in ["سؤال", "سوال"]:

        q, a = get_question()

        c.execute("REPLACE INTO active_q VALUES (?,?)", (uid, a))
        conn.commit()

        await update.message.reply_text(f"❓ {q}")
        return

    # ================= ANSWER =================
    c.execute("SELECT answer FROM active_q WHERE user_id=?", (uid,))
    active = c.fetchone()

    if active:

        correct = active[0]

        if text.lower() == correct.lower():
            await update.message.reply_text("✅ صحيح +5 نقاط")
            add = 5
        else:
            await update.message.reply_text(f"❌ خطأ\nالإجابة: {correct}")
            add = 0

        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

    else:
        add = 1

    # ================= UPDATE USER =================
    c.execute("SELECT points,messages,title,title_locked FROM users WHERE user_id=?", (uid,))
    p, m, title, locked = c.fetchone()

    p += add
    m += 1

    # ================= TITLE SYSTEM =================
    old_title = title

    if locked == 0:
        new_title = get_title(m)
    else:
        new_title = title

    # ================= SAVE =================
    c.execute(
        "UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
        (p, m, new_title, uid)
    )

    conn.commit()

    # ================= ANNOUNCEMENT =================
    if locked == 0 and new_title != old_title:

        await update.message.reply_text(
            f"🎉 مبروك! حصلت على لقب: {new_title}"
        )

        if GROUP_ID:
            try:
                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=f"""🎊 ترقية جديدة!

👤 {name}
🏅 {new_title}
🔥 مبروك لقبك الجديد
"""
                )
            except:
                pass

# ================= ROUTER =================
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    data = q.data

    if data == "admin_panel":
        await panel(update, context)

    elif data == "users":
        await show_users(update, context)

    elif data.startswith("user_"):
        await user_menu(update, context)

    elif data.startswith("info_"):
        await user_info(update, context)

    elif data.startswith("addp_"):
        await add_points(update, context)

    elif data.startswith("title_"):
        await set_title(update, context)

    elif data.startswith("unlock_"):
        await unlock(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🚀 FULL SYSTEM BOT RUNNING")
app.run_polling()
