import os
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================= ENV =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN:
    raise Exception("BOT_TOKEN is missing")

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 0,
    title TEXT DEFAULT '🌱 جديد'
)
""")
conn.commit()

# ================= MEMORY =================
admin_state = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("👋 أهلاً بك")
        return

    keyboard = [
        [InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="admin_panel")]
    ]

    await update.message.reply_text(
        "🔥 لوحة التحكم",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= PANEL =================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("➕ إرسال نقاط للجميع", callback_data="all_points")]
    ]

    await q.message.reply_text(
        "🛠 لوحة الأدمن",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= SHOW USERS =================
def get_users():
    c.execute("SELECT user_id,name,points FROM users LIMIT 20")
    return c.fetchall()

async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    users = get_users()

    keyboard = []

    for u in users:
        keyboard.append([
            InlineKeyboardButton(
                f"{u[1]} | {u[2]} نقطة",
                callback_data=f"user_{u[0]}"
            )
        ])

    await q.message.reply_text(
        "👥 اختر عضو:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= USER CONTROL =================
async def user_control(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    keyboard = [
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data=f"addp_{uid}")],
        [InlineKeyboardButton("✏️ تعديل لقب", callback_data=f"title_{uid}")]
    ]

    await q.message.reply_text(
        "⚙️ إدارة العضو",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= ADD POINTS =================
async def add_points(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    admin_state[ADMIN_ID] = ("add_points", uid)

    await q.message.reply_text("💰 أرسل عدد النقاط")

# ================= TITLE =================
async def set_title(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    admin_state[ADMIN_ID] = ("set_title", uid)

    await q.message.reply_text("🏅 أرسل اللقب الجديد")

# ================= MESSAGE HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text

    # ================= ADMIN ACTION =================
    if uid == ADMIN_ID and ADMIN_ID in admin_state:

        state, target = admin_state[ADMIN_ID]

        # -------- ADD POINTS --------
        if state == "add_points":

            try:
                amount = int(text)

                c.execute("SELECT points FROM users WHERE user_id=?", (target,))
                row = c.fetchone()

                if row:
                    new_points = row[0] + amount

                    c.execute(
                        "UPDATE users SET points=? WHERE user_id=?",
                        (new_points, target)
                    )

                    conn.commit()

                await update.message.reply_text("✅ تم إضافة النقاط")

            except:
                await update.message.reply_text("❌ خطأ في الرقم")

            admin_state.pop(ADMIN_ID)
            return

        # -------- SET TITLE --------
        if state == "set_title":

            c.execute(
                "UPDATE users SET title=? WHERE user_id=?",
                (text, target)
            )

            conn.commit()

            await update.message.reply_text("🏅 تم تعديل اللقب")

            admin_state.pop(ADMIN_ID)
            return

    # ================= AUTO REGISTER USER =================
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():

        c.execute(
            "INSERT INTO users VALUES (?,?,0,'🌱 جديد')",
            (uid, update.effective_user.first_name)
        )

        conn.commit()

# ================= CALLBACK ROUTER =================
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    data = q.data

    if data == "admin_panel":
        await panel(update, context)

    elif data == "users":
        await show_users(update, context)

    elif data.startswith("user_"):
        await user_control(update, context)

    elif data.startswith("addp_"):
        await add_points(update, context)

    elif data.startswith("title_"):
        await set_title(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🚀 ADMIN PANEL BOT RUNNING")
app.run_polling()
