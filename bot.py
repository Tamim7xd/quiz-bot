import os
import random
import sqlite3
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
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
    min_points INTEGER PRIMARY KEY,
    title TEXT
)
""")

conn.commit()

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
            (100, "🥉 متطور"),
            (150, "🥈 نشط"),
            (200, "🥈 نشط جداً"),
            (300, "🥇 جيد"),
            (400, "🥇 محترف"),
            (500, "🔥 خبير"),
            (650, "⚡ متقدم"),
            (800, "🚀 قوي"),
            (1000, "🏆 مميز"),
            (1200, "🏆 متألق"),
            (1500, "👑 ملك"),
            (1800, "💎 نادر"),
            (2000, "💎 أسطوري"),
            (2500, "💀 مخيف"),
            (3000, "🌌 خارق"),
            (3500, "🌟 نجم"),
            (4000, "🧠 ذكي"),
            (5000, "🔥 أسطورة"),
            (6000, "👑 ملك الملوك"),
            (7500, "⚔️ محارب"),
            (9000, "🌀 أسطوري جداً"),
            (12000, "💠 النخبة"),
        ]
        cursor.executemany("INSERT INTO titles VALUES (?,?)", base)
        conn.commit()

init_titles()

# ================= +150 QUESTIONS =================
QUESTIONS = []

# 120 رياضيات
for i in range(120):
    a = random.randint(1, 50)
    b = random.randint(1, 50)
    QUESTIONS.append((f"كم {a} + {b}؟", str(a + b)))

# 30 عامة
general = [
    ("ما عاصمة العراق؟", "بغداد"),
    ("ما عاصمة فرنسا؟", "باريس"),
    ("ما عاصمة مصر؟", "القاهرة"),
    ("ما عاصمة السعودية؟", "الرياض"),
    ("ما عاصمة أمريكا؟", "واشنطن"),
    ("ما أكبر كوكب؟", "المشتري"),
    ("ما أصغر قارة؟", "أستراليا"),
    ("كم عدد القارات؟", "7"),
    ("كم عدد أيام الأسبوع؟", "7"),
    ("ما لون السماء؟", "أزرق"),
    ("ما الغاز الذي نتنفسه؟", "الأوكسجين"),
    ("ما رمز الماء؟", "H2O"),
    ("ما أطول نهر؟", "النيل"),
    ("ما أكبر دولة؟", "روسيا"),
    ("ما الحيوان الأسرع؟", "الفهد"),
    ("ما هو الإنترنت؟", "شبكة"),
    ("ما عاصمة تركيا؟", "أنقرة"),
    ("ما عملة العراق؟", "الدينار"),
    ("ما أقرب كوكب للشمس؟", "عطارد"),
    ("ما أكبر محيط؟", "الهادئ"),
    ("كم عدد العيون؟", "2"),
    ("ما مصدر الضوء؟", "الشمس"),
    ("ما الحيوان الصحراوي؟", "الجمل"),
    ("ما أعلى جبل؟", "إيفرست"),
    ("ما لون الدم؟", "أحمر"),
    ("ما الكوكب الأزرق؟", "الأرض"),
    ("ما عدد الكواكب؟", "8"),
    ("ما اللغة في العراق؟", "العربية"),
    ("ما أكبر قارة؟", "آسيا"),
    ("ما أصغر دولة؟", "الفاتيكان"),
]

QUESTIONS.extend(general)

# ================= MEMORY =================
active_q = {}
state = {}

# ================= HELPERS =================
def is_admin(uid):
    return int(uid) == ADMIN_ID


def get_user(uid, name=""):
    cursor.execute("SELECT points, messages, title FROM users WHERE user_id=?", (str(uid),))
    row = cursor.fetchone()

    if not row:
        cursor.execute(
            "INSERT INTO users VALUES (?,?,?,?,?)",
            (str(uid), name, 0, 0, "👶 مبتدئ")
        )
        conn.commit()
        save_json()
        return (0, 0, "👶 مبتدئ")

    return row


def update_title(uid):
    cursor.execute("SELECT points FROM users WHERE user_id=?", (str(uid),))
    row = cursor.fetchone()
    if not row:
        return

    points = row[0]

    cursor.execute("""
        SELECT title FROM titles
        WHERE min_points <= ?
        ORDER BY min_points DESC
        LIMIT 1
    """, (points,))

    title = cursor.fetchone()[0]

    cursor.execute("UPDATE users SET title=? WHERE user_id=?", (title, str(uid)))
    conn.commit()
    save_json()


def add_points(uid, v):
    p, m, t = get_user(uid)

    cursor.execute("UPDATE users SET points=? WHERE user_id=?", (p + v, str(uid)))
    conn.commit()

    update_title(uid)
    save_json()


def add_message(uid):
    p, m, t = get_user(uid)

    cursor.execute("UPDATE users SET messages=? WHERE user_id=?", (m + 1, str(uid)))
    conn.commit()

    save_json()

# ================= ADMIN MENU =================
def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 المستخدمين", callback_data="users")],
        [InlineKeyboardButton("💰 نقاط جماعية", callback_data="global_points")],
        [InlineKeyboardButton("🏷️ الألقاب", callback_data="titles")]
    ])

# ================= TRACK =================
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.message.from_user.id
    name = update.message.from_user.first_name
    text = update.message.text.strip()

    get_user(uid, name)
    add_message(uid)

    # ===== سوال =====
    if text in ["سوال", "سؤال"]:
        qst, ans = random.choice(QUESTIONS)
        active_q[uid] = ans
        await update.message.reply_text(f"❓ {qst}")
        return

    # ===== معلوماتي =====
    if text == "معلوماتي":
        p, m, title = get_user(uid)

        await update.message.reply_text(
            f"👤 الاسم: {name}\n"
            f"⭐ النقاط: {p}\n"
            f"📨 الرسائل: {m}\n"
            f"🏷️ اللقب: {title}"
        )
        return

    # ===== إجابة =====
    if uid in active_q:
        if text.lower() == active_q[uid].lower():
            add_points(uid, 1)
            del active_q[uid]
            await update.message.reply_text("🎉 صحيح +1 ⭐")

# ================= CALLBACKS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    if not is_admin(uid):
        return await q.answer("❌ غير مصرح", show_alert=True)

    # ===== USERS =====
    if data == "users":
        cursor.execute("SELECT user_id,name FROM users")
        rows = cursor.fetchall()

        keyboard = [
            [InlineKeyboardButton(r[1], callback_data=f"u_{r[0]}")]
            for r in rows
        ]

        await q.edit_message_text(
            "👤 اختر مستخدم:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ===== GLOBAL POINTS =====
    elif data == "global_points":
        state[uid] = {"mode": "global_points"}
        await q.edit_message_text("💰 ارسل النقاط الجماعية")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track))

    print("BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
