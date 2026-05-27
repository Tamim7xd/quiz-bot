import os
import random
import asyncio
from collections import defaultdict
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ================== DATA ==================
points = defaultdict(int)
xp = defaultdict(int)
messages = defaultdict(int)

active_question = {}

admin_state = {}

# ================== QUESTIONS ==================
questions = [
    ("ما عاصمة العراق؟", "بغداد"),
    ("كم عدد الكواكب؟", "8"),
    ("ما أكبر قارة؟", "آسيا"),
    ("كم عدد أيام الأسبوع؟", "7"),
    ("ما نتيجة 2+2؟", "4"),
]

# ================== KEYBOARDS ==================
user_kb = ReplyKeyboardMarkup(
    [["نقاطي", "معلوماتي"], ["سؤال"]],
    resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
    [
        ["سؤال مفاجئ", "عرض مستخدم"],
        ["تعديل نقاط", "إضافة نقاط"],
        ["Top 10", "إيقاف"]
    ],
    resize_keyboard=True
)

# ================== CHECK ADMIN ==================
def is_admin(uid):
    return uid == ADMIN_ID

# ================== HANDLER ==================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id
    text = update.message.text.strip()

    chat_type = update.effective_chat.type  # private / group

    # عداد رسائل
    messages[uid] += 1

    # ================= USER =================
    if text == "نقاطي":
        return await update.message.reply_text(
            f"⭐ النقاط: {points[uid]}\n✨ XP: {xp[uid]}"
        )

    if text == "معلوماتي":
        return await update.message.reply_text(
            f"📊 الرسائل: {messages[uid]}\n⭐ النقاط: {points[uid]}\n✨ XP: {xp[uid]}"
        )

    if text == "سؤال":
        q, a = random.choice(questions)
        active_question["answer"] = a
        return await update.message.reply_text(f"❓ {q}")

    # ================= ANSWER =================
    if "answer" in active_question:
        if text.lower() == active_question["answer"].lower():
            points[uid] += 1
            xp[uid] += 1
            active_question.clear()
            return await update.message.reply_text("🎉 صحيح +1 نقطة +1 XP")
        else:
            return await update.message.reply_text("❌ خطأ")

    # ================= ADMIN PANEL TRIGGER =================
    if text == "$تعديل":

        # ممنوع داخل المجموعة
        if chat_type != "private":
            return

        if is_admin(uid):
            return await update.message.reply_text(
                "👑 لوحة الأدمن:",
                reply_markup=admin_kb
            )
        else:
            return await update.message.reply_text("❌ ليس لديك صلاحية")

    # ================= ADMIN ACTIONS =================
    if is_admin(uid):

        if text == "سؤال مفاجئ":
            q, a = random.choice(questions)
            active_question["answer"] = a
            return await update.message.reply_text(f"🚨 سؤال مفاجئ:\n❓ {q}")

        if text == "Top 10":
            top = sorted(points.items(), key=lambda x: x[1], reverse=True)[:10]
            msg = "🏆 أفضل اللاعبين:\n"
            for i, (u, p) in enumerate(top, 1):
                msg += f"{i}- {u}: {p}\n"
            return await update.message.reply_text(msg)

        if text == "عرض مستخدم":
            admin_state[uid] = "view"
            return await update.message.reply_text("👤 أرسل ID المستخدم")

        if text == "تعديل نقاط":
            admin_state[uid] = "set"
            return await update.message.reply_text("✏️ أرسل: ID + نقاط")

        if text == "إضافة نقاط":
            admin_state[uid] = "add"
            return await update.message.reply_text("➕ أرسل: ID + نقاط")

        if text == "إيقاف":
            admin_state.clear()
            return await update.message.reply_text("⛔ تم إيقاف وضع الأدمن")

    # ================= ADMIN INPUT =================
    if is_admin(uid) and uid in admin_state:

        parts = text.split()

        try:
            target = int(parts[0])

            if admin_state[uid] == "set":
                points[target] = int(parts[1])
                admin_state.pop(uid)
                return await update.message.reply_text("✅ تم تعديل النقاط")

            if admin_state[uid] == "add":
                points[target] += int(parts[1])
                admin_state.pop(uid)
                return await update.message.reply_text("➕ تم الإضافة")

            if admin_state[uid] == "view":
                return await update.message.reply_text(
                    f"👤 ID: {target}\n⭐ نقاط: {points[target]}\n📊 رسائل: {messages[target]}\n✨ XP: {xp[target]}"
                )

        except:
            return await update.message.reply_text("❌ خطأ في الإدخال")

# ================== MAIN ==================
def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
