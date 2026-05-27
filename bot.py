import os
import random
import sqlite3
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ================= DATABASE =================
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    title TEXT DEFAULT '👶 مبتدئ جداً'
)
""")
conn.commit()

# ================= BACKUP JSON =================
JSON_FILE = "backup.json"

def save_json():
    data = {}

    cursor.execute("SELECT * FROM users")
    for r in cursor.fetchall():
        data[r[0]] = {
            "name": r[1],
            "points": r[2],
            "messages": r[3],
            "title": r[4]
        }

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= TITLES (25) =================
titles = [
    (0, "👶 مبتدئ جداً"),
    (25, "🌱 مبتدئ"),
    (50, "🥉 متعلم"),
    (100, "🥈 نشط"),
    (150, "🥈 نشط جداً"),
    (200, "🥇 جيد"),
    (300, "🥇 جيد جداً"),
    (400, "💎 محترف"),
    (500, "💎 محترف 2"),
    (600, "🔥 خبير"),
    (750, "🔥 خبير 2"),
    (900, "⚡ متقدم"),
    (1100, "⚡ متقدم جداً"),
    (1300, "🚀 قوي"),
    (1500, "🚀 قوي جداً"),
    (1800, "🏆 أسطورة"),
    (2100, "🏆 أسطورة 2"),
    (2500, "👑 ملك"),
    (3000, "👑 ملك قوي"),
    (3500, "👑 ملك الأساطير"),
    (4000, "💀 خارق"),
    (5000, "💀 خارق جداً"),
    (6500, "🌌 أسطوري"),
    (8000, "🌌 أسطوري جداً"),
    (10000, "🔱 إله النقاط")
]

# ================= QUESTIONS =================
QUESTIONS = [("ما عاصمة العراق؟", "بغداد")]

for i in range(1, 140):
    a = random.randint(1, 30)
    b = random.randint(1, 30)
    QUESTIONS.append((f"كم {a} + {b}؟", str(a + b)))

# ================= ACTIVE =================
active_q = {}
state = {}

# ================= HELPERS =================
def is_admin(uid):
    return int(uid) == ADMIN_ID


def get_user(uid, name=""):
    cursor.execute("SELECT points, messages FROM users WHERE user_id=?", (str(uid),))
    row = cursor.fetchone()

    if not row:
        cursor.execute(
            "INSERT INTO users (user_id, name) VALUES (?,?)",
            (str(uid), name)
        )
        conn.commit()
        save_json()
        return (0, 0)

    return row


def update_title(uid):
    cursor.execute("SELECT points FROM users WHERE user_id=?", (str(uid),))
    row = cursor.fetchone()
    if not row:
        return

    points = row[0]
    title = titles[0][1]

    for p, t in titles:
        if points >= p:
            title = t

    cursor.execute("UPDATE users SET title=? WHERE user_id=?", (title, str(uid)))
    conn.commit()
    save_json()


def add_points(uid, v):
    p, m = get_user(uid)
    cursor.execute("UPDATE users SET points=? WHERE user_id=?", (p + v, str(uid)))
    conn.commit()
    update_title(uid)
    save_json()


def add_message(uid):
    p, m = get_user(uid)
    cursor.execute("UPDATE users SET messages=? WHERE user_id=?", (m + 1, str(uid)))
    conn.commit()
    save_json()

# ================= USER MENU =================
def menu(uid):
    buttons = [
        [InlineKeyboardButton("⭐ نقاطي", callback_data="points")],
        [InlineKeyboardButton("📨 رسائلي", callback_data="messages")],
        [InlineKeyboardButton("❓ سؤال", callback_data="question")]
    ]

    if is_admin(uid):
        buttons.append([InlineKeyboardButton("⚙️ لوحة الأدمن", callback_data="admin")])

    return InlineKeyboardMarkup(buttons)

# ================= ADMIN MENU =================
def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ تعديل النقاط", callback_data="edit_points")],
        [InlineKeyboardButton("📨 تعديل الرسائل", callback_data="edit_messages")],
        [InlineKeyboardButton("👤 المستخدمين", callback_data="users")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    name = update.message.from_user.first_name

    get_user(uid, name)

    await update.message.reply_text(
        "👋 أهلاً بك",
        reply_markup=menu(uid)
    )

# ================= TRACK =================
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.message.from_user.id
    name = update.message.from_user.first_name

    get_user(uid, name)
    add_message(uid)

    text = update.message.text.strip()

    if uid in active_q:
        if text.lower() == active_q[uid].lower():
            add_points(uid, 1)
            del active_q[uid]
            await update.message.reply_text("🎉 إجابة صحيحة +1 ⭐")

# ================= BUTTONS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    # ===== USER =====
    if data == "points":
        p, m = get_user(uid)
        await q.edit_message_text(f"⭐ نقاطك: {p}", reply_markup=menu(uid))

    elif data == "messages":
        p, m = get_user(uid)
        await q.edit_message_text(f"📨 رسائلك: {m}", reply_markup=menu(uid))

    elif data == "question":
        qst, ans = random.choice(QUESTIONS)
        active_q[uid] = ans
        await q.edit_message_text(f"❓ {qst}", reply_markup=menu(uid))

    # ===== ADMIN =====
    elif data == "admin":
        if not is_admin(uid):
            return await q.answer("❌ غير مصرح", show_alert=True)

        await q.edit_message_text("⚙️ لوحة الأدمن", reply_markup=admin_menu())

    elif data == "back":
        await q.edit_message_text("👋 القائمة", reply_markup=menu(uid))

    elif data == "users":
        if not is_admin(uid):
            return

        cursor.execute("SELECT user_id, name, points, messages FROM users ORDER BY points DESC")
        rows = cursor.fetchall()

        msg = "👤 المستخدمين:\n\n"
        for i, r in enumerate(rows, 1):
            msg += f"{i}) {r[1]} | {r[0]}\n⭐ {r[2]} | 📨 {r[3]}\n\n"

        await q.edit_message_text(msg, reply_markup=admin_menu())

    elif data == "edit_points":
        if not is_admin(uid):
            return

        state[uid] = {"step": "pid"}
        await q.edit_message_text("🆔 ارسل ID المستخدم")

    elif data == "edit_messages":
        if not is_admin(uid):
            return

        state[uid] = {"step": "mid"}
        await q.edit_message_text("🆔 ارسل ID المستخدم")

# ================= TEXT STEPS =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text

    if uid not in state:
        return

    step = state[uid]["step"]

    # ===== POINTS =====
    if step == "pid":
        state[uid]["target"] = text
        state[uid]["step"] = "pval"
        await update.message.reply_text("⭐ ارسل النقاط الجديدة")

    elif step == "pval":
        target = state[uid]["target"]

        cursor.execute("UPDATE users SET points=? WHERE user_id=?", (int(text), target))
        conn.commit()
        update_title(target)
        save_json()

        del state[uid]
        await update.message.reply_text("✅ تم تعديل النقاط")

    # ===== MESSAGES =====
    elif step == "mid":
        state[uid]["target"] = text
        state[uid]["step"] = "mval"
        await update.message.reply_text("📨 ارسل الرسائل الجديدة")

    elif step == "mval":
        target = state[uid]["target"]

        cursor.execute("UPDATE users SET messages=? WHERE user_id=?", (int(text), target))
        conn.commit()
        save_json()

        del state[uid]
        await update.message.reply_text("✅ تم تعديل الرسائل")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.COMMAND, start))

    print("BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
