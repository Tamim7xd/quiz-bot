import os
import sqlite3
import random
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= 🔥 ENV CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
GROUP_ID = os.getenv("GROUP_ID")

# تحويل آمن
if not TOKEN:
    raise Exception("BOT_TOKEN is missing")

try:
    ADMIN_ID = int(ADMIN_ID)
except:
    raise Exception("ADMIN_ID must be number")

try:
    GROUP_ID = int(GROUP_ID) if GROUP_ID else None
except:
    GROUP_ID = None

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

# ================= TITLES =================
TITLES = [
"مبتدئ","نشط","متفاعل","محترف","نجم",
"أسطورة","قائد","ملك","بطل","Legend",
"Elite","Pro","Master","Diamond","Gold",
"Platinum","Titan","Emperor","Mythic","Hero",
"VIP","Boss","Ultra","King","God"
]

# ================= QUESTIONS =================
BASE = [
("ما هي عاصمة العراق؟","بغداد"),
("ما هي عاصمة فرنسا؟","باريس"),
("ما هو أكبر كوكب؟","المشتري"),
("ما هو أطول نهر؟","النيل"),
("كم عدد القارات؟","7"),
]

QUESTIONS = (BASE * 30)[:150]

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
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = [[InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="panel")]]
        await update.message.reply_text("🔥 أهلاً أدمن", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text("👋 أهلاً بك")

# ================= CALLBACK =================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if uid != ADMIN_ID:
        return

    if q.data == "panel":
        kb = [
            [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
            [InlineKeyboardButton("➕ نقاط", callback_data="p")],
            [InlineKeyboardButton("🏅 ألقاب", callback_data="t")]
        ]
        await q.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data == "users":
        c.execute("SELECT user_id,name,points FROM users")
        for u in c.fetchall():
            kb = [[InlineKeyboardButton(
                f"{u[1]} | {u[2]}",
                callback_data=f"user_{u[0]}"
            )]]
            await q.message.reply_text("👤 عضو:", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("user_"):
        target = int(q.data.split("_")[1])

        kb = [
            [InlineKeyboardButton("➕ نقاط", callback_data=f"setp_{target}")],
            [InlineKeyboardButton("🏅 لقب", callback_data=f"sett_{target}")]
        ]
        await q.message.reply_text("⚙️ اختر:", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("setp_"):
        admin_state[uid] = ("points", int(q.data.split("_")[1]))
        await q.message.reply_text("✏️ اكتب النقاط:")

    elif q.data.startswith("sett_"):
        admin_state[uid] = ("title", int(q.data.split("_")[1]))
        await q.message.reply_text("🏅 اكتب اللقب:")

# ================= MAIN =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        uid = user.id
        name = user.first_name
        text = update.message.text

        points, messages, title = get_user(uid, name)

        # ===== ADMIN INPUT =====
        if uid in admin_state:
            action, target = admin_state[uid]

            if action == "points":
                add = int(text)
                c.execute("SELECT points FROM users WHERE user_id=?", (target,))
                row = c.fetchone()

                if row:
                    c.execute("UPDATE users SET points=? WHERE user_id=?",
                              (row[0] + add, target))
                    conn.commit()

                await update.message.reply_text("✅ تم إعطاء النقاط")
                admin_state.pop(uid)
                return

            if action == "title":
                c.execute("UPDATE users SET title=? WHERE user_id=?", (text, target))
                conn.commit()

                await update.message.reply_text("🏅 تم إعطاء اللقب")
                admin_state.pop(uid)
                return

        # ===== INFO =====
        if text == "معلوماتي":
            await update.message.reply_text(
f"""👤 معلوماتك:
🔢 نقاط: {points}
💬 رسائل: {messages}
🏅 لقب: {title}"""
            )
            return

        # ===== QUESTION =====
        if text == "سؤال":
            q = random.choice(QUESTIONS)

            c.execute("REPLACE INTO active_q VALUES (?,?,?)",(uid,q[0],q[1]))
            conn.commit()

            await update.message.reply_text(f"❓ {q[0]}")
            return

        # ===== ANSWER =====
        c.execute("SELECT q,a FROM active_q WHERE user_id=?", (uid,))
        active = c.fetchone()

        if active:
            if text.lower() == active[1].lower():
                await update.message.reply_text("✅ صحيح +5")
                points += 5
            else:
                await update.message.reply_text(f"❌ خطأ: {active[1]}")

            c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
            conn.commit()

        # ===== NORMAL =====
        old = title

        points += 1
        messages += 1

        new = get_title(points)

        save_user(uid,name,points,messages,new)

        if new != old:
            await update.message.reply_text(f"🎉 ترقية: {new}")

    except Exception:
        await update.message.reply_text("⚠️ خطأ في النظام\n" + traceback.format_exc())

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🚀 BOT RUNNING (CLEAN ENV MODE)")
app.run_polling()
