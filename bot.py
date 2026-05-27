import os
import random
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ================= DB =================
conn = sqlite3.connect("data.db", check_same_thread=False)
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

state = {}
active_q = {}

# ================= TITLES =================
def update_title(uid):
    cursor.execute("SELECT points FROM users WHERE user_id=?", (str(uid),))
    row = cursor.fetchone()
    if not row:
        return

    points = row[0]

    cursor.execute("""
        SELECT title FROM users
        WHERE user_id=?
    """, (str(uid),))
    old = cursor.fetchone()

    # توليد لقب تلقائي بسيط حسب النقاط
    if points >= 5000:
        title = "👑 أسطورة"
    elif points >= 2000:
        title = "🔥 خبير"
    elif points >= 1000:
        title = "🥇 محترف"
    elif points >= 500:
        title = "🥈 نشط"
    else:
        title = "👶 مبتدئ"

    cursor.execute("UPDATE users SET title=? WHERE user_id=?", (title, str(uid)))
    conn.commit()

# ================= QUESTIONS =================
QUESTIONS = []
for i in range(80):
    a = random.randint(1, 50)
    b = random.randint(1, 50)
    QUESTIONS.append((f"كم {a}+{b}؟", str(a+b)))

QUESTIONS += [
    ("ما عاصمة العراق؟", "بغداد"),
    ("ما عاصمة فرنسا؟", "باريس"),
    ("ما عدد الكواكب؟", "8"),
    ("ما أكبر كوكب؟", "المشتري"),
    ("ما أعلى جبل؟", "إيفرست"),
]

# ================= HELPERS =================
def is_admin(uid):
    return int(uid) == ADMIN_ID


def get_user(uid, name=""):
    cursor.execute("SELECT points,messages,title FROM users WHERE user_id=?", (str(uid),))
    row = cursor.fetchone()

    if not row:
        cursor.execute(
            "INSERT INTO users VALUES (?,?,?,?,?)",
            (str(uid), name, 0, 0, "👶 مبتدئ")
        )
        conn.commit()
        return (0, 0, "👶 مبتدئ")

    return row


def set_user(uid, field, value):
    cursor.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, str(uid)))
    conn.commit()

# ================= MENU =================
def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 المستخدمين", callback_data="users")],
        [InlineKeyboardButton("👤 العضو + ID", callback_data="ids")]
    ])


def user_panel(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ نقاط", callback_data=f"p:{uid}")],
        [InlineKeyboardButton("📨 رسائل", callback_data=f"m:{uid}")],
        [InlineKeyboardButton("🏷️ لقب", callback_data=f"t:{uid}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="users")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    get_user(uid, update.effective_user.first_name)

    if is_admin(uid):
        await update.message.reply_text("👑 لوحة التحكم", reply_markup=admin_menu())
    else:
        await update.message.reply_text("👋 اكتب: سوال / معلوماتي / top")

# ================= MAIN =================
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    get_user(uid, update.effective_user.first_name)

    # سوال
    if text in ["سوال", "سؤال"]:
        q, a = random.choice(QUESTIONS)
        active_q[uid] = a
        await update.message.reply_text(q)
        return

    # معلوماتي
    if text == "معلوماتي":
        p, m, t = get_user(uid)
        await update.message.reply_text(f"⭐ {p}\n📨 {m}\n🏷️ {t}")
        return

    # top
    if text == "top":
        cursor.execute("SELECT name,points FROM users ORDER BY points DESC LIMIT 10")
        rows = cursor.fetchall()

        msg = "🏆 TOP 10\n\n"
        for i, r in enumerate(rows, 1):
            msg += f"{i}) {r[0]} ⭐ {r[1]}\n"

        await update.message.reply_text(msg)
        return

    # إجابة
    if uid in active_q:
        if text.lower() == active_q[uid].lower():
            p, m, t = get_user(uid)
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

    if not is_admin(uid):
        return

    # ===== USERS =====
    if data == "users":
        cursor.execute("SELECT user_id,name,points FROM users")
        rows = cursor.fetchall()

        keyboard = [
            [InlineKeyboardButton(f"{r[1]} ⭐{r[2]}", callback_data=f"user:{r[0]}")]
            for r in rows
        ]

        await q.edit_message_text("👤 المستخدمين:", reply_markup=InlineKeyboardMarkup(keyboard))

    # ===== IDS =====
    elif data == "ids":
        cursor.execute("SELECT user_id,name FROM users")
        rows = cursor.fetchall()

        text = "👤 الأعضاء + ID:\n\n"
        for r in rows:
            text += f"{r[1]}\n🆔 {r[0]}\n\n"

        await q.edit_message_text(text)

    # ===== OPEN USER =====
    elif data.startswith("user:"):
        target = data.split(":")[1]
        state[uid] = {"target": target}
        await q.edit_message_text("⚙️ إدارة المستخدم", reply_markup=user_panel(target))

    # ===== POINTS =====
    elif data.startswith("p:"):
        target = data.split(":")[1]
        state[uid] = {"target": target, "mode": "points"}
        await q.edit_message_text("⭐ ارسل النقاط")

    # ===== MESSAGES =====
    elif data.startswith("m:"):
        target = data.split(":")[1]
        state[uid] = {"target": target, "mode": "messages"}
        await q.edit_message_text("📨 ارسل الرسائل")

    # ===== TITLE =====
    elif data.startswith("t:"):
        target = data.split(":")[1]
        state[uid] = {"target": target, "mode": "title"}
        await q.edit_message_text("🏷️ ارسل اللقب")

# ================= TEXT FIXED =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    if uid not in state:
        return

    s = state[uid]
    target = s["target"]

    try:
        if s["mode"] == "points":
            set_user(target, "points", int(text))
            update_title(target)
            await update.message.reply_text("✔️ تم تعديل النقاط")

        elif s["mode"] == "messages":
            set_user(target, "messages", int(text))
            await update.message.reply_text("✔️ تم تعديل الرسائل")

        elif s["mode"] == "title":
            set_user(target, "title", text)
            await update.message.reply_text("✔️ تم تعديل اللقب")

    except:
        await update.message.reply_text("❌ خطأ في الإدخال")

    del state[uid]

# ================= MAIN RUN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("BOT RUNNING")
    app.run_polling()


if __name__ == "__main__":
    main()
