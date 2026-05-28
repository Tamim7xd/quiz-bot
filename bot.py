import os
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

# ================= DB =================
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

# ================= XP =================
def xp_bar(points):
    percent = (points % 200) / 200
    bar = int(percent * 10)
    return "█" * bar + "░" * (10 - bar)

# ================= TITLES 50 =================
def get_title(points):
    if points < 200:
        return "🌱 عضو جديد"

    titles = [
        "🟢 مبتدئ","🔵 متعلم","🟣 نشيط","🟡 متقدم","🟠 محترف",
        "🔴 مميز","🟢 بطل","🔵 نجم","🟣 قائد","🟡 خبير",
        "🟠 محارب","🔴 مقاتل","🟢 حارس","🔵 أسطورة","🟣 ملك",
        "💎 خبير","⚡ محترف","🔥 قوي","👑 قائد","🏆 بطل",
        "🌟 نجم","🚀 متقدم","🎯 ذكي","🧠 عبقري","📚 مثقف",
        "🌍 رحّال","🛡️ حارس","⚔️ محارب","🎮 لاعب","💥 خارق",
        "🏅 مميز","🥇 ذهبي","👑 ملك الملوك","💎 أسطورة","⚡ خارق",
        "🔥 أسطورة النار","🌟 أسطورة الضوء","🚀 أسطورة الفضاء",
        "👑 الملك الأعلى","🏆 أسطورة العالم"
    ]

    level = points // 200
    return titles[level] if level < len(titles) else "👑 أسطورة مطلقة"

# ================= REGISTER =================
def register(uid, name):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",
                  (uid, name, 0, 0, "🌱 عضو جديد", 0))
        conn.commit()

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="admin")]] if update.effective_user.id == ADMIN_ID else []
    await update.message.reply_text("👋 أهلاً بك", reply_markup=InlineKeyboardMarkup(kb) if kb else None)

# ================= ADMIN PANEL =================
async def admin(update, context):
    q = update.callback_query
    await q.answer()

    kb = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")],
        [InlineKeyboardButton("📢 إرسال للقناة", callback_data="send")]
    ]

    await q.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

# ================= USERS =================
async def users(update, context):
    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name,points,title FROM users LIMIT 30")
    rows = c.fetchall()

    kb = [[InlineKeyboardButton(f"{n} | {p} | {t}", callback_data=f"user_{u}")] for u,n,p,t in rows]

    await q.message.reply_text("👥 الأعضاء:", reply_markup=InlineKeyboardMarkup(kb))

# ================= USER MENU =================
async def user_menu(update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    kb = [
        [InlineKeyboardButton("➕ نقاط", callback_data=f"add_{uid}")],
        [InlineKeyboardButton("➖ خصم", callback_data=f"sub_{uid}")],
        [InlineKeyboardButton("✏️ لقب", callback_data=f"title_{uid}")],
        [InlineKeyboardButton("🔒 قفل/فتح", callback_data=f"lock_{uid}")]
    ]

    await q.message.reply_text("⚙️ إدارة العضو", reply_markup=InlineKeyboardMarkup(kb))

# ================= HANDLE =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text
    name = update.effective_user.first_name

    register(uid, name)

    # ================= 💥 خصم بالرد =================
    if text.startswith("$خصم") and update.message.reply_to_message:
        if uid != ADMIN_ID:
            return

        try:
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

            await update.message.reply_text(f"❌ تم خصم {amount} من {tname}\n📝 {reason}")

            if GROUP_ID:
                await context.bot.send_message(
                    GROUP_ID,
                    f"🚨 خصم نقاط\n👤 {tname}\n❌ -{amount}\n📝 {reason}"
                )

        except:
            await update.message.reply_text("خطأ في الخصم")
        return

    # ================= SYSTEM =================
    c.execute("SELECT points,messages,title_locked,title FROM users WHERE user_id=?", (uid,))
    p, m, locked, old = c.fetchone()

    p += 1
    m += 1

    new_title = get_title(p) if locked == 0 else old

    c.execute("UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
              (p,m,new_title,uid))
    conn.commit()

    # ================= XP =================
    await update.message.reply_text(
        f"""👤 {name}

💰 {p} نقطة
🏆 {new_title}

📊 XP
[{xp_bar(p)}] {p%200}/200
"""
    )

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
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("BOT RUNNING 🚀")
app.run_polling()
