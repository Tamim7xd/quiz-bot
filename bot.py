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

# ================= QUESTIONS =================
questions = [
    ("ما عاصمة العراق؟", "بغداد"),
    ("كم عدد الكواكب في المجموعة الشمسية؟", "8"),
    ("ما أكبر قارة؟", "آسيا"),
    ("كم عدد أيام الأسبوع؟", "7"),
    ("ما نتيجة 2+2؟", "4"),
]

# ================= TITLES =================
def title(msg_count):
    if msg_count >= 5000:
        return "👑 واحد عراق"
    elif msg_count >= 1000:
        return "🔥 أسطورة"
    elif msg_count >= 500:
        return "💎 خبير"
    elif msg_count >= 250:
        return "🥇 محترف"
    elif msg_count >= 100:
        return "🥈 نشط"
    elif msg_count >= 50:
        return "🥉 مبتدئ"
    return "👶 جديد"

# ================= ADMIN CHECK =================
def is_admin(uid):
    return uid == ADMIN_ID

# ================= HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.message.from_user
    uid = user.id
    text = update.message.text.strip()
    chat_type = update.effective_chat.type

    # عداد رسائل
    messages[uid] += 1

    # ================= USER COMMANDS =================
    if text == "نقاطي":
        return await update.message.reply_text(
            f"⭐ نقاطك: {points[uid]}\n📊 رسائل: {messages[uid]}\n🏷️ لقب: {title(messages[uid])}"
        )

    if text == "معلوماتي":
        return await update.message.reply_text(
            f"📊 الرسائل: {messages[uid]}\n⭐ النقاط: {points[uid]}\n🏷️ اللقب: {title(messages[uid])}"
        )

    # ================= GROUP QUIZ =================
    if text == "سوال":

        if chat_type == "private":
            return await update.message.reply_text("❌ استخدمه داخل المجموعة")

        q, a = random.choice(questions)

        active_question["answer"] = a
        active_question["chat"] = update.effective_chat.id

        return await update.message.reply_text(f"❓ سؤال جماعي:\n{q}")

    # ================= ANSWER SYSTEM =================
    if active_question.get("chat") == update.effective_chat.id:

        if text.lower() == active_question["answer"].lower():

            points[uid] += 1
            active_question["chat"] = None
            active_question["answer"] = None

            return await update.message.reply_text(
                f"🎉 صحيح!\n🏆 {user.first_name} حصل على نقطة"
            )

        elif active_question["answer"] is not None:
            return await update.message.reply_text("❌ خطأ")

    # ================= ADMIN PANEL =================
    if is_admin(uid):

        # ===== تعديل نقاط =====
        if text.startswith("تعديل"):
            try:
                _, target, value = text.split()
                target = int(target)
                value = int(value)

                old = points[target]
                points[target] = value

                await update.message.reply_text("✅ تم تعديل النقاط")

                await context.bot.send_message(
                    GROUP_ID,
                    f"🔔 تحديث إداري:\n"
                    f"👤 المستخدم: {target}\n"
                    f"⭐ قبل: {old}\n"
                    f"⭐ بعد: {value}"
                )

            except:
                await update.message.reply_text("❌ استخدم: تعديل ID عدد")
            return

        # ===== إضافة نقاط =====
        if text.startswith("إضافة"):
            try:
                _, target, value = text.split()
                target = int(target)
                value = int(value)

                old = points[target]
                points[target] += value

                await update.message.reply_text("➕ تم إضافة النقاط")

                await context.bot.send_message(
                    GROUP_ID,
                    f"➕ إضافة نقاط:\n"
                    f"👤 المستخدم: {target}\n"
                    f"⭐ قبل: {old}\n"
                    f"⭐ بعد: {points[target]}"
                )

            except:
                await update.message.reply_text("❌ استخدم: إضافة ID عدد")
            return

        # ===== سؤال مفاجئ في المجموعة =====
        if text == "سؤال مفاجئ":

            if chat_type == "private":
                return await update.message.reply_text("❌ فقط داخل المجموعة")

            q, a = random.choice(questions)

            active_question["answer"] = a
            active_question["chat"] = update.effective_chat.id

            return await update.message.reply_text(f"🚨 سؤال مفاجئ:\n❓ {q}")

# ================= MAIN =================
def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()                old = points[target]
                points[target] = value

                await update.message.reply_text("✅ تم تعديل النقاط")

                await context.bot.send_message(
                    GROUP_ID,
                    f"🔔 تحديث إداري:\n"
                    f"👤 المستخدم: {target}\n"
                    f"⭐ قبل: {old}\n"
                    f"⭐ بعد: {value}"
                )

            except:
                await update.message.reply_text("❌ استخدم: تعديل ID عدد")
            return

        # ===== إضافة نقاط =====
        if text.startswith("إضافة"):
            try:
                _, target, value = text.split()
                target = int(target)
                value = int(value)

                old = points[target]
                points[target] += value

                await update.message.reply_text("➕ تم إضافة النقاط")

                await context.bot.send_message(
                    GROUP_ID,
                    f"➕ إضافة نقاط:\n"
                    f"👤 المستخدم: {target}\n"
                    f"⭐ قبل: {old}\n"
                    f"⭐ بعد: {points[target]}"
                )

            except:
                await update.message.reply_text("❌ استخدم: إضافة ID عدد")
            return

        # ===== سؤال مفاجئ في المجموعة =====
        if text == "سؤال مفاجئ":

            if chat_type == "private":
                return await update.message.reply_text("❌ فقط داخل المجموعة")

            q, a = random.choice(questions)

            active_question["answer"] = a
            active_question["chat"] = update.effective_chat.id

            return await update.message.reply_text(f"🚨 سؤال مفاجئ:\n❓ {q}")

# ================= MAIN =================
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
