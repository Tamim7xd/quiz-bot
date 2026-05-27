import os
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    title TEXT DEFAULT 'مبتدئ'
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    q TEXT,
    a TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS active_q (
    user_id INTEGER PRIMARY KEY,
    q TEXT,
    a TEXT
)
""")

conn.commit()

# ================= STATE =================
admin_state = {}

# ================= TITLES =================
TITLES = [
    "مبتدئ","نشيط","متفاعل","محترف","نجم",
    "أسطورة","قائد","ملك","بطل","Legend",
    "Elite","Diamond","Gold","Platinum","Master",
    "Pro","Ultra","King+","Emperor","Titan",
    "Mythic","Hero","VIP","Boss","God"
]

# ================= HELPERS =================
def get_user(uid):
    c.execute("SELECT points,messages,title FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (uid,))
        conn.commit()
        return 0,0,"مبتدئ"
    return row

def save_user(uid, p, m, t):
    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
              (p,m,t,uid))
    conn.commit()

def get_title(points):
    return TITLES[min(points // 50, len(TITLES)-1)]

# ================= MESSAGE HANDLER =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    user = update.effective_user
    uid = user.id
    text = update.message.text

    points, messages, title = get_user(uid)

    # ===== ADMIN STATES =====
    if uid in admin_state:

        state = admin_state[uid]

        # add points
        if state.startswith("add_points_"):
            target = int(state.split("_")[2])
            amount = int(text)

            p,m,t = get_user(target)
            p += amount
            save_user(target, p, m, t)

            await update.message.reply_text("✅ تم إضافة النقاط")
            admin_state.pop(uid)
            return

        # add question step 1
        if state == "q1":
            admin_state[uid] = {"q": text}
            await update.message.reply_text("✏️ اكتب الجواب:")
            return

        # add question step 2
        if isinstance(state, dict):
            c.execute("INSERT INTO questions (q,a) VALUES (?,?)",
                      (state["q"], text))
            conn.commit()

            await update.message.reply_text("✅ تم إضافة السؤال")
            admin_state.pop(uid)
            return

        # search user
        if state == "search":
            c.execute("SELECT user_id FROM users")
            users = c.fetchall()

            found = []
            for u in users:
                try:
                    chat = await context.bot.get_chat(u[0])
                    name = chat.first_name or ""
                    if text.lower() in name.lower():
                        found.append((u[0], name))
                except:
                    pass

            if not found:
                await update.message.reply_text("لا يوجد نتائج")
            else:
                for f in found:
                    kb = [[InlineKeyboardButton(f[1], callback_data=f"user_{f[0]}")]]
                    await update.message.reply_text("نتيجة:", reply_markup=InlineKeyboardMarkup(kb))

            admin_state.pop(uid)
            return

    # ===== ANSWER SYSTEM =====
    c.execute("SELECT q,a FROM active_q WHERE user_id=?", (uid,))
    active = c.fetchone()

    if active:
        correct = active[1]

        if text.strip().lower() == correct.strip().lower():
            await update.message.reply_text("✅ الجواب صحيح")
            points += 5
        else:
            await update.message.reply_text(f"❌ الجواب خاطئ\nالإجابة: {correct}")

        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

        save_user(uid, points, messages, get_title(points))
        return

    # ===== COMMANDS =====
    if text == "معلوماتي":
        await update.message.reply_text(
            f"""👤 معلوماتك: @{user.username or user.first_name}

🔢 النقاط: {points}
💬 الرسائل: {messages}
🏅 اللقب: {title}"""
        )
        return

    if text == "سؤال":
        c.execute("SELECT q,a FROM questions ORDER BY RANDOM() LIMIT 1")
        q = c.fetchone()

        if q:
            c.execute("REPLACE INTO active_q VALUES (?,?,?)",(uid,q[0],q[1]))
            conn.commit()
            await update.message.reply_text(f"❓ {q[0]}")
        else:
            await update.message.reply_text("لا توجد أسئلة")
        return

    # ===== NORMAL MESSAGE =====
    old_title = title

    points += 1
    messages += 1

    new_title = get_title(points)

    save_user(uid, points, messages, new_title)

    # 🔔 global rank up
    if new_title != old_title:
        await update.message.reply_text(
            f"""🎉 إشعار ترقية!

👤 @{user.username or user.first_name}
🏅 {new_title}
🔢 نقاط: {points}"""
        )

# ================= ADMIN PANEL =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("🔍 بحث", callback_data="search")],
        [InlineKeyboardButton("➕ إضافة سؤال", callback_data="add_q")]
    ]

    await update.message.reply_text(
        "🛠 لوحة الأدمن",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= CALLBACK =================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    # list users
    if q.data == "users":
        c.execute("SELECT user_id FROM users")
        users = c.fetchall()

        for u in users:
            try:
                chat = await context.bot.get_chat(u[0])
                name = chat.first_name

                kb = [[InlineKeyboardButton(name, callback_data=f"user_{u[0]}")]]
                await q.message.reply_text(name, reply_markup=InlineKeyboardMarkup(kb))
            except:
                pass

    # select user
    elif q.data.startswith("user_"):
        target = int(q.data.split("_")[1])

        kb = [
            [InlineKeyboardButton("➕ نقاط", callback_data=f"add_{target}")]
        ]

        await q.message.reply_text("اختر:", reply_markup=InlineKeyboardMarkup(kb))

    # add points
    elif q.data.startswith("add_"):
        target = q.data.split("_")[1]
        admin_state[uid] = f"add_points_{target}"
        await q.message.reply_text("✏️ اكتب عدد النقاط:")

    # search
    elif q.data == "search":
        admin_state[uid] = "search"
        await q.message.reply_text("🔍 اكتب اسم العضو:")

    # add question
    elif q.data == "add_q":
        admin_state[uid] = "q1"
        await q.message.reply_text("✏️ اكتب السؤال:")

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("admin", admin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(callback))

print("Bot Running...")
app.run_polling()
