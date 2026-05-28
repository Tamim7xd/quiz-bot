import os
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

if not TOKEN:
    raise Exception("BOT_TOKEN missing")

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
name TEXT,
points INTEGER DEFAULT 0,
messages INTEGER DEFAULT 0,
title TEXT DEFAULT '👤 عضو جديد',
title_locked INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS active_q (
user_id INTEGER PRIMARY KEY,
answer TEXT
)
""")
conn.commit()

# ================= TITLES (50) =================
TITLES = [
"🌱 مبتدئ","🌿 متعلم","⚡ نشيط","🔥 متفاعل","🚀 متقدم",
"🎯 محترف","⭐ مميز","🏅 بطل","🥇 نجم","👑 قائد",
"💎 خبير","🏆 أسطورة","⚔️ محارب","🛡️ حارس","🌟 سوبر ستار",
"💥 خارق","🎮 لاعب","🧩 محلل","📚 مثقف","🌍 رحّالة",
"💠 أسطورة عليا","🔥 أسطورة نارية","⚡ أسطورة كهرباء","🌪️ إعصار","☄️ نيزك",
"👑 ملك","💎 ملك الألماس","🏆 أسطورة ذهبية","🥇 أسطورة فضية","🥈 أسطورة برونزية",
"🎯 صائد","🚀 فضائي","🧠 عبقري","🧿 حكيم","🦅 صقر",
"🐉 تنين","🗡️ مقاتل","🛡️ حارس النخبة","💣 مدمر","⚡ سريع",
"🎮 محترف ألعاب","📊 محلل بيانات","🧠 مفكر","🌍 عالمي","🔥 أسطورة المجتمع",
"💎 VIP","🏆 Legend","👑 Supreme","⚔️ Warrior Pro","🌟 Elite"
]

def get_title(points):
    if points < 200:
        return "👤 عضو جديد"
    level = points // 200
    if level >= len(TITLES):
        return TITLES[-1]
    return TITLES[level]

def progress(points):
    return points % 200

# ================= QUESTIONS =================
QUESTIONS = [
("ما عاصمة العراق؟","بغداد"),
("ما عاصمة السعودية؟","الرياض"),
("ما عاصمة مصر؟","القاهرة"),
("ما أكبر قارة؟","آسيا"),
("أسرع حيوان؟","الفهد"),
("ما لون السماء؟","أزرق")
]

def get_q():
    return random.choice(QUESTIONS)

# ================= ADMIN STATE =================
admin_state = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك في البوت")

# ================= HANDLE MESSAGES =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    text = update.message.text

    # register
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,0)", (uid, name, 0, 0))
        conn.commit()

    # ================= ADMIN $COMMAND =================
    if text.startswith("$") and uid == ADMIN_ID:
        parts = text.split()
        cmd = parts[0]

        # خصم
        if cmd == "$خصم":
            amount = int(parts[1])
            reason = " ".join(parts[2:]) if len(parts) > 2 else "بدون سبب"

            c.execute("SELECT points FROM users WHERE user_id=?", (uid,))
            old = c.fetchone()[0]
            new = max(0, old - amount)

            c.execute("UPDATE users SET points=? WHERE user_id=?", (new, uid))
            conn.commit()

            msg = f"❌ تم خصم {amount} من {name}\n📝 السبب: {reason}"
            await update.message.reply_text(msg)

            if GROUP_ID:
                await context.bot.send_message(GROUP_ID, msg)
            return

    # ================= QUESTION =================
    if text == "سؤال":
        q, a = get_q()
        c.execute("REPLACE INTO active_q VALUES (?,?)", (uid, a))
        conn.commit()
        await update.message.reply_text(q)
        return

    # answer check
    c.execute("SELECT answer FROM active_q WHERE user_id=?", (uid,))
    row = c.fetchone()

    add = 1
    if row:
        if text.lower() == row[0].lower():
            add = 5
            await update.message.reply_text("✅ صحيح +5")
        else:
            await update.message.reply_text(f"❌ خطأ الجواب: {row[0]}")
        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

    # ================= UPDATE USER =================
    c.execute("SELECT points,messages,title_locked FROM users WHERE user_id=?", (uid,))
    p,m,lock = c.fetchone()

    old_title = get_title(p)
    p += add
    m += 1

    new_title = old_title if lock else get_title(p)

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
              (p,m,new_title,uid))
    conn.commit()

    # ================= LEVEL UP =================
    if new_title != old_title and not lock:
        msg = f"🎉 ترقية جديدة!\n🏅 {name}\n{new_title}\n⭐ XP: {progress(p)}/200"

        await update.message.reply_text(msg)

        if GROUP_ID:
            await context.bot.send_message(GROUP_ID, msg)

# ================= ADMIN PANEL =================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📢 إرسال للقناة", callback_data="send")]
    ]
    await update.message.reply_text("⚙️ لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= CALLBACK =================
async def cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "users":
        c.execute("SELECT user_id,name,points,title FROM users LIMIT 20")
        users = c.fetchall()

        kb = []
        for u in users:
            kb.append([InlineKeyboardButton(f"{u[1]} | {u[2]} | {u[3]}", callback_data=f"u_{u[0]}")])

        await q.message.reply_text("👥 الأعضاء", reply_markup=InlineKeyboardMarkup(kb))

# ================= MAIN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("panel", panel))
app.add_handler(CallbackQueryHandler(cb))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING")
app.run_polling()
