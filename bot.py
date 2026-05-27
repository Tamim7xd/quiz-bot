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
QUESTIONS = [(f"كم {i}+{i+1}؟", str(i + i + 1)) for i in range(1, 100)]

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


def update_user(uid, **kwargs):
    for k, v in kwargs.items():
        cursor.execute(f"UPDATE users SET {k}=? WHERE user_id=?", (v, str(uid)))
    conn.commit()

# ================= ADMIN MENU =================
def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 المستخدمين", callback_data="users")],
        [InlineKeyboardButton("👤 العضو + ID", callback_data="show_ids")],
        [InlineKeyboardButton("💰 نقاط جماعية", callback_data="global")],
    ])


def user_panel(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ تعديل نقاط", callback_data=f"p_{uid}")],
        [InlineKeyboardButton("📨 تعديل رسائل", callback_data=f"m_{uid}")],
        [InlineKeyboardButton("🏷️ تعديل لقب", callback_data=f"t_{uid}")],
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

# ================= TRACK =================
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
        await update.message.reply_text(
            f"👤 {n}\n⭐ {p}\n📨 {m}\n🏷️ {t}"
        )
        return

    # إجابة
    if uid in active_q:
        if text.lower() == active_q[uid].lower():
            p, m, t, n = get_user(uid)
            update_user(uid, points=p+1)
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
            [InlineKeyboardButton(f"{r[1]} ⭐{r[2]}", callback_data=f"user_{r[0]}")]
            for r in rows
        ]

        await q.edit_message_text("👤 المستخدمين:", reply_markup=InlineKeyboardMarkup(keyboard))

    # ===== SHOW USER + ID (طلبك الجديد) =====
    elif data == "show_ids":
        cursor.execute("SELECT user_id,name FROM users")
        rows = cursor.fetchall()

        text = "👤 الأعضاء:\n\n"
        for r in rows:
            text += f"• {r[1]}\n🆔 {r[0]}\n\n"

        await q.edit_message_text(text)

    # ===== OPEN USER =====
    elif data.startswith("user_"):
        target = data.split("_")[1]
        state[uid] = {"target": target}
        await q.edit_message_text("⚙️ إدارة المستخدم", reply_markup=user_panel(target))

    # ===== EDIT POINTS =====
    elif data.startswith("p_"):
        state[uid] = {"target": data.split("_")[1], "mode": "points"}
        await q.edit_message_text("⭐ ارسل النقاط")

    # ===== EDIT MESSAGES =====
    elif data.startswith("m_"):
        state[uid] = {"target": data.split("_")[1], "mode": "messages"}
        await q.edit_message_text("📨 ارسل الرسائل")

    # ===== EDIT TITLE =====
    elif data.startswith("t_"):
        state[uid] = {"target": data.split("_")[1], "mode": "title"}
        await q.edit_message_text("🏷️ ارسل اللقب")

    # ===== GLOBAL =====
    elif data == "global":
        state[uid] = {"mode": "global"}
        await q.edit_message_text("💰 ارسل النقاط الجماعية")

# ================= TEXT HANDLER (FIXED) =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    if uid not in state:
        return

    s = state[uid]
    target = s.get("target")

    # ⭐ نقاط
    if s["mode"] == "points":
        update_user(target, points=int(text))
        del state[uid]
        await update.message.reply_text("✔️ تم تعديل النقاط")

    # 📨 رسائل
    elif s["mode"] == "messages":
        update_user(target, messages=int(text))
        del state[uid]
        await update.message.reply_text("✔️ تم تعديل الرسائل")

    # 🏷️ لقب
    elif s["mode"] == "title":
        update_user(target, title=text)
        del state[uid]
        await update.message.reply_text("✔️ تم تعديل اللقب")

    # 💰 جماعي
    elif s["mode"] == "global":
        cursor.execute("UPDATE users SET points = points + ?", (int(text),))
        conn.commit()
        del state[uid]
        await update.message.reply_text("✔️ تم إضافة نقاط جماعية")

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
