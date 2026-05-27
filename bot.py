import os
import random
from collections import defaultdict
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = os.getenv("GROUP_ID")

# ================= DATA =================
points = defaultdict(int)
messages = defaultdict(int)

active_question = {
    "chat": None,
    "answer": None
}

questions = [
    ("ما عاصمة العراق؟", "بغداد"),
    ("كم عدد الكواكب؟", "8"),
    ("ما أكبر قارة؟", "آسيا"),
    ("كم عدد أيام الأسبوع؟", "7"),
]

# ================= TITLE SYSTEM =================
def title(count):
    if count >= 1000:
        return "🔥 أسطورة"
    elif count >= 500:
        return "💎 خبير"
    elif count >= 250:
        return "🥇 محترف"
    elif count >= 100:
        return "🥈 نشط"
    elif count >= 50:
        return "🥉 مبتدئ"
    return "👶 جديد"

# ================= ADMIN CHECK =================
def is_admin(uid):
    return uid == ADMIN_ID

# ================= HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user = update.message.from_user
    uid = user.id
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    messages[uid] += 1

    # ===== USER =====
    if text == "نقاطي":
        await update.message.reply_text(
            f"⭐ نقاطك: {points[uid]}\n"
            f"📊 رسائل: {messages[uid]}\n"
            f"🏷️ لقب: {title(messages[uid])}"
        )
        return

    # ===== GROUP QUESTION =====
    if text == "سوال":

        if chat_type == "private":
            await update.message.reply_text("❌ استخدمه داخل المجموعة")
            return

        q, a = random.choice(questions)

        active_question["chat"] = chat_id
        active_question["answer"] = a

        await update.message.reply_text(f"❓ سؤال جماعي:\n{q}")
        return

    # ===== ANSWER SYSTEM =====
    if active_question["chat"] == chat_id and active_question["answer"]:

        if text.lower() == active_question["answer"].lower():

            points[uid] += 1

            active_question["chat"] = None
            active_question["answer"] = None

            await update.message.reply_text(
                f"🎉 صحيح!\n🏆 +1 نقطة"
            )
            return

        else:
            return

    # ===== ADMIN ONLY =====
    if is_admin(uid):

        # تعديل نقاط
        if text.startswith("تعديل"):
            try:
                _, target, value = text.split()
                target = int(target)
                value = int(value)

                old = points[target]
                points[target] = value

                await update.message.reply_text("✅ تم التعديل")

                if GROUP_ID:
                    await context.bot.send_message(
                        GROUP_ID,
                        f"🔔 تعديل إداري:\n"
                        f"👤 ID: {target}\n"
                        f"⭐ قبل: {old}\n"
                        f"⭐ بعد: {value}"
                    )

            except:
                await update.message.reply_text("❌ استخدم: تعديل ID رقم")
            return

        # إضافة نقاط
        if text.startswith("إضافة"):
            try:
                _, target, value = text.split()
                target = int(target)
                value = int(value)

                old = points[target]
                points[target] += value

                await update.message.reply_text("➕ تم الإضافة")

                if GROUP_ID:
                    await context.bot.send_message(
                        GROUP_ID,
                        f"➕ إضافة نقاط:\n"
                        f"👤 ID: {target}\n"
                        f"⭐ قبل: {old}\n"
                        f"⭐ بعد: {points[target]}"
                    )

            except:
                await update.message.reply_text("❌ استخدم: إضافة ID رقم")
            return


# ================= MAIN =================
def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
