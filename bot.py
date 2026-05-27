import os
import random
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    title TEXT DEFAULT '👶 مبتدئ'
)
""")
conn.commit()

# ================= STATE =================
state = {}
active_q = {}

# ================= TITLES (25 LEVELS) =================
def get_title(points):
    levels = [
        (0, "👶 مبتدئ"),
        (50, "🌱 متعلم"),
        (100, "🥉 نشط"),
        (200, "🥈 جيد"),
        (300, "🥇 محترف"),
        (500, "🔥 خبير"),
        (800, "⚡ متقدم"),
        (1200, "🚀 قوي"),
        (2000, "🏆 أسطورة"),
        (3000, "👑 ملك"),
        (5000, "💎 أسطوري"),
        (7000, "⚔️ محارب"),
        (9000, "🧠 عبقري"),
        (12000, "🌌 أسطورة العالم"),
        (15000, "💀 مرعب"),
        (18000, "🚀 فضائي"),
        (21000, "👑 ملك الملوك"),
        (25000, "🔥 نار"),
        (30000, "💠 نادر"),
        (35000, "🌀 خارق"),
        (40000, "🏆 بطل"),
        (50000, "💎 لا يُهزم"),
        (70000, "⚡ أسطورة مطلقة"),
        (90000, "🧿 حكيم"),
        (120000, "🔱 قائد"),
    ]

    title = "👶 مبتدئ"
    for p, t in levels:
        if points >= p:
            title = t
    return title


def update_title(uid):
    cursor.execute("SELECT points FROM users WHERE user_id=?", (str(uid),))
    row = cursor.fetchone()
    if not row:
        return

    title = get_title(row[0])
    cursor.execute("UPDATE users SET title=? WHERE user_id=?", (title, str(uid)))
    conn.commit()

# ================= USERS =================
def create_user(uid, name):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (str(uid),))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users VALUES (?,?,?,?,?)",
            (str(uid), name, 0, 0, "👶 مبتدئ")
        )
        conn.commit()


def get_user(uid):
    cursor.execute("SELECT points,messages,title,name FROM users WHERE user_id=?", (str(uid),))
    return cursor.fetchone()


def set_user(uid, field, value):
    cursor.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, str(uid)))
    conn.commit()

# ================= QUESTIONS (150+) =================
QUESTIONS = []

for _ in range(100):
    a = random.randint(1, 50)
    b = random.randint(1, 50)
    QUESTIONS.append((f"كم {a}+{b}؟", str(a+b)))

for _ in range(50):
    a = random.randint(50, 200)
    b = random.randint(10, 100)
    QUESTIONS.append((f"كم {a}+{b}؟", str(a+b)))

QUESTIONS += [
    ("ما عاصمة العراق؟", "بغداد"),
    ("ما عاصمة فرنسا؟", "باريس"),
    ("ما عدد الكواكب؟", "8"),
    ("ما أكبر كوكب؟", "المشتري"),
    ("ما أعلى جبل؟", "إيفرست"),
]

# ================= MENUS =================
def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 المستخدمين", callback_data="users")],
        [InlineKeyboardButton("👥 عرض ID", callback_data="ids")],
        [InlineKeyboardButton("💰 نقاط جماعية", callback_data="global")]
    ])


def user_menu(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ نقاط", callback_data=f"p:{uid}")],
        [InlineKeyboardButton("📨 رسائل", callback_data=f"m:{uid}")],
        [InlineKeyboardButton("🏷️ لقب", callback_data=f"t:{uid}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="users")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    create_user(uid, update.effective_user.first_name)

    if uid == ADMIN_ID:
        await update.message.reply_text("👑 لوحة الإدارة", reply_markup=admin_menu())
    else:
        await update.message.reply_text("👋 اكتب: سوال / معلوماتي / top")

# ================= MAIN CHAT =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    create_user(uid, update.effective_user.first_name)

    if text in ["سوال", "سؤال"]:
        q, a = random.choice(QUESTIONS)
        active_q[uid] = a
        await update.message.reply_text(q)
        return

    if text == "معلوماتي":
        p, m, t, n = get_user(uid)
        await update.message.reply_text(f"👤 {n}\n⭐ {p}\n📨 {m}\n🏷️ {t}")
        return

    if text == "top":
        cursor.execute("SELECT name,points FROM users ORDER BY points DESC LIMIT 10")
        rows = cursor.fetchall()

        msg = "🏆 TOP 10\n\n"
        for i, r in enumerate(rows, 1):
            msg += f"{i}) {r[0]} ⭐ {r[1]}\n"

        await update.message.reply_text(msg)
        return

    if uid in active_q:
        if text.lower() == active_q[uid].lower():
            p, m, t, n = get_user(uid)
            set_user(uid, "points", p + 1)
            update_title(uid)
            del active_q[uid]
            await update.message.reply_text("✔️ صحيح +1")

# ================= CALLBACK =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    if uid != ADMIN_ID:
        return

    # USERS
    if data == "users":
        cursor.execute("SELECT user_id,name,points FROM users")
        rows = cursor.fetchall()

        keyboard = [
            [InlineKeyboardButton(f"{r[1]} ⭐{r[2]}", callback_data=f"user:{r[0]}")]
            for r in rows
        ]

        await q.edit_message_text("👤 المستخدمين", reply_markup=InlineKeyboardMarkup(keyboard))

    # IDS
    elif data == "ids":
        cursor.execute("SELECT user_id,name FROM users")
        rows = cursor.fetchall()

        text = "👥 الأعضاء + ID\n\n"
        for r in rows:
            text += f"{r[1]}\n🆔 {r[0]}\n\n"

        await q.edit_message_text(text)

    # OPEN USER
    elif data.startswith("user:"):
        target = data.split(":")[1]
        state[uid] = {"target": target}
        await q.edit_message_text("⚙️ اختر:", reply_markup=user_menu(target))

    # EDIT POINTS
    elif data.startswith("p:"):
        state[uid] = {"target": data.split(":")[1], "mode": "points"}
        await q.edit_message_text("⭐ ارسل النقاط")

    # EDIT MSG
    elif data.startswith("m:"):
        state[uid] = {"target": data.split(":")[1], "mode": "messages"}
        await q.edit_message_text("📨 ارسل الرسائل")

    # EDIT TITLE
    elif data.startswith("t:"):
        state[uid] = {"target": data.split(":")[1], "mode": "title"}
        await q.edit_message_text("🏷️ ارسل اللقب")

    # GLOBAL
    elif data == "global":
        state[uid] = {"mode": "global"}
        await q.edit_message_text("💰 ارسل النقاط الجماعية")

# ================= STATE =================
async def state_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    if uid not in state:
        return

    s = state[uid]
    target = s.get("target")

    try:
        if s["mode"] == "points":
            set_user(target, "points", int(text))
            update_title(target)

        elif s["mode"] == "messages":
            set_user(target, "messages", int(text))

        elif s["mode"] == "title":
            set_user(target, "title", text)

        elif s["mode"] == "global":
            cursor.execute("UPDATE users SET points = points + ?", (int(text),))
            conn.commit()

    except:
        await update.message.reply_text("❌ خطأ")

    del state[uid]
    await update.message.reply_text("✔️ تم التنفيذ")

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, state_handler))

    print("BOT RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
