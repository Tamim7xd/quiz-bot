import os
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    title TEXT DEFAULT 'مبتدئ'
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

# ================= TITLES (25 احترافي) =================
TITLES = [
"مبتدئ","مشارك","نشط","متعلم","متفاعل",
"مميز","محترف","خبير","نجم","أسطورة",
"قائد","ملك الدردشة","بطل","Legend","Elite",
"Pro","Master","Diamond","Gold","Platinum",
"Titan","Emperor","Mythic","Hero","God"
]

# ================= 150 QUESTIONS AUTO =================
BASE_Q = [
("ما هي عاصمة العراق؟","بغداد"),
("ما هي عاصمة فرنسا؟","باريس"),
("ما هي عاصمة اليابان؟","طوكيو"),
("ما هو أكبر كوكب؟","المشتري"),
("ما هو أطول نهر؟","النيل"),
("كم عدد قارات العالم؟","7"),
]

QUESTIONS = (BASE_Q * 30)[:150]

# ================= HELPERS =================
def get_user(uid, name):
    c.execute("SELECT points,messages,title FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users VALUES (?,?,0,0,'مبتدئ')", (uid,name))
        conn.commit()
        return 0,0,"مبتدئ"
    return row

def save_user(uid, name, p, m, t):
    c.execute("UPDATE users SET name=?,points=?,messages=?,title=? WHERE user_id=?",
              (name,p,m,t,uid))
    conn.commit()

def get_title(points):
    return TITLES[min(points // 50, len(TITLES)-1)]

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id == ADMIN_ID:
        kb = [
            [InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="panel")]
        ]
        await update.message.reply_text("🔥 أهلاً أدمن", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text("👋 أهلاً بك\nاكتب: معلوماتي / سؤال")

# ================= MAIN =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    name = user.first_name
    text = update.message.text

    points, messages, title = get_user(uid, name)

    # ================= ANSWER =================
    c.execute("SELECT q,a FROM active_q WHERE user_id=?", (uid,))
    active = c.fetchone()

    if active:
        correct = active[1]

        if text.lower() == correct.lower():
            await update.message.reply_text("✅ صحيح +5 نقاط")
            points += 5
        else:
            await update.message.reply_text(f"❌ خطأ\nالإجابة: {correct}")

        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

        save_user(uid,name,points,messages,title)
        return

    # ================= INFO =================
    if text == "معلوماتي":
        await update.message.reply_text(
f"""👤 معلوماتك:
🔢 نقاط: {points}
💬 رسائل: {messages}
🏅 لقب: {title}"""
        )
        return

    # ================= QUESTION =================
    if text == "سوال":
        q = random.choice(QUESTIONS)
        c.execute("REPLACE INTO active_q VALUES (?,?,?)",(uid,q[0],q[1]))
        conn.commit()
        await update.message.reply_text(f"❓ {q[0]}")
        return

    # ================= NORMAL =================
    old_title = title

    points += 1
    messages += 1
    new_title = get_title(points)

    save_user(uid,name,points,messages,new_title)

    # 🔔 rank up global
    if new_title != old_title:
        await update.message.reply_text(
f"""🎉 ترقية!

👤 {name}
🏅 {new_title}
🔢 {points} نقطة"""
        )

# ================= ADMIN PANEL =================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    # ===== PANEL =====
    if q.data == "panel":
        if uid != ADMIN_ID:
            return

        kb = [
            [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
            [InlineKeyboardButton("➕ نقاط", callback_data="add_points")],
            [InlineKeyboardButton("🏅 إعطاء لقب", callback_data="set_title")]
        ]

        await q.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

    # ===== USERS =====
    elif q.data == "users":
        if uid != ADMIN_ID:
            return

        c.execute("SELECT user_id,name,points FROM users")
        users = c.fetchall()

        for u in users:
            kb = [[InlineKeyboardButton(
                f"{u[1]} | {u[2]} نقطة",
                callback_data=f"u_{u[0]}"
            )]]
            await q.message.reply_text("👤 عضو:", reply_markup=InlineKeyboardMarkup(kb))

    # ===== SELECT USER =====
    elif q.data.startswith("u_"):
        if uid != ADMIN_ID:
            return

        target = int(q.data.split("_")[1])

        kb = [
            [InlineKeyboardButton("➕ نقاط", callback_data=f"ap_{target}")],
            [InlineKeyboardButton("🏅 لقب", callback_data=f"al_{target}")]
        ]

        await q.message.reply_text("⚙️ إدارة العضو", reply_markup=InlineKeyboardMarkup(kb))

    # ===== ADD POINTS =====
    elif q.data.startswith("ap_"):
        target = int(q.data.split("_")[1])
        admin_state[uid] = ("points", target)
        await q.message.reply_text("✏️ اكتب عدد النقاط:")

    # ===== ADD TITLE =====
    elif q.data.startswith("al_"):
        target = int(q.data.split("_")[1])
        admin_state[uid] = ("title", target)
        await q.message.reply_text("✏️ اكتب اللقب:")

# ================= ADMIN INPUT =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    text = update.message.text

    if uid not in admin_state:
        return

    action, target = admin_state[uid]
    name = user.first_name

    if action == "points":
        c.execute("SELECT points,messages,title,name FROM users WHERE user_id=?", (target,))
        row = c.fetchone()

        if row:
            p,m,t,n = row
            p += int(text)

            c.execute("UPDATE users SET points=? WHERE user_id=?", (p,target))
            conn.commit()

        await update.message.reply_text("✅ تم إضافة النقاط")

    elif action == "title":
        c.execute("UPDATE users SET title=? WHERE user_id=?", (text,target))
        conn.commit()

        await update.message.reply_text("🏅 تم إعطاء اللقب")

    admin_state.pop(uid)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

print("PRO MIX BOT RUNNING...")
app.run_polling()
