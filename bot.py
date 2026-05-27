import os
import json
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = os.getenv("GROUP_ID")

DATA_FILE = "data.json"

# ================= LOAD / SAVE =================
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"points": {}, "messages": {}, "active_question": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

# تحويل dict
def get_points(uid):
    return data["points"].get(str(uid), 0)

def set_points(uid, value):
    data["points"][str(uid)] = value
    save_data(data)

def add_points(uid, value):
    data["points"][str(uid)] = get_points(uid) + value
    save_data(data)

def get_messages(uid):
    return data["messages"].get(str(uid), 0)

def add_message(uid):
    data["messages"][str(uid)] = get_messages(uid) + 1
    save_data(data)

# ================= QUESTIONS =================
QUESTIONS = [
    ("ما عاصمة العراق؟", "بغداد"),
    ("ما أكبر دولة؟", "روسيا"),
    ("كم عدد الكواكب؟", "8"),
    ("ما أطول نهر؟", "النيل"),
]

# ================= ADMIN =================
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

    add_message(uid)

    # ================= QUESTION =================
    if text == "سؤال":
        q, a = random.choice(QUESTIONS)

        data["active_question"] = {
            "user": str(uid),
            "answer": a
        }
        save_data(data)

        return await update.message.reply_text(f"❓ {q}")

    # ================= ANSWER =================
    aq = data.get("active_question", {})

    if aq.get("user") == str(uid):

        if text.lower() == aq.get("answer", "").lower():

            add_points(uid, 1)

            data["active_question"] = {}
            save_data(data)

            return await update.message.reply_text("🎉 صحيح +1 نقطة")

        else:
            return await update.message.reply_text("❌ خطأ")

    # ================= USER INFO =================
    if text == "نقاطي":
        return await update.message.reply_text(
            f"⭐ نقاطك: {get_points(uid)}\n📊 رسائل: {get_messages(uid)}"
        )

    # ================= ADMIN =================
    if is_admin(uid):

        if text.startswith("تعديل"):
            try:
                _, target, value = text.split()
                target = int(target)
                value = int(value)

                old = get_points(target)
                set_points(target, value)

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

        if text.startswith("إضافة"):
            try:
                _, target, value = text.split()
                target = int(target)
                value = int(value)

                old = get_points(target)
                add_points(target, value)

                await update.message.reply_text("➕ تم الإضافة")

                if GROUP_ID:
                    await context.bot.send_message(
                        GROUP_ID,
                        f"➕ إضافة نقاط:\n"
                        f"👤 ID: {target}\n"
                        f"⭐ قبل: {old}\n"
                        f"⭐ بعد: {get_points(target)}"
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

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
