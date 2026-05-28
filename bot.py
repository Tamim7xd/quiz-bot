import os
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
name TEXT,
points INTEGER DEFAULT 0,
messages INTEGER DEFAULT 0,
title TEXT DEFAULT '🌱 مبتدئ',
title_locked INTEGER DEFAULT 0
)""")

c.execute("""CREATE TABLE IF NOT EXISTS active_q(
user_id INTEGER PRIMARY KEY,
answer TEXT
)""")

conn.commit()

# ================= TITLES =================
TITLES = [
"🌱 مبتدئ","⚡ نشيط","🔥 متفاعل","🚀 متقدم","🎯 محترف",
"⭐ مميز","🏅 بطل","🥇 نجم","👑 قائد","💎 خبير",
"🏆 أسطورة","⚔️ محارب","🛡️ حارس","🌟 خارق","💥 قوي",
"🎮 لاعب","🧠 ذكي","📚 مثقف","🌍 رحّال","💠 أسطورة",
"👑 ملك","🤴 أمير","🦁 أسد","🐉 تنين","🦅 صقر",
"⚡ برق","🌪️ عاصفة","🔥 نار","❄️ جليد","🧿 محظوظ",
"💰 غني","🪙 ثري","🎯 قناص","🚁 طيار","🧩 محلل",
"🔬 عالم","🎨 مبدع","🎧 فنان","⚙️ مهندس","📡 مخترق",
"👽 فضائي","🤖 روبوت","⚔️ مقاتل","🏹 رامٍ","🐺 ذئب",
"☠️ قاتل","🌌 أسطورة الكون","👑 ملك الملوك","💀 نخبة","🏆 بطل مطلق"
]

def level(p): return p // 200

def title(p):
    l = level(p)
    return TITLES[l] if l < len(TITLES) else "👑 أسطورة نهائية"

def bar(p):
    x = p % 200
    return f"[{'█'*(x//20)}{'░'*(10-x//20)}] {x}/200"

# ================= QUESTIONS =================
QUESTIONS = [
("ما عاصمة العراق؟","بغداد"),
("ما عاصمة فرنسا؟","باريس"),
("ما أكبر كوكب؟","المشتري"),
("ما أطول نهر؟","النيل"),
("ما لغة القرآن؟","العربية"),
("كم عدد الصلوات؟","5"),
("ما الحيوان الأسرع؟","الفهد"),
("ما عملة أمريكا؟","الدولار"),
]

def q():
    return random.choice(QUESTIONS)

admin_state = {}
post_cache = {}

# ================= START =================
async def start(update, context):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        kb = [[InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="admin")]]
        await update.message.reply_text("🔥 أهلاً أدمن", reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text("👋 أهلاً بك في البوت")

# ================= ADMIN =================
async def admin(update, context):
    q = update.callback_query
    await q.answer()

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📊 المراتب", callback_data="ranks")],
        [InlineKeyboardButton("📢 إرسال للقناة", callback_data="post")],
        [InlineKeyboardButton("🎁 نقاط للجميع", callback_data="all")]
    ]

    await q.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= USERS =================
async def users(update, context):
    q = update.callback_query
    await q.answer()

    c.execute("SELECT name,points,title,user_id FROM users ORDER BY points DESC LIMIT 25")
    rows = c.fetchall()

    text = "🏆 قائمة الأعضاء:\n\n"
    for n,p,t,u in rows:
        text += f"{n} | {p} | {t}\n"

    await q.message.reply_text(text)

# ================= POST =================
async def post(update, context):
    q = update.callback_query
    await q.answer()

    admin_state[ADMIN_ID] = "post_text"
    await q.message.reply_text("✍️ أرسل الرسالة")

# ================= HANDLE =================
async def handle(update, context):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    text = update.message.text.strip()

    # register
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",(uid,name,0,0,"🌱 مبتدئ",0))
        conn.commit()

    # admin post
    if uid == ADMIN_ID and ADMIN_ID in admin_state:
        if admin_state[ADMIN_ID] == "post_text":
            post_cache[ADMIN_ID] = text
            admin_state[ADMIN_ID] = "post_pin"

            kb = [
                [InlineKeyboardButton("📌 تثبيت", callback_data="pin_yes")],
                [InlineKeyboardButton("❌ بدون", callback_data="pin_no")]
            ]

            await update.message.reply_text("تثبيت؟", reply_markup=InlineKeyboardMarkup(kb))
            return

    # question
    if text == "سؤال":
        qn, ans = q()
        c.execute("REPLACE INTO active_q VALUES (?,?)",(uid,ans))
        conn.commit()
        await update.message.reply_text(qn)
        return

    # answer
    c.execute("SELECT answer FROM active_q WHERE user_id=?", (uid,))
    r = c.fetchone()

    add = 1

    if r:
        if text.lower() == r[0].lower():
            add = 5
            await update.message.reply_text("✅ صحيح")
        else:
            await update.message.reply_text(f"❌ خطأ: {r[0]}")
        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

    c.execute("SELECT points,messages,title_locked FROM users WHERE user_id=?", (uid,))
    p,m,l = c.fetchone()

    old = title(p)
    p += add
    m += 1

    new = title(p) if l == 0 else old

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",(p,m,new,uid))
    conn.commit()

    if new != old:
        await update.message.reply_text(f"🎉 ترقية: {new}")

# ================= CALLBACK =================
async def cb(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "admin":
        await admin(update, context)

    elif data == "users":
        await users(update, context)

    elif data == "post":
        await post(update, context)

    elif data == "pin_yes":
        msg = await context.bot.send_message(GROUP_ID, post_cache[ADMIN_ID])
        await context.bot.pin_chat_message(GROUP_ID, msg.message_id)
        await q.message.reply_text("📌 تم التثبيت")

    elif data == "pin_no":
        await context.bot.send_message(GROUP_ID, post_cache[ADMIN_ID])
        await q.message.reply_text("📢 تم الإرسال")

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(cb))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING...")
app.run_polling()
