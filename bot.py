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

cursor.execute("""
CREATE TABLE IF NOT EXISTS titles (
    min_points INTEGER PRIMARY KEY,
    title TEXT
)
""")

conn.commit()

# ================= JSON BACKUP =================
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

# ================= INIT TITLES =================
def init_titles():
    if cursor.execute("SELECT COUNT(*) FROM titles").fetchone()[0] == 0:

        base_titles = [
            (0, "👶 مبتدئ جداً"),
            (25, "🌱 مبتدئ"),
            (50, "🥉 متعلم"),
            (100, "🥈 نشط"),
            (150, "🥈 نشط جداً"),
            (200, "🥇 جيد"),
            (300, "🥇 جيد جداً"),
            (400, "💎 محترف"),
            (500, "🔥 خبير"),
            (750, "⚡ متقدم"),
            (1000, "🚀 قوي"),
            (1500, "🏆 أسطورة"),
            (2000, "👑 ملك"),
            (3000, "💀 خارق"),
            (5000, "🌌 أسطوري"),
        ]

        cursor.executemany("INSERT INTO titles VALUES (?,?)", base_titles)
        conn.commit()

init_titles()

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

    cursor.execute("""
        SELECT title FROM titles
        WHERE min_points <= ?
        ORDER BY min_points DESC
        LIMIT 1
    """, (points,))

    title = cursor.fetchone()[0]

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

# ================= ADMIN MENU =================
def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ تعديل النقاط", callback_data="edit_points")],
        [InlineKeyboardButton("📨 تعديل الرسائل", callback_data="edit_messages")],
        [InlineKeyboardButton("🏷️ الألقاب", callback_data="titles")],
        [InlineKeyboardButton("👤 المستخدمين", callback_data="users")],
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    name = update.message.from_user.first_name

    get_user(uid, name)

    if is_admin(uid):
        await update.message.reply_text("👑 لوحة الأدمن", reply_markup=admin_menu())
    else:
        await update.message.reply_text("👋 أهلاً بك في البوت")

# ================= MAIN TRACK =================
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.message.from_user.id
    name = update.message.from_user.first_name
    text = update.message.text.strip()

    get_user(uid, name)
    add_message(uid)

    # ================= سوال =================
    if text == "سوال" or text == "سوال":
        qst, ans = random.choice(QUESTIONS)
        active_q[uid] = ans
        await update.message.reply_text(f"❓ {qst}")
        return

    # ================= معلوماتي =================
    if text == "معلوماتي":
        p, m = get_user(uid)

        cursor.execute("SELECT title FROM users WHERE user_id=?", (str(uid),))
        row = cursor.fetchone()
        title = row[0] if row else "غير معروف"

        await update.message.reply_text(
            f"👤 الاسم: {name}\n"
            f"⭐ النقاط: {p}\n"
            f"📨 الرسائل: {m}\n"
            f"🏷️ اللقب: {title}"
        )
        return

    # ================= إجابة =================
    if uid in active_q:
        if text.lower() == active_q[uid].lower():
            add_points(uid, 1)
            del active_q[uid]
            await update.message.reply_text("🎉 إجابة صحيحة +1 ⭐")

# ================= ADMIN BUTTONS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    if not is_admin(uid):
        return await q.answer("❌ غير مصرح", show_alert=True)

    if data == "users":
        cursor.execute("SELECT user_id, name, points, messages FROM users ORDER BY points DESC")
        rows = cursor.fetchall()

        msg = "👤 المستخدمين:\n\n"
        for i, r in enumerate(rows, 1):
            msg += f"{i}) {r[1]} | {r[0]}\n⭐ {r[2]} | 📨 {r[3]}\n\n"

        await q.edit_message_text(msg, reply_markup=admin_menu())

    elif data == "titles":
        cursor.execute("SELECT * FROM titles ORDER BY min_points ASC")
        rows = cursor.fetchall()

        msg = "🏷️ الألقاب:\n\n"
        for r in rows:
            msg += f"{r[0]} ⭐ → {r[1]}\n"

        await q.edit_message_text(msg, reply_markup=admin_menu())

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track))
    app.add_handler(MessageHandler(filters.COMMAND, start))

    print("BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
