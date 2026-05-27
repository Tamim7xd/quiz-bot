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

# ================= QUESTIONS =================
QUESTIONS = [(f"كم {i}+{i+2}؟", str(i + i + 2)) for i in range(1, 120)]

# ================= HELPERS =================
def is_admin(uid):
    return int(uid) == ADMIN_ID


def get_user(uid, name=""):
    cursor.execute("SELECT points,messages,title,name FROM users WHERE user_id=?", (str(uid),))
    row = cursor.fetchone()

    if not row:
        cursor.execute(
            "INSERT INTO users VALUES (?,?,?,?,?)",
            (str(uid), name, 0, 0, "👶 مبتدئ")
        )
        conn.commit()
        return (0, 0, "👶 مبتدئ", name)

    return row


def set_user(uid, field, value):
    cursor.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, str(uid)))
    conn.commit()

# ================= UI =================
def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 المستخدمين", callback_data="users")],
        [InlineKeyboardButton("👤 العضو + ID", callback_data="ids")],
    ])


def user_panel(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ النقاط", callback_data=f"set_points:{uid}")],
        [InlineKeyboardButton("📨 الرسائل", callback_data=f"set_msgs:{uid}")],
        [InlineKeyboardButton("🏷️ اللقب", callback_data=f"set_title:{uid}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="users")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    get_user(uid, update.effective_user.first_name)

    if is_admin(uid):
        await update.message.reply_text("👑 لوحة التحكم", reply_markup=admin_menu())
    else:
        await update.message.reply_text("👋 اكتب: سوال / معلوماتي")

# ================= NORMAL =================
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
        p, m, t, n = get_user(uid)
        await update.message.reply_text(f"👤 {n}\n⭐ {p}\n📨 {m}\n🏷️ {t}")
        return

    # إجابة
    if uid in active_q:
        if text.lower() == active_q[uid].lower():
            p, m, t, n = get_user(uid)
            set_user(uid, "points", p + 1)
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

    # ===== IDS LIST =====
    elif data == "ids":
        cursor.execute("SELECT user_id,name FROM users")
        rows = cursor.fetchall()

        text = "👤 الأعضاء:\n\n"
        for r in rows:
            text += f"{r[1]}\n🆔 {r[0]}\n\n"

        await q.edit_message_text(text)

    # ===== OPEN USER =====
    elif data.startswith("user:"):
        target = data.split(":")[1]
        state[uid] = {"target": target}
        await q.edit_message_text("⚙️ اختر:", reply_markup=user_panel(target))

    # ===== SET POINTS =====
    elif data.startswith("set_points:"):
        target = data.split(":")[1]
        state[uid] = {"target": target, "mode": "points"}
        await q.edit_message_text("⭐ ارسل النقاط الجديدة")

    # ===== SET MESSAGES =====
    elif data.startswith("set_msgs:"):
        target = data.split(":")[1]
        state[uid] = {"target": target, "mode": "msgs"}
        await q.edit_message_text("📨 ارسل الرسائل الجديدة")

    # ===== SET TITLE =====
    elif data.startswith("set_title:"):
        target = data.split(":")[1]
        state[uid] = {"target": target, "mode": "title"}
        await q.edit_message_text("🏷️ ارسل اللقب الجديد")

# ================= TEXT HANDLER (FIXED 100%) =================
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
            await update.message.reply_text("✔️ تم تعديل النقاط")

        elif s["mode"] == "msgs":
            set_user(target, "messages", int(text))
            await update.message.reply_text("✔️ تم تعديل الرسائل")

        elif s["mode"] == "title":
            set_user(target, "title", text)
            await update.message.reply_text("✔️ تم تعديل اللقب")

    except Exception as e:
        await update.message.reply_text("❌ خطأ في الإدخال")

    del state[uid]

# ================= MAIN =================
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
