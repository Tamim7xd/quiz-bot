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

# ================= LOAD DATA =================
def load():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "points": {},
            "messages": {},
            "titles": {},
            "active_question": {},
            "users": {}
        }

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load()

# ================= HELPERS =================
def get_points(uid): return data["points"].get(str(uid), 0)
def set_points(uid, v): data["points"][str(uid)] = v; save()
def add_points(uid, v): set_points(uid, get_points(uid) + v)

def get_messages(uid): return data["messages"].get(str(uid), 0)
def add_message(uid):
    data["messages"][str(uid)] = get_messages(uid) + 1
    save()

def is_admin(uid): return uid == ADMIN_ID

def get_title(m):
    if m >= 1000: return "🔥 أسطورة"
    if m >= 500: return "💎 خبير"
    if m >= 250: return "🥇 محترف"
    if m >= 100: return "🥈 نشط"
    if m >= 50: return "🥉 مبتدئ"
    return "👶 جديد"

# ================= QUESTIONS =================
QUESTIONS = [
    ("ما عاصمة العراق؟", "بغداد"),
    ("كم عدد الكواكب؟", "8"),
    ("ما أكبر دولة؟", "روسيا"),
    ("ما أطول نهر؟", "النيل"),
    ("في أي قارة تقع مصر؟", "افريقيا"),
]

# ================= STATE =================
state = {}

# ================= HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user = update.message.from_user
    uid = user.id
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    # حفظ المستخدم
    data["users"][str(uid)] = user.first_name
    save()

    add_message(uid)

    # ================= USER INFO =================
    if text == "نقاطي":
        return await update.message.reply_text(
            f"⭐ نقاطك: {get_points(uid)}\n"
            f"📊 رسائل: {get_messages(uid)}\n"
            f"🏷️ لقب: {get_title(get_messages(uid))}"
        )

    # ================= QUESTION =================
    if text == "سوال":

        q, a = random.choice(QUESTIONS)

        data["active_question"] = {
            "chat": chat_id,
            "answer": a,
            "user": str(uid)
        }
        save()

        return await update.message.reply_text(f"❓ {q}")

    # ================= ANSWER =================
    aq = data.get("active_question", {})

    if aq.get("chat") == chat_id and aq.get("user") == str(uid):

        if text.lower() == aq.get("answer", "").lower():

            add_points(uid, 1)

            data["active_question"] = {}
            save()

            return await update.message.reply_text("🎉 صحيح +1 نقطة")

        else:
            return await update.message.reply_text("❌ خطأ")

    # ================= ADMIN PANEL =================
    if is_admin(uid):

        # فتح لوحة التحكم
        if text == "$تعديل":
            state[uid] = {"step": "search"}

            return await update.message.reply_text(
                "🔍 ابحث عن مستخدم (اسم أو ID)"
            )

        # البحث
        if uid in state and state[uid]["step"] == "search":

            q = text.lower()
            results = []

            for u, name in data["users"].items():
                if q in name.lower() or q in u:
                    results.append((u, name))

            if not results:
                return await update.message.reply_text("❌ لا يوجد نتائج")

            state[uid]["results"] = results
            state[uid]["step"] = "select"

            msg = "📋 النتائج:\n"
            for i, (u, n) in enumerate(results, 1):
                msg += f"{i}) {n} - {u}\n"

            return await update.message.reply_text(msg + "\n✏️ اختر رقم")

        # اختيار المستخدم
        if uid in state and state[uid]["step"] == "select":

            idx = int(text) - 1
            target = state[uid]["results"][idx][0]

            state[uid]["target"] = target
            state[uid]["step"] = "edit"

            return await update.message.reply_text(
                "✏️ اختر:\n1) تعديل نقاط\n2) إضافة نقاط"
            )

        # تنفيذ التعديل
        if uid in state and state[uid]["step"] == "edit":

            target = int(state[uid]["target"])

            if text == "1":
                state[uid]["mode"] = "set"
                return await update.message.reply_text("اكتب النقاط الجديدة:")

            if text == "2":
                state[uid]["mode"] = "add"
                return await update.message.reply_text("اكتب عدد النقاط:")

            if state[uid]["mode"] == "set":
                old = get_points(target)
                set_points(target, int(text))

                await update.message.reply_text("✅ تم التعديل")

                if GROUP_ID:
                    await context.bot.send_message(
                        GROUP_ID,
                        f"🔔 تعديل إداري:\n👤 {target}\n⭐ {old} → {text}"
                    )

                del state[uid]
                return

            if state[uid]["mode"] == "add":
                old = get_points(target)
                add_points(target, int(text))

                await update.message.reply_text("➕ تم الإضافة")

                if GROUP_ID:
                    await context.bot.send_message(
                        GROUP_ID,
                        f"➕ إضافة نقاط:\n👤 {target}\n⭐ {old} → {get_points(target)}"
                    )

                del state[uid]
                return


# ================= RUN =================
def main():
    if not BOT_TOKEN:
        print("BOT_TOKEN missing")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
