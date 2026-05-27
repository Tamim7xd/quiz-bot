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

# ================= 25 TITLES =================
TITLES = [
"مبتدئ","متعلم","نشط","مشارك","متفاعل",
"مميز","محترف","بارع","نشيط جداً","خبير",
"نجم","أسطورة","قائد","ملك الدردشة","بطل",
"Legend","Elite","Pro","Master","Diamond",
"Gold","Platinum","Titan","Emperor","Mythic"
]

# ================= 150 AUTO QUESTIONS =================
QUESTIONS = [
("ما هي عاصمة العراق؟","بغداد"),
("ما هي عاصمة فرنسا؟","باريس"),
("ما هو أطول نهر في العالم؟","النيل"),
("ما هي عاصمة اليابان؟","طوكيو"),
("كم عدد قارات العالم؟","7"),
("ما هو أكبر كوكب؟","المشتري"),
("ما هي عاصمة مصر؟","القاهرة"),
("من هو مكتشف الكهرباء؟","فاراداي"),
("ما هي عاصمة تركيا؟","أنقرة"),
("كم عدد أيام السنة؟","365"),
]

# نكررها لتصبح 150 سؤال تلقائيًا
while len(QUESTIONS) < 150:
    base = random.choice(QUESTIONS)
    QUESTIONS.append(base)

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

# ================= START INFO =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك في البوت\nاكتب: معلوماتي - سؤال")

# ================= MAIN =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    text = update.message.text

    points, messages, title = get_user(uid)

    # ================= ANSWER SYSTEM =================
    c.execute("SELECT q,a FROM active_q WHERE user_id=?", (uid,))
    active = c.fetchone()

    if active:
        if text.strip().lower() == active[1].strip().lower():
            await update.message.reply_text("✅ صحيح")
            points += 5
        else:
            await update.message.reply_text(f"❌ خطأ\nالإجابة: {active[1]}")

        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

        save_user(uid, points, messages, get_title(points))
        return

    # ================= INFO =================
    if text == "معلوماتي":
        await update.message.reply_text(
f"""👤 معلوماتك
🔢 نقاط: {points}
💬 رسائل: {messages}
🏅 لقب: {title}"""
        )
        return

    # ================= QUESTION =================
    if text == "سؤال":
        q = random.choice(QUESTIONS)

        c.execute("REPLACE INTO active_q VALUES (?,?,?)",(uid,q[0],q[1]))
        conn.commit()

        await update.message.reply_text(f"❓ {q[0]}")
        return

    # ================= NORMAL MESSAGE =================
    old_title = title

    points += 1
    messages += 1

    new_title = get_title(points)

    save_user(uid, points, messages, new_title)

    # 🔔 rank up
    if new_title != old_title:
        await update.message.reply_text(
f"""🎉 ترقية جديدة!

👤 {user.first_name}
🏅 {new_title}
🔢 {points} نقطة"""
        )

# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("➕ نقاط", callback_data="add")],
        [InlineKeyboardButton("🏅 لقب", callback_data="title")],
        [InlineKeyboardButton("🔍 بحث", callback_data="search")]
    ]
    await update.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= CALLBACK =================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(callback))

print("BOT RUNNING...")
app.run_polling()
