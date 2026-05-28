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
CREATE TABLE IF NOT EXISTS questions (
user_id INTEGER PRIMARY KEY,
answer TEXT
)
""")

conn.commit()

# ================= STATE =================
state = {}

# ================= 50 TITLES =================
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

# ================= SYSTEM =================
def register(uid, name):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",
                  (uid, name, 0, 0, "🌱 عضو جديد", 0))
        conn.commit()

def level(points):
    return points // 200

def progress(points):
    return points % 200

def get_title(points):
    lvl = level(points)
    return TITLES[lvl] if lvl < len(TITLES) else TITLES[-1]

def xp_bar(points):
    return "█" * (progress(points)//20) + "░" * (10 - (progress(points)//20))

def question():
    return random.choice([
        ("ما عاصمة العراق؟","بغداد"),
        ("ما عاصمة فرنسا؟","باريس"),
        ("ما أكبر دولة؟","روسيا"),
        ("ما أصغر دولة؟","الفاتيكان"),
        ("ما أطول نهر؟","النيل"),
        ("ما غاز التنفس؟","الأكسجين"),
        ("كم عدد القارات؟","7"),
        ("ما قبلة المسلمين؟","الكعبة"),
        ("من أول نبي؟","آدم"),
        ("ما أكبر كوكب؟","المشتري")
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text("👋 أهلاً بك في النظام")

# ================= ADMIN PANEL =================
async def admin(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📊 إحصائيات", callback_data="stats")]
    ]

    await update.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= USERS =================
async def users(update: Update, context):
    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name,points FROM users ORDER BY points DESC LIMIT 25")
    rows = c.fetchall()

    kb = [[InlineKeyboardButton(f"{n} | {p}", callback_data=f"user_{i}")] for i,n,p in rows]

    await q.message.reply_text("👥 الأعضاء", reply_markup=InlineKeyboardMarkup(kb))

# ================= PROFILE =================
async def profile(update: Update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT name,points,title,locked FROM users WHERE user_id=?", (uid,))
    name, points, title, locked = c.fetchone()

    kb = [
        [InlineKeyboardButton("➕ إضافة", callback_data=f"add_{uid}")],
        [InlineKeyboardButton("➖ خصم", callback_data=f"sub_{uid}")],
        [InlineKeyboardButton("🔒 قفل/فتح", callback_data=f"lock_{uid}")],
        [InlineKeyboardButton("📨 سؤال", callback_data=f"q_{uid}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="users")]
    ]

    await q.message.reply_text(f"""
👤 {name}

💰 النقاط: {points}
🎖 اللقب: {title}
🔒 الحالة: {"مقفول" if locked else "مفتوح"}
📊 المستوى: {level(points)}
{xp_bar(points)} {progress(points)}/200
""", reply_markup=InlineKeyboardMarkup(kb))

# ================= ADD / SUB =================
async def add(update, context):
    q = update.callback_query
    await q.answer()
    state["action"] = ("add", int(q.data.split("_")[1]))
    await q.message.reply_text("➕ أرسل العدد")

async def sub(update, context):
    q = update.callback_query
    await q.answer()
    state["action"] = ("sub", int(q.data.split("_")[1]))
    await q.message.reply_text("➖ أرسل العدد")

# ================= LOCK =================
async def lock(update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT locked FROM users WHERE user_id=?", (uid,))
    l = c.fetchone()[0]

    c.execute("UPDATE users SET locked=? WHERE user_id=?", (0 if l else 1, uid))
    conn.commit()

    await q.message.reply_text("🔄 تم التبديل")

# ================= QUESTIONS =================
async def handle(update: Update, context):

    uid = update.effective_user.id
    text = update.message.text

    register(uid, update.effective_user.first_name)

    # ===== ADMIN ACTION =====
    if uid == ADMIN_ID and "action" in state:

        action, target = state["action"]

        c.execute("SELECT points,name FROM users WHERE user_id=?", (target,))
        points, name = c.fetchone()

        old_title = get_title(points)

        if action == "add":
            points += int(text)
        else:
            points -= int(text)
            if points < 0:
                points = 0

        new_title = get_title(points)

        c.execute("UPDATE users SET points=? WHERE user_id=?", (points, target))
        conn.commit()

        await update.message.reply_text(f"✅ {name} → {points}")

        # 🔥 إشعار ترقية
        if new_title != old_title:
            await context.bot.send_message(
                GROUP_ID,
                f"🎉 ترقية جديدة!\n👤 {name}\n🏅 {new_title}"
            )

        state.pop("action")
        return

    # ===== QUESTION =====
    if text in ["سؤال","سوال"]:
        q,a = question()
        c.execute("REPLACE INTO questions VALUES (?,?)", (uid,a))
        conn.commit()
        await update.message.reply_text(q)
        return

    c.execute("SELECT answer FROM questions WHERE user_id=?", (uid,))
    row = c.fetchone()

    add = 1

    if row:
        if text.lower() == row[0].lower():
            add = 5
            await update.message.reply_text("✅ صحيح +5")
        else:
            await update.message.reply_text(f"❌ خطأ: {row[0]}")

        c.execute("DELETE FROM questions WHERE user_id=?", (uid,))
        conn.commit()

    # ===== UPDATE USER =====
    c.execute("SELECT points,messages,title,locked,name FROM users WHERE user_id=?", (uid,))
    points,msg,title,locked,name = c.fetchone()

    old = get_title(points)

    points += add
    msg += 1

    new = get_title(points) if locked == 0 else title

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
              (points,msg,new,uid))
    conn.commit()

    await update.message.reply_text(f"""
💰 {points}
🎖 {new}
📊 {xp_bar(points)}
""")

    if old != new:
        await context.bot.send_message(
            GROUP_ID,
            f"🎉 ترقية!\n👤 {name}\n🏅 {new}"
        )

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

    elif d.startswith("lock_"):
        await lock(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT V4 RUNNING")
app.run_polling()
