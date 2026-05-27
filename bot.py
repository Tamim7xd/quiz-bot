import os
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ====== VARIABLES ======
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = os.getenv("GROUP_ID")

# ====== DATA (simple memory) ======
user_points = {}
user_messages = {}

questions = [
    ("ما عاصمة العراق؟", "بغداد"),
    ("كم عدد قارات العالم؟", "7"),
    ("ما هو أكبر كوكب؟", "المشتري"),
    ("كم عدد أيام الأسبوع؟", "7"),
]

active_question = {}

# ====== KEYBOARD ======
keyboard = ReplyKeyboardMarkup(
    [["نقاطي", "معلوماتي"], ["سوال"]],
    resize_keyboard=True
)

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 أهلاً بك في بوت المسابقات!", reply_markup=keyboard)

# ====== MESSAGE TRACKING ======
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    user_messages[user_id] = user_messages.get(user_id, 0) + 1

    text = update.message.text

    # Points command
    if text == "نقاطي":
        points = user_points.get(user_id, 0)
        await update.message.reply_text(f"⭐ نقاطك: {points}")
        return

    # Info command
    if text == "معلوماتي":
        msgs = user_messages.get(user_id, 0)
        points = user_points.get(user_id, 0)
        await update.message.reply_text(f"📊 الرسائل: {msgs}\n⭐ النقاط: {points}")
        return

    # Ask question
    if text == "سوال":
        q, a = random.choice(questions)
        active_question["q"] = q
        active_question["a"] = a
        await update.message.reply_text(f"❓ {q}")
        return

    # Answer check
    if "a" in active_question:
        if text.strip() == active_question["a"]:
            user_points[user_id] = user_points.get(user_id, 0) + 1
            await update.message.reply_text(f"🎉 إجابة صحيحة! تم إضافة نقطة لك")
            active_question.clear()
        else:
            await update.message.reply_text("❌ إجابة خاطئة")

# ====== MAIN ======
def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
