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
    title TEXT DEFAULT '🟢 عضو جديد',
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
("ما عاصمة مصر؟", "القاهرة"),
("ما أكبر قارة؟", "آسيا"),
("ما أصغر قارة؟", "أستراليا"),
("ما أعلى جبل؟", "إيفرست"),
("ما أطول نهر؟", "النيل"),
("ما لغة القرآن؟", "العربية"),
("كم عدد الصلوات؟", "5"),
("ما الحيوان الأسرع؟", "الفهد"),
]

def get_question():
    return random.choice(QUESTIONS)

# ================= TITLES (50 LEVELS + COLORS) =================
TITLES = [
"🟢 عضو جديد","🟢 مبتدئ","🟢 متعلم","🟢 نشيط","🟢 متفاعل",
"🔵 محترف","🔵 قوي","🔵 بارع","🔵 متقدم","🔵 خبير",
"🟣 نجم","🟣 محلل","🟣 لاعب ذكي","🟣 أسطورة صغيرة","🟣 مميز",
"🟡 قائد","🟡 بطل","🟡 ملك الأداء","🟡 محترف جداً","🟡 أسطورة",
"🟠 محارب","🟠 سيد اللعبة","🟠 أسطورة قوية","🟠 أسطورة نادرة","🟠 بطل خارق",
"🔴 أسطورة","🔴 ملك","🔴 ملك الأساطير","🔴 أسطورة ذهبية","🔴 أسطورة نارية",
"⚫ كيان","⚫ قوة مطلقة","⚫ سيد الظلام","⚫ أسطورة الظل","⚫ خارق",
"💎 ماس","💎 نجم لامع","💎 قوة خارقة","💎 أسطورة خالدة","💎 لؤلؤة",
"👑 ملك الملوك","👑 سيد العالم","👑 أسطورة الملوك","👑 أسطورة نهائية","👑 ملك الأساطير",
"🔥 بطل النهايات","🚀 متجاوز الحدود","🌌 كيان أسطوري","⚡ قوة لا توقف","🏆 الأسطورة الكبرى"
]

def get_title(points):
    level = points // 200
    return TITLES[level] if level < len(TITLES) else TITLES[-1]

# ================= PROGRESS =================
def get_progress(points):
    base = 200
    current = points % base
    percent = int((current / base) * 100)
    bar = "🟩" * (percent // 10) + "⬜" * (10 - percent // 10)
    return bar, percent

# ================= ADMIN STATE =================
admin_state = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        keyboard = [[InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="admin")]]
        await update.message.reply_text("🔥 أهلاً أدمن", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("👋 أهلاً بك في البوت")

# ================= ADMIN PANEL =================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton("👥 المستخدمين", callback_data="users")],
        [InlineKeyboardButton("📢 إرسال للقناة + تثبيت", callback_data="send_channel")]
    ]

    await q.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= USERS =================
async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name FROM users LIMIT 30")
    rows = c.fetchall()

    keyboard = [[InlineKeyboardButton(n, callback_data=f"user_{i}")] for i, n in rows]

    await q.message.reply_text("👥 المستخدمين:", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= USER MENU =================
async def user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    keyboard = [
        [InlineKeyboardButton("➕ نقاط", callback_data=f"add_{uid}")],
        [InlineKeyboardButton("🏅 لقب", callback_data=f"title_{uid}")],
        [InlineKeyboardButton("🔒 قفل/فتح اللقب", callback_data=f"lock_{uid}")]
    ]

    await q.message.reply_text("⚙️ إدارة المستخدم", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= ADMIN ACTIONS =================
async def add_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])
    admin_state[ADMIN_ID] = ("points", uid)
    await q.message.reply_text("💰 ارسل النقاط")

async def set_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])
    admin_state[ADMIN_ID] = ("title", uid)
    await q.message.reply_text("🏅 ارسل اللقب")

async def lock_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT title_locked FROM users WHERE user_id=?", (uid,))
    locked = c.fetchone()[0]

    new = 0 if locked else 1
    c.execute("UPDATE users SET title_locked=? WHERE user_id=?", (new, uid))
    conn.commit()

    await q.message.reply_text("🔒 تم تغيير حالة القفل")

# ================= SEND TO CHANNEL =================
async def send_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    admin_state[ADMIN_ID] = ("channel", None)
    await q.message.reply_text("📢 ارسل الرسالة الآن (ستُرسل وتُثبت)")

# ================= HANDLE =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text.strip()
    name = update.effective_user.first_name

    # register
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,0,0,'🟢 عضو جديد',0)", (uid, name))
        conn.commit()

    # admin actions
    if uid == ADMIN_ID and ADMIN_ID in admin_state:

        action, target = admin_state[ADMIN_ID]

        if action == "points":
            amount = int(text)

            c.execute("SELECT points FROM users WHERE user_id=?", (target,))
            p = c.fetchone()[0]

            c.execute("UPDATE users SET points=? WHERE user_id=?", (p + amount, target))
            conn.commit()

            await update.message.reply_text("✅ تم إضافة النقاط")
            admin_state.pop(ADMIN_ID)
            return

        if action == "title":
            c.execute("UPDATE users SET title=?, title_locked=1 WHERE user_id=?", (text, target))
            conn.commit()

            await update.message.reply_text("🏅 تم تعيين اللقب")
            admin_state.pop(ADMIN_ID)
            return

        if action == "channel":
            try:
                msg = await context.bot.send_message(chat_id=GROUP_ID, text=text)
                await context.bot.pin_chat_message(chat_id=GROUP_ID, message_id=msg.message_id)
                await update.message.reply_text("📢 تم الإرسال والتثبيت")
            except:
                await update.message.reply_text("❌ خطأ في الإرسال")

            admin_state.pop(ADMIN_ID)
            return

    # question
    if text in ["سؤال", "سوال"]:
        q, a = get_question()
        c.execute("REPLACE INTO active_q VALUES (?,?)", (uid, a))
        conn.commit()

        await update.message.reply_text(f"❓ {q}")
        return

    # answer
    c.execute("SELECT answer FROM active_q WHERE user_id=?", (uid,))
    active = c.fetchone()

    add = 1

    if active:
        if text.lower() == active[0].lower():
            add = 5
            await update.message.reply_text("✅ صحيح +5 نقاط")

        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

    # update user
    c.execute("SELECT points,messages,title_locked FROM users WHERE user_id=?", (uid,))
    p, m, locked = c.fetchone()

    old_level = p // 200

    p += add
    m += 1

    new_level = p // 200

    if locked == 0:
        title = get_title(p)
    else:
        title = c.execute("SELECT title FROM users WHERE user_id=?", (uid,)).fetchone()[0]

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
              (p, m, title, uid))
    conn.commit()

    # LEVEL UP REWARD
    if new_level > old_level:
        reward = random.randint(20, 100)
        p += reward

        c.execute("UPDATE users SET points=? WHERE user_id=?", (p, uid))
        conn.commit()

        await update.message.reply_text(
            f"🎉 ترقية مستوى!\n🎁 +{reward} نقطة\n🔥 مبروك!"
        )

    # info
    if text == "معلوماتي":
        bar, percent = get_progress(p)

        await update.message.reply_text(
            f"""
👤 {name}
💰 {p} نقطة
🏅 {title}

📊 {bar} {percent}%
"""
        )

# ================= ROUTER =================
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    data = q.data

    if data == "admin":
        await admin_panel(update, context)

    elif data == "users":
        await show_users(update, context)

    elif data.startswith("user_"):
        await user_menu(update, context)

    elif data.startswith("add_"):
        await add_points(update, context)

    elif data.startswith("title_"):
        await set_title(update, context)

    elif data.startswith("lock_"):
        await lock_title(update, context)

    elif data == "send_channel":
        await send_channel(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🚀 BOT FULL SYSTEM RUNNING")
app.run_polling()
