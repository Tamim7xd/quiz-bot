import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    title TEXT DEFAULT '🌱 عضو جديد',
    title_locked INTEGER DEFAULT 0
)
""")

conn.commit()

admin_state = {}

# ================= 50 TITLES (FIXED & CLEAN) =================
TITLES = [
"🌱 عضو جديد","🌿 مبتدئ","🌿 مبتدئ نشيط","⚡ متعلم","⚡ متطور",
"🔥 نشيط","🔥 متفاعل","🚀 متقدم","🚀 مميز","🎯 محترف",
"🎯 قوي","⭐ بارع","⭐ ذكي","🏅 متميز","🏅 متألق",
"🥇 بطل","🥇 مقاتل","👑 قائد","👑 ملك","💎 خبير",
"💎 أسطورة","⚔️ محارب","⚔️ مقاتل قوي","🛡️ حارس","🛡️ درع",
"🌍 رحالة","🎮 لاعب","🎮 محترف ألعاب","🧠 عبقري","📚 مثقف",
"🌟 نجم","🌟 سوبر ستار","🔥 أسطورة نار","⚡ قوة خارقة","🚀 صاروخ",
"🏆 بطل العالم","🏆 أسطورة عليا","👑 ملك الملوك","💎 لؤلؤة",
"🌟 نور","⚡ كهرباء","🔥 بركان","🚀 فضائي","🎯 دقيق",
"🧠 مفكر","📚 عالم","🌍 عالمي","💥 مدمر","👑 أسطورة مطلقة"
]

# ================= TITLE SYSTEM =================
def get_title(points):
    index = min(points // 200, len(TITLES) - 1)
    return TITLES[index]

# ================= REGISTER =================
def register(uid, name):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",
                  (uid, name, 0, 0, TITLES[0], 0))
        conn.commit()

# ================= ADMIN PANEL =================
async def admin(update, context):
    q = update.callback_query
    await q.answer()

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📢 إرسال للقناة", callback_data="send")]
    ]

    await q.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= USERS LIST =================
async def users(update, context):
    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name,points,title FROM users LIMIT 30")
    rows = c.fetchall()

    kb = [[InlineKeyboardButton(f"{n} | {p} | {t}", callback_data=f"user_{u}")]
          for u,n,p,t in rows]

    await q.message.reply_text("👥 الأعضاء:", reply_markup=InlineKeyboardMarkup(kb))

# ================= USER MENU =================
async def user_menu(update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    kb = [
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data=f"add_{uid}")],
        [InlineKeyboardButton("➖ خصم نقاط", callback_data=f"sub_{uid}")],
        [InlineKeyboardButton("✏️ تعديل لقب", callback_data=f"title_{uid}")],
        [InlineKeyboardButton("🔒 قفل/فتح لقب", callback_data=f"lock_{uid}")]
    ]

    await q.message.reply_text("⚙️ إدارة العضو", reply_markup=InlineKeyboardMarkup(kb))

# ================= FIXED MESSAGE SYSTEM =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text
    name = update.effective_user.first_name

    register(uid, name)

    # ================= 🔥 خصم بالرد =================
    if text.startswith("$خصم") and update.message.reply_to_message:
        if uid != ADMIN_ID:
            return

        parts = text.split()
        amount = int(parts[1])
        reason = " ".join(parts[2:]) if len(parts) > 2 else "بدون سبب"

        target = update.message.reply_to_message.from_user.id
        tname = update.message.reply_to_message.from_user.first_name

        c.execute("SELECT points FROM users WHERE user_id=?", (target,))
        p = c.fetchone()[0]

        new = max(0, p - amount)

        c.execute("UPDATE users SET points=? WHERE user_id=?", (new, target))
        conn.commit()

        await update.message.reply_text(
            f"❌ تم خصم {amount} من {tname}\n📝 السبب: {reason}"
        )

        if GROUP_ID:
            await context.bot.send_message(
                GROUP_ID,
                f"🚨 خصم نقاط\n👤 {tname}\n❌ -{amount}\n📝 {reason}"
            )
        return

    # ================= SYSTEM =================
    c.execute("SELECT points,messages,title_locked,title FROM users WHERE user_id=?", (uid,))
    p, m, locked, old_title = c.fetchone()

    p += 1
    m += 1

    new_title = get_title(p) if locked == 0 else old_title

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
              (p,m,new_title,uid))
    conn.commit()

# ================= ROUTER =================
async def router(update, context):
    q = update.callback_query
    d = q.data

    if d == "admin":
        await admin(update, context)
    elif d == "users":
        await users(update, context)
    elif d.startswith("user_"):
        await user_menu(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("بوت شغال")))
app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT FIXED RUNNING 🚀")
app.run_polling()
