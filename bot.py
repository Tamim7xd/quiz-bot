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
    title TEXT DEFAULT '👶 مبتدئ'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS titles (
    min_points INTEGER PRIMARY KEY,
    title TEXT
)
""")

conn.commit()

# ================= BACKUP JSON =================
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

    with open("backup.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= TITLES =================
def init_titles():
    if cursor.execute("SELECT COUNT(*) FROM titles").fetchone()[0] == 0:
        base = [
            (0, "👶 مبتدئ"),
            (50, "🌱 مبتدئ متطور"),
            (100, "🥉 نشط"),
            (200, "🥈 جيد"),
            (300, "🥇 محترف"),
            (500, "🔥 خبير"),
            (800, "⚡ متقدم"),
            (1200, "🚀 قوي"),
            (2000, "🏆 أسطورة"),
            (3000, "👑 ملك"),
        ]
        cursor.executemany("INSERT INTO titles VALUES (?,?)", base)
        conn.commit()

init_titles()

# ================= QUESTIONS =================
QUESTIONS = [("ما عاصمة العراق؟", "بغداد")]

for i in range(1, 120):
    a = random.randint(1, 25)
    b = random.randint(1, 25)
    QUESTIONS.append((f"كم {a} + {b}؟", str(a + b)))

# ================= MEMORY =================
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
        [InlineKeyboardButton("👤 المستخدمين", callback_data="users")],
        [InlineKeyboardButton("💰 نقاط جماعية", callback_data="global_points")],
        [InlineKeyboardButton("🏷️ الألقاب", callback_data="titles")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    name = update.message.from_user.first_name

    get_user(uid, name)

    if is_admin(uid):
        await update.message.reply_text("👑 لوحة الأدمن", reply_markup=admin_menu())
    else:
        await update.message.reply_text("👋 اكتب: سوال أو معلوماتي")

# ================= TRACK =================
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.message.from_user.id
    name = update.message.from_user.first_name
    text = update.message.text.strip()

    get_user(uid, name)
    add_message(uid)

    # ===== سؤال =====
    if text in ["سوال", "سؤال"]:
        qst, ans = random.choice(QUESTIONS)
        active_q[uid] = ans
        await update.message.reply_text(f"❓ {qst}")
        return

    # ===== معلوماتي =====
    if text == "معلوماتي":
        p, m = get_user(uid)

        cursor.execute("SELECT title FROM users WHERE user_id=?", (str(uid),))
        title = cursor.fetchone()[0]

        await update.message.reply_text(
            f"👤 الاسم: {name}\n"
            f"⭐ النقاط: {p}\n"
            f"📨 الرسائل: {m}\n"
            f"🏷️ اللقب: {title}"
        )
        return

    # ===== إجابة =====
    if uid in active_q:
        if text.lower() == active_q[uid].lower():
            add_points(uid, 1)
            del active_q[uid]
            await update.message.reply_text("🎉 صحيح +1 ⭐")

    # ===== admin state =====
    if uid in state:
        mode = state[uid]["mode"]

        # اختيار مستخدم
        if mode == "select_user":
            state[uid]["target"] = text
            state[uid]["mode"] = "menu"

            await update.message.reply_text(
                "⚙️ اختر العملية:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⭐ تعديل نقاط", callback_data="edit_points")],
                    [InlineKeyboardButton("📨 تعديل رسائل", callback_data="edit_messages")],
                    [InlineKeyboardButton("❌ حذف مستخدم", callback_data="delete_user")],
                    [InlineKeyboardButton("⬅️ رجوع", callback_data="users")]
                ])
            )
            return

        target = state[uid].get("target")

        # تعديل نقاط
        if mode == "set_points":
            cursor.execute("UPDATE users SET points=? WHERE user_id=?", (int(text), target))
            conn.commit()
            update_title(target)
            save_json()
            del state[uid]
            await update.message.reply_text("✅ تم تعديل النقاط")
            return

        # تعديل رسائل
        if mode == "set_messages":
            cursor.execute("UPDATE users SET messages=? WHERE user_id=?", (int(text), target))
            conn.commit()
            save_json()
            del state[uid]
            await update.message.reply_text("✅ تم تعديل الرسائل")
            return

        # نقاط جماعية
        if mode == "global_points":
            cursor.execute("UPDATE users SET points = points + ?", (int(text),))
            conn.commit()

            cursor.execute("SELECT user_id FROM users")
            for u in cursor.fetchall():
                update_title(u[0])

            save_json()
            del state[uid]
            await update.message.reply_text("💰 تم إضافة نقاط جماعية")
            return

# ================= CALLBACKS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    if not is_admin(uid):
        return await q.answer("❌ غير مصرح", show_alert=True)

    # ===== USERS =====
    if data == "users":
        cursor.execute("SELECT user_id,name FROM users")
        rows = cursor.fetchall()

        keyboard = []
        for r in rows:
            keyboard.append([
                InlineKeyboardButton(r[1], callback_data=f"u_{r[0]}")
            ])

        await q.edit_message_text(
            "👤 اختر مستخدم:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ===== SELECT USER =====
    elif data.startswith("u_"):
        target = data.split("_")[1]
        state[uid] = {"mode": "select_user", "target": target}

        await q.edit_message_text("✍️ ارسل ID أو اسم (تأكيد)")

    # ===== EDIT POINTS =====
    elif data == "edit_points":
        state[uid]["mode"] = "set_points"
        await q.edit_message_text("⭐ ارسل النقاط الجديدة")

    # ===== EDIT MESSAGES =====
    elif data == "edit_messages":
        state[uid]["mode"] = "set_messages"
        await q.edit_message_text("📨 ارسل الرسائل الجديدة")

    # ===== DELETE USER =====
    elif data == "delete_user":
        target = state[uid]["target"]

        cursor.execute("DELETE FROM users WHERE user_id=?", (target,))
        conn.commit()
        save_json()

        await q.edit_message_text("❌ تم حذف المستخدم")

    # ===== GLOBAL POINTS =====
    elif data == "global_points":
        state[uid] = {"mode": "global_points"}
        await q.edit_message_text("💰 ارسل عدد النقاط الجماعية")

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
