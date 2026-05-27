import os
import random
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    points INTEGER,
    messages INTEGER,
    title TEXT
)
""")
conn.commit()

state = {}
active_q = {}

# ================= USERS =================
def create_user(uid, name):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (str(uid),))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES (?,?,?,?,?)",
                       (str(uid), name, 0, 0, "مبتدئ"))
        conn.commit()


def get_user(uid):
    cursor.execute("SELECT points,messages,title,name FROM users WHERE user_id=?", (str(uid),))
    return cursor.fetchone()


def update(uid, field, value):
    cursor.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, str(uid)))
    conn.commit()

# ================= TITLES =================
def calc_title(points):
    if points >= 5000:
        return "أسطورة"
    elif points >= 2000:
        return "خبير"
    elif points >= 1000:
        return "محترف"
    elif points >= 500:
        return "نشط"
    return "مبتدئ"


def update_title(uid):
    cursor.execute("SELECT points FROM users WHERE user_id=?", (str(uid),))
    row = cursor.fetchone()
    if row:
        update(uid, "title", calc_title(row[0]))

# ================= QUESTIONS =================
QUESTIONS = [(f"كم {i}+{i+2}؟", str(i+i+2)) for i in range(1, 120)]
QUESTIONS += [("ما عاصمة العراق؟", "بغداد"), ("ما عاصمة فرنسا؟", "باريس")]

# ================= UI =================
def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("المستخدمين", callback_data="users")],
        [InlineKeyboardButton("ID", callback_data="ids")]
    ])


def user_menu(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("نقاط", callback_data=f"p:{uid}")],
        [InlineKeyboardButton("رسائل", callback_data=f"m:{uid}")],
        [InlineKeyboardButton("لقب", callback_data=f"t:{uid}")],
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    create_user(uid, update.effective_user.first_name)

    if uid == ADMIN_ID:
        await update.message.reply_text("لوحة الأدمن", reply_markup=admin_menu())
    else:
        await update.message.reply_text("اكتب: سوال / معلوماتي / top")

# ================= SINGLE HANDLER (FIXED CORE) =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    create_user(uid, update.effective_user.first_name)

    # ===== ADMIN STATE FIRST =====
    if uid in state:
        s = state[uid]
        target = s["target"]

        if s["mode"] == "points":
            update(target, "points", int(text))
            update_title(target)

        elif s["mode"] == "messages":
            update(target, "messages", int(text))

        elif s["mode"] == "title":
            update(target, "title", text)

        del state[uid]
        await update.message.reply_text("تم التعديل ✔️")
        return

    # ===== USER COMMANDS =====
    if text in ["سوال", "سؤال"]:
        q, a = random.choice(QUESTIONS)
        active_q[uid] = a
        await update.message.reply_text(q)
        return

    if text == "معلوماتي":
        p, m, t, n = get_user(uid)
        await update.message.reply_text(f"{n}\n{p}\n{m}\n{t}")
        return

    if uid in active_q and text.lower() == active_q[uid].lower():
        p, m, t, n = get_user(uid)
        update(uid, "points", p + 1)
        update_title(uid)
        del active_q[uid]
        await update.message.reply_text("+1 صحيح")

# ================= CALLBACK =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    if uid != ADMIN_ID:
        return

    if data == "users":
        cursor.execute("SELECT user_id,name,points FROM users")
        rows = cursor.fetchall()

        keyboard = [[InlineKeyboardButton(f"{r[1]} ({r[2]})", callback_data=f"user:{r[0]}")] for r in rows]

        await q.edit_message_text("المستخدمين", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("user:"):
        target = data.split(":")[1]
        state[uid] = {"target": target}
        await q.edit_message_text("اختر:", reply_markup=user_menu(target))

    elif data.startswith("p:"):
        state[uid] = {"target": data.split(":")[1], "mode": "points"}
        await q.edit_message_text("ارسل النقاط")

    elif data.startswith("m:"):
        state[uid] = {"target": data.split(":")[1], "mode": "messages"}
        await q.edit_message_text("ارسل الرسائل")

    elif data.startswith("t:"):
        state[uid] = {"target": data.split(":")[1], "mode": "title"}
        await q.edit_message_text("ارسل اللقب")

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("BOT RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()
