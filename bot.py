import os
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

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
messages INTEGER DEFAULT 0,
title TEXT DEFAULT '🌱 عضو جديد',
locked INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS active_q(
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
"🏆 Supreme","🌟 Apex","🎯 Boss","👑 GOD","💎 Final"
]

def level(p): return p // 200
def get_title(p): return TITLES[level(p)] if level(p) < len(TITLES) else TITLES[-1]

# ================= QUESTIONS =================
QUESTIONS = [
("ما عاصمة العراق؟", "بغداد"),
("ما عاصمة السعودية؟", "الرياض"),
("ما أكبر كوكب؟", "المشتري"),
("ما أطول نهر؟", "النيل"),
("ما لغة القرآن؟", "العربية"),
("كم عدد القارات؟", "7"),
("ما لون السماء؟", "أزرق"),
("ما أقرب كوكب للشمس؟", "عطارد"),
("ما الحيوان الأسرع؟", "الفهد"),
("ما عملة العراق؟", "الدينار")
]

def get_question():
    return random.choice(QUESTIONS)

# ================= REGISTER =================
def register(uid, name):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",
                  (uid, name, 0, 0, "🌱 عضو جديد", 0))
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
        [InlineKeyboardButton("📢 رسالة جماعية", callback_data="broadcast")]
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
    name, points, title = c.fetchone()

    kb = [
        [InlineKeyboardButton("➕ إضافة", callback_data=f"add_{uid}")],
        [InlineKeyboardButton("➖ خصم", callback_data=f"sub_{uid}")],
        [InlineKeyboardButton("🎖 لقب", callback_data=f"title_{uid}")],
        [InlineKeyboardButton("📢 تنبيه", callback_data=f"alert_{uid}")],
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
    state["a"] = ("add", int(q.data.split("_")[1]))
    await q.message.reply_text("➕ أرسل النقاط")

async def sub(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("sub", int(q.data.split("_")[1]))
    await q.message.reply_text("➖ أرسل الخصم")

async def title_set(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("title", int(q.data.split("_")[1]))
    await q.message.reply_text("🎖 أرسل اللقب")

async def alert(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("alert", int(q.data.split("_")[1]))
    await q.message.reply_text("📢 أرسل التنبيه")

async def broadcast(update, context):
    q = update.callback_query
    await q.answer()
    state["a"] = ("broadcast", 0)
    await q.message.reply_text("📢 أرسل رسالة جماعية")

# ================= GROUP DISCOUNT =================
async def group_discount(update: Update, context):

    text = update.message.text

    if text.startswith("$خصم") and update.message.reply_to_message:

        if update.effective_user.id != ADMIN_ID:
            return

        parts = text.split(" ",2)
        amount = int(parts[1])
        reason = parts[2] if len(parts)>2 else "بدون سبب"

        target = update.message.reply_to_message.from_user

        c.execute("SELECT points FROM users WHERE user_id=?", (target.id,))
        row = c.fetchone()

        if row:
            new = max(0, row[0] - amount)
            c.execute("UPDATE users SET points=? WHERE user_id=?", (new, target.id))
            conn.commit()

        await context.bot.send_message(
            GROUP_ID,
            f"📉 خصم\n👤 {target.first_name}\n➖ {amount}\n📝 {reason}"
        )

# ================= QUESTIONS =================
async def question_trigger(update: Update, context):

    text = update.message.text

    if text in ["سؤال", "سوال"]:
        q, a = get_question()

        c.execute("REPLACE INTO active_q VALUES (?,?)", (update.effective_user.id, a))
        conn.commit()

        await update.message.reply_text(f"❓ {q}")
        return True

    return False

# ================= ANSWER CHECK =================
def check_answer(uid, text):
    c.execute("SELECT answer FROM active_q WHERE user_id=?", (uid,))
    row = c.fetchone()

    if row:
        correct = row[0]

        if text.lower() == correct.lower():
            add = 5
            msg = "✅ صحيح +5"
        else:
            add = 0
            msg = f"❌ خطأ الإجابة: {correct}"

        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

        return add, msg

    return 1, None

# ================= HANDLE =================
async def handle(update: Update, context):

    uid = update.effective_user.id
    text = update.message.text
    name = update.effective_user.first_name

    register(uid, name)

    await group_discount(update, context)

    if await question_trigger(update, context):
        return

    add, msg = check_answer(uid, text)

    if uid == ADMIN_ID and "a" in state:

        action, target = state["a"]

        c.execute("SELECT name,points FROM users WHERE user_id=?", (target,))
        uname, points = c.fetchone()

        if action == "add":
            points += int(text)
            out = f"➕ إضافة {text}"

        elif action == "sub":
            points = max(0, points - int(text))
            out = f"➖ خصم {text}"

        elif action == "title":
            c.execute("UPDATE users SET title=? WHERE user_id=?", (text, target))
            conn.commit()
            await update.message.reply_text("🎖 تم")
            state.pop("a")
            return

        elif action == "alert":
            await context.bot.send_message(target, f"📢 تنبيه: {text}")
            await context.bot.send_message(GROUP_ID, f"📢 تنبيه لـ {uname}")
            state.pop("a")
            return

        elif action == "broadcast":
            await context.bot.send_message(GROUP_ID, f"📢 {text}")
            state.pop("a")
            return

        c.execute("UPDATE users SET points=? WHERE user_id=?", (points, target))
        conn.commit()

        new_title = get_title(points)

        await context.bot.send_message(
            GROUP_ID,
            f"📊 تحديث\n👤 {uname}\n{out}\n💰 {points}\n🏅 {new_title}"
        )

        state.pop("a")
        return

    c.execute("SELECT points,title FROM users WHERE user_id=?", (uid,))
    p,t = c.fetchone()

    p += add

    c.execute("UPDATE users SET points=? WHERE user_id=?", (p, uid))
    conn.commit()

    new_title = get_title(p)

    if msg:
        await update.message.reply_text(msg)

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
        await title_set(update, context)

    elif d.startswith("alert_"):
        await alert(update, context)

    elif d == "broadcast":
        await broadcast(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT FULL SYSTEM RUNNING")
app.run_polling()
