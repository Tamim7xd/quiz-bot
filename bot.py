import os
import random
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

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

# ================= STATE خفيف جدًا =================
context_state = {}

# ================= TITLES 25 =================
TITLES = [
    (0, "👶 مبتدئ"),
    (50, "🌱 متعلم"),
    (100, "🥉 نشط"),
    (200, "🥈 جيد"),
    (300, "🥇 محترف"),
    (500, "🔥 خبير"),
    (800, "⚡ متقدم"),
    (1200, "🚀 قوي"),
    (1500, "🏆 أسطورة"),
    (2000, "👑 ملك"),
    (2500, "💎 مميز"),
    (3000, "⚔️ مقاتل"),
    (4000, "🧠 ذكي"),
    (5000, "🌌 خارق"),
    (6000, "💀 مرعب"),
    (7000, "🚀 فضائي"),
    (8000, "👑 ملك الملوك"),
    (9000, "🔥 نار"),
    (10000, "💠 نادر"),
    (12000, "🌀 أسطوري"),
    (15000, "🏆 بطل"),
    (20000, "💎 لا يُهزم"),
    (30000, "⚡ أسطورة مطلقة"),
    (50000, "🧿 حكيم"),
    (100000, "🔱 قائد"),
]

def calc_title(points):
    t = "👶 مبتدئ"
    for p, name in TITLES:
        if points >= p:
            t = name
    return t

# ================= DB =================
def create_user(uid, name):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)",
                   (str(uid), name, 0, 0, "👶 مبتدئ"))
    conn.commit()


def get_user(uid):
    cursor.execute("SELECT points,messages,title,name FROM users WHERE user_id=?", (str(uid),))
    return cursor.fetchone()


def update(uid, field, value):
    cursor.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, str(uid)))
    conn.commit()


def refresh_title(uid):
    p = get_user(uid)[0]
    update(uid, "title", calc_title(p))

# ================= QUESTIONS 150+ =================
QUESTIONS = []

for i in range(120):
    a = random.randint(1, 100)
    b = random.randint(1, 100)
    QUESTIONS.append((f"كم {a}+{b}؟", str(a+b)))

QUESTIONS += [
    ("ما عاصمة العراق؟", "بغداد"),
    ("ما عاصمة فرنسا؟", "باريس"),
    ("ما عدد الكواكب؟", "8"),
    ("ما أكبر كوكب؟", "المشتري"),
    ("ما أعلى جبل؟", "إيفرست"),
]

active_q = {}

# ================= MENUS =================
def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 المستخدمين", callback_data="users")],
        [InlineKeyboardButton("📊 TOP", callback_data="top")]
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

    # ===== سؤال =====
    if text in ["سوال", "سؤال"]:
        q, a = random.choice(QUESTIONS)
        active_q[uid] = a
        await update.message.reply_text(q)
        return

    # ===== معلوماتي =====
    if text == "معلوماتي":
        p, m, t, n = get_user(uid)
        await update.message.reply_text(f"👤 {n}\n⭐ {p}\n📨 {m}\n🏷️ {t}")
        return

    # ===== TOP =====
    if text == "top":
        cursor.execute("SELECT name,points FROM users ORDER BY points DESC LIMIT 10")
        rows = cursor.fetchall()

        msg = "🏆 TOP 10\n\n"
        for i, r in enumerate(rows, 1):
            msg += f"{i}) {r[0]} ⭐ {r[1]}\n"

        await update.message.reply_text(msg)
        return

    # ===== ANSWER =====
    if uid in active_q:
        if text.lower() == active_q[uid].lower():
            p, m, t, n = get_user(uid)
            update(uid, "points", p + 1)
            refresh_title(uid)
            del active_q[uid]
            await update.message.reply_text("✔️ صحيح +1")

    # ===== TITLE EDIT (كتابة فقط) =====
    if uid in context_state and context_state[uid]["mode"] == "title":
        target = context_state[uid]["target"]
        update(target, "title", text)
        del context_state[uid]
        await update.message.reply_text("✔️ تم تعديل اللقب")
        return

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

    # OPEN USER
    elif data.startswith("user:"):
        target = data.split(":")[1]
        context_state[uid] = {"target": target}

        await q.edit_message_text(
            "⚙️ اختر:",
            reply_markup=user_menu(target)
        )

    # POINTS
    elif data.startswith("p:"):
        target = data.split(":")[1]
        p = get_user(target)[0]
        update(target, "points", p + 10)
        refresh_title(target)
        await q.answer("✔️ +10 نقاط", show_alert=True)

    elif data.startswith("m:"):
        target = data.split(":")[1]
        m = get_user(target)[1]
        update(target, "messages", m + 1)
        await q.answer("✔️ +1 رسالة", show_alert=True)

    # TITLE (كتابة فقط)
    elif data.startswith("t:"):
        target = data.split(":")[1]
        context_state[uid] = {"target": target, "mode": "title"}
        await q.edit_message_text("🏷️ اكتب اللقب الجديد (نص فقط)")

    # TOP
    elif data == "top":
        cursor.execute("SELECT name,points FROM users ORDER BY points DESC LIMIT 10")
        rows = cursor.fetchall()

        text = "🏆 TOP 10\n\n"
        for i, r in enumerate(rows, 1):
            text += f"{i}) {r[0]} ⭐ {r[1]}\n"

        await q.edit_message_text(text)

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("BOT RUNNING 3.0")
    app.run_polling()

if __name__ == "__main__":
    main()
