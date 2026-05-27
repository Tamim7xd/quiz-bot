import os
import random
import sqlite3
import json

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

# ================= DATABASE =================
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS titles (
    min_points INTEGER,
    title TEXT
)
""")

conn.commit()

state = {}
active_q = {}

# ================= BACKUP =================
def save_json():
    data = {}
    cursor.execute("SELECT * FROM users")
    for r in cursor.fetchall():
        data[r[0]] = {
            "name": r[1],
            "points": r[2],
            "messages": r[3],
            "title": r[4]
        }

    with open("backup.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= 25 TITLES =================
def init_titles():
    if cursor.execute("SELECT COUNT(*) FROM titles").fetchone()[0] == 0:
        base = [
            (0, "👶 مبتدئ"),
            (20, "🌱 مبتدئ نشط"),
            (50, "🥉 متعلم"),
            (100, "🥈 نشط"),
            (200, "🥇 محترف"),
            (500, "🔥 خبير"),
            (1000, "🏆 أسطورة"),
            (2000, "👑 ملك"),
            (5000, "💎 أسطوري"),
            (10000, "⚔️ خارق"),
            (15000, "🧠 عبقري"),
            (20000, "🌌 أسطورة العالم"),
            (30000, "💀 مرعب"),
            (40000, "🚀 فضائي"),
            (50000, "👑 ملك الملوك"),
            (60000, "🔥 نار"),
            (70000, "💠 نادر"),
            (80000, "🌀 أسطوري جداً"),
            (90000, "🏆 بطل"),
            (100000, "💎 لا يُهزم"),
            (120000, "⚡ سريع"),
            (140000, "🧿 حكيم"),
            (160000, "🔱 قائد"),
            (180000, "👁️ مراقب"),
            (200000, "🌟 نجم خارق"),
        ]
        cursor.executemany("INSERT INTO titles VALUES (?,?)", base)
        conn.commit()

init_titles()

# ================= QUESTIONS (150+) =================
QUESTIONS = []

# easy 60
for _ in range(60):
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    QUESTIONS.append((f"كم {a}+{b}؟", str(a+b)))

# medium 60
for _ in range(60):
    a = random.randint(10, 50)
    b = random.randint(10, 50)
    QUESTIONS.append((f"كم {a}+{b}؟", str(a+b)))

# hard 30
for _ in range(30):
    a = random.randint(50, 200)
    b = random.randint(50, 200)
    QUESTIONS.append((f"كم {a}+{b}؟", str(a+b)))

# general
QUESTIONS += [
    ("ما عاصمة العراق؟", "بغداد"),
    ("ما عاصمة فرنسا؟", "باريس"),
    ("ما عاصمة مصر؟", "القاهرة"),
    ("ما عاصمة السعودية؟", "الرياض"),
    ("ما عاصمة أمريكا؟", "واشنطن"),
    ("ما أكبر كوكب؟", "المشتري"),
    ("ما عدد الكواكب؟", "8"),
    ("ما أعلى جبل؟", "إيفرست"),
    ("ما أكبر محيط؟", "الهادئ"),
]

# ================= HELPERS =================
def is_admin(uid):
    return int(uid) == ADMIN_ID


def get_user(uid, name=""):
    cursor.execute("SELECT points, messages, title FROM users WHERE user_id=?", (str(uid),))
    row = cursor.fetchone()

    if not row:
        cursor.execute("INSERT INTO users VALUES (?,?,?,?,?)",
                       (str(uid), name, 0, 0, "👶 مبتدئ"))
        conn.commit()
        save_json()
        return (0, 0, "👶 مبتدئ")

    return row


def add_points(uid, v):
    p, m, t = get_user(uid)
    cursor.execute("UPDATE users SET points=? WHERE user_id=?", (p + v, str(uid)))
    conn.commit()
    save_json()


def add_message(uid):
    p, m, t = get_user(uid)
    cursor.execute("UPDATE users SET messages=? WHERE user_id=?", (m + 1, str(uid)))
    conn.commit()
    save_json()


def get_top():
    cursor.execute("SELECT name, points FROM users ORDER BY points DESC LIMIT 10")
    return cursor.fetchall()


# ================= ADMIN MENU =================
def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 المستخدمين", callback_data="users")],
        [InlineKeyboardButton("🏷️ الألقاب", callback_data="titles")],
        [InlineKeyboardButton("💰 نقاط جماعية", callback_data="global")]
    ])


def user_panel(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ نقاط", callback_data=f"p_{uid}")],
        [InlineKeyboardButton("📨 رسائل", callback_data=f"m_{uid}")],
        [InlineKeyboardButton("🏷️ لقب", callback_data=f"t_{uid}")],
        [InlineKeyboardButton("❌ حذف", callback_data=f"d_{uid}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="users")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    get_user(uid, update.effective_user.first_name)

    if is_admin(uid):
        await update.message.reply_text("👑 لوحة التحكم", reply_markup=admin_menu())
    else:
        await update.message.reply_text("👋 اكتب: سوال / معلوماتي / top")

# ================= TRACK =================
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    get_user(uid, update.effective_user.first_name)
    add_message(uid)

    if text in ["سوال", "سؤال"]:
        q, a = random.choice(QUESTIONS)
        active_q[uid] = a
        await update.message.reply_text(q)
        return

    if text == "معلوماتي":
        p, m, t = get_user(uid)
        await update.message.reply_text(f"⭐ {p}\n📨 {m}\n🏷️ {t}")
        return

    if text == "top":
        top = get_top()
        msg = "🏆 TOP 10\n\n"
        for i, (n, p) in enumerate(top, 1):
            msg += f"{i}) {n} ⭐ {p}\n"
        await update.message.reply_text(msg)
        return

    if uid in active_q:
        if text.lower() == active_q[uid].lower():
            add_points(uid, 1)
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

    if data == "users":
        cursor.execute("SELECT user_id,name,points FROM users")
        rows = cursor.fetchall()

        keyboard = [
            [InlineKeyboardButton(f"{r[1]} ⭐{r[2]}", callback_data=f"user_{r[0]}")]
            for r in rows
        ]

        await q.edit_message_text("👤 المستخدمين:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("user_"):
        target = data.split("_")[1]
        state[uid] = {"target": target}
        await q.edit_message_text("⚙️ اختر:", reply_markup=user_panel(target))

    elif data.startswith("p_"):
        state[uid] = {"target": data.split("_")[1], "mode": "points"}
        await q.edit_message_text("⭐ ارسل النقاط")

    elif data.startswith("m_"):
        state[uid] = {"target": data.split("_")[1], "mode": "msgs"}
        await q.edit_message_text("📨 ارسل الرسائل")

    elif data.startswith("t_"):
        state[uid] = {"target": data.split("_")[1], "mode": "title"}
        await q.edit_message_text("🏷️ ارسل اللقب")

    elif data.startswith("d_"):
        target = data.split("_")[1]
        cursor.execute("DELETE FROM users WHERE user_id=?", (target,))
        conn.commit()
        save_json()
        await q.edit_message_text("❌ تم الحذف")

    elif data == "global":
        state[uid] = {"mode": "global"}
        await q.edit_message_text("💰 ارسل النقاط الجماعية")

# ================= TEXT =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    if uid not in state:
        return

    s = state[uid]

    if s["mode"] == "points":
        cursor.execute("UPDATE users SET points=? WHERE user_id=?", (int(text), s["target"]))
        conn.commit()
        save_json()

    elif s["mode"] == "msgs":
        cursor.execute("UPDATE users SET messages=? WHERE user_id=?", (int(text), s["target"]))
        conn.commit()
        save_json()

    elif s["mode"] == "title":
        cursor.execute("UPDATE users SET title=? WHERE user_id=?", (text, s["target"]))
        conn.commit()
        save_json()

    elif s["mode"] == "global":
        cursor.execute("UPDATE users SET points = points + ?", (int(text),))
        conn.commit()
        save_json()

    del state[uid]
    await update.message.reply_text("✔️ تم التنفيذ")

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
