import os
import json
import random
import asyncio

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = os.getenv("GROUP_ID")

DATA_FILE = "data.json"

# ================= LOAD DATA =================
def load():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "points": {},
            "messages": {},
            "titles": {},
            "users": {},
            "active_question": {}
        }

def save():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load()

# ================= MEMORY =================
all_messages = []
state = {}

# ================= QUESTIONS =================
QUESTIONS = [
    ("ما عاصمة العراق؟", "بغداد"),
    ("ما أكبر دولة في العالم؟", "روسيا"),
    ("ما أطول نهر في العالم؟", "النيل"),
    ("كم عدد الكواكب؟", "8"),
    ("من أول نبي؟", "ادم"),
    ("في أي قارة تقع مصر؟", "افريقيا"),
    ("ما عاصمة فرنسا؟", "باريس"),
    ("كم عدد أيام الأسبوع؟", "7"),
]

# ================= HELPERS =================
def is_admin(uid):
    return uid == ADMIN_ID

def get_points(uid):
    return data["points"].get(str(uid), 0)

def set_points(uid, value):
    data["points"][str(uid)] = value
    save()

def add_points(uid, value):
    set_points(uid, get_points(uid) + value)

def get_messages(uid):
    return data["messages"].get(str(uid), 0)

def set_messages(uid, value):
    data["messages"][str(uid)] = value
    save()

def add_message(uid):
    data["messages"][str(uid)] = get_messages(uid) + 1
    save()

def get_title(msg):
    if msg >= 5000:
        return "👑 ملك الشلة"
    elif msg >= 1000:
        return "🔥 أسطورة"
    elif msg >= 500:
        return "💎 خبير"
    elif msg >= 250:
        return "🥇 محترف"
    elif msg >= 100:
        return "🥈 نشط"
    elif msg >= 50:
        return "🥉 مبتدئ"
    return "👶 جديد"

# ================= DELETE JOIN/LEAVE =================
async def delete_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.delete_message(
            update.effective_chat.id,
            update.message.message_id
        )
    except:
        pass

# ================= MAIN HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    user = update.message.from_user
    uid = user.id
    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    # حفظ الرسائل
    all_messages.append(update.message.message_id)

    # حفظ المستخدم
    data["users"][str(uid)] = user.first_name
    save()

    # زيادة الرسائل
    add_message(uid)

    # ================= معلوماتي =================
    if text == "نقاطي":

        title = get_title(get_messages(uid))

        return await update.message.reply_text(
            f"⭐ نقاطك: {get_points(uid)}\n"
            f"📨 رسائلك: {get_messages(uid)}\n"
            f"🏷️ لقبك: {title}"
        )

    # ================= سؤال =================
    if text == "سوال":

        q, a = random.choice(QUESTIONS)

        data["active_question"][str(uid)] = a
        save()

        return await update.message.reply_text(
            f"❓ سؤالك:\n{q}"
        )

    # ================= الإجابة =================
    if str(uid) in data["active_question"]:

        if text.lower() == data["active_question"][str(uid)].lower():

            add_points(uid, 1)

            del data["active_question"][str(uid)]
            save()

            return await update.message.reply_text(
                "🎉 إجابة صحيحة +1 نقطة"
            )

    # ================= لوحة الإدارة =================
    if is_admin(uid):

        # ===== فتح لوحة التعديل =====
        if text == "$تعديل":

            state[uid] = {"step": "search"}

            return await update.message.reply_text(
                "🔍 اكتب اسم أو ID المستخدم"
            )

        # ===== البحث =====
        if uid in state and state[uid]["step"] == "search":

            query = text.lower()
            results = []

            for u, name in data["users"].items():

                if query in name.lower() or query in u:
                    results.append((u, name))

            if not results:
                return await update.message.reply_text(
                    "❌ لا يوجد نتائج"
                )

            state[uid]["results"] = results
            state[uid]["step"] = "select"

            msg = "📋 النتائج:\n\n"

            for i, (u, n) in enumerate(results, 1):

                msg += (
                    f"{i}) {n}\n"
                    f"🆔 {u}\n"
                    f"⭐ {get_points(int(u))}\n"
                    f"📨 {get_messages(int(u))}\n\n"
                )

            msg += "✏️ اختر الرقم"

            return await update.message.reply_text(msg)

        # ===== اختيار المستخدم =====
        if uid in state and state[uid]["step"] == "select":

            try:
                idx = int(text) - 1

                target = int(
                    state[uid]["results"][idx][0]
                )

                state[uid]["target"] = target
                state[uid]["step"] = "edit"

                return await update.message.reply_text(
                    "⚙️ اختر:\n\n"
                    "1) تعديل النقاط\n"
                    "2) تعديل الرسائل\n"
                    "3) إضافة نقاط\n"
                    "4) إضافة رسائل"
                )

            except:
                return await update.message.reply_text(
                    "❌ اختيار غير صحيح"
                )

        # ===== خيارات التعديل =====
        if uid in state and state[uid]["step"] == "edit":

            target = state[uid]["target"]

            if text == "1":
                state[uid]["mode"] = "set_points"
                return await update.message.reply_text(
                    "⭐ اكتب النقاط الجديدة"
                )

            if text == "2":
                state[uid]["mode"] = "set_messages"
                return await update.message.reply_text(
                    "📨 اكتب عدد الرسائل الجديد"
                )

            if text == "3":
                state[uid]["mode"] = "add_points"
                return await update.message.reply_text(
                    "➕ اكتب عدد النقاط"
                )

            if text == "4":
                state[uid]["mode"] = "add_messages"
                return await update.message.reply_text(
                    "➕ اكتب عدد الرسائل"
                )

            # ===== تنفيذ التعديلات =====
            try:
                value = int(text)

                # تعديل نقاط
                if state[uid]["mode"] == "set_points":

                    old = get_points(target)

                    set_points(target, value)

                    await update.message.reply_text(
                        "✅ تم تعديل النقاط"
                    )

                    if GROUP_ID:
                        await context.bot.send_message(
                            GROUP_ID,
                            f"🔔 تعديل إداري\n"
                            f"👤 {target}\n"
                            f"⭐ {old} → {value}"
                        )

                # تعديل رسائل
                elif state[uid]["mode"] == "set_messages":

                    old = get_messages(target)

                    set_messages(target, value)

                    await update.message.reply_text(
                        "✅ تم تعديل الرسائل"
                    )

                    if GROUP_ID:
                        await context.bot.send_message(
                            GROUP_ID,
                            f"📨 تعديل الرسائل\n"
                            f"👤 {target}\n"
                            f"📊 {old} → {value}"
                        )

                # إضافة نقاط
                elif state[uid]["mode"] == "add_points":

                    old = get_points(target)

                    add_points(target, value)

                    await update.message.reply_text(
                        "➕ تم إضافة النقاط"
                    )

                    if GROUP_ID:
                        await context.bot.send_message(
                            GROUP_ID,
                            f"⭐ إضافة نقاط\n"
                            f"👤 {target}\n"
                            f"⭐ {old} → {get_points(target)}"
                        )

                # إضافة رسائل
                elif state[uid]["mode"] == "add_messages":

                    old = get_messages(target)

                    set_messages(
                        target,
                        old + value
                    )

                    await update.message.reply_text(
                        "➕ تم إضافة الرسائل"
                    )

                    if GROUP_ID:
                        await context.bot.send_message(
                            GROUP_ID,
                            f"📨 إضافة رسائل\n"
                            f"👤 {target}\n"
                            f"📊 {old} → {get_messages(target)}"
                        )

                del state[uid]

            except:
                return await update.message.reply_text(
                    "❌ اكتب رقم صحيح"
                )

        # ================= تنظيف كامل =================
        if text == "$تنظيف":

            msg = await update.message.reply_text(
                "🧹 بدء التنظيف..."
            )

            for i in range(5, -1, -1):

                await msg.edit_text(
                    f"🧹 تنظيف خلال {i}..."
                )

                await asyncio.sleep(1)

            await msg.edit_text(
                "⚠️ جارِ تنظيف جميع الرسائل..."
            )

            # حذف الرسائل
            for mid in reversed(all_messages):

                try:
                    await context.bot.delete_message(
                        chat_id,
                        mid
                    )

                    await asyncio.sleep(0.03)

                except:
                    pass

            # حذف رسالة التنظيف
            try:
                await context.bot.delete_message(
                    chat_id,
                    msg.message_id
                )
            except:
                pass

            # حذف رسالة الأمر
            try:
                await context.bot.delete_message(
                    chat_id,
                    update.message.message_id
                )
            except:
                pass

            return

# ================= MAIN =================
def main():

    if not BOT_TOKEN:
        print("BOT_TOKEN missing")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # الرسائل العادية
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle
        )
    )

    # حذف الدخول والخروج
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.ALL,
            delete_service
        )
    )

    print("BOT RUNNING...")
    app.run_polling()

# ================= START =================
if __name__ == "__main__":
    main()
