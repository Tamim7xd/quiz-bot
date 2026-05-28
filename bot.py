import os
import sqlite3
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================= ENV =================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

if not TOKEN:
    raise Exception("BOT_TOKEN is missing")

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    title TEXT DEFAULT '🌱 مبتدئ',
    title_locked INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS active_q (
    user_id INTEGER PRIMARY KEY,
    answer TEXT
)
""")

conn.commit()

# ================= QUESTIONS =================
QUESTIONS = [
("ما عاصمة العراق؟", "بغداد"),
("ما عاصمة السعودية؟", "الرياض"),
("ما عاصمة مصر؟", "القاهرة"),
("ما عاصمة فرنسا؟", "باريس"),
("ما عاصمة اليابان؟", "طوكيو"),
("ما عاصمة تركيا؟", "أنقرة"),
("ما عاصمة ألمانيا؟", "برلين"),
("ما عاصمة إيطاليا؟", "روما"),
("ما عاصمة روسيا؟", "موسكو"),
("ما عاصمة الصين؟", "بكين"),
("ما أكبر قارة في العالم؟", "آسيا"),
("ما أصغر قارة؟", "أستراليا"),
("ما أكبر محيط في العالم؟", "المحيط الهادئ"),
("ما أطول نهر في العالم؟", "النيل"),
("ما أعلى جبل في العالم؟", "إيفرست"),
("ما أكبر صحراء في العالم؟", "الصحراء الكبرى"),
("كم عدد قارات العالم؟", "7"),
("ما أكبر دولة في العالم مساحة؟", "روسيا"),
("ما أصغر دولة في العالم؟", "الفاتيكان"),
("ما الدولة التي تسمى بلد الشمس المشرقة؟", "اليابان"),
("ما الكوكب الأحمر؟", "المريخ"),
("ما أكبر كوكب في المجموعة الشمسية؟", "المشتري"),
("ما أصغر كوكب؟", "عطارد"),
("ما الغاز الذي نتنفسه؟", "الأكسجين"),
("كم عدد كواكب المجموعة الشمسية؟", "8"),
("ما مركز النظام الشمسي؟", "الشمس"),
("ما أقرب كوكب للشمس؟", "عطارد"),
("ما أبعد كوكب عن الشمس؟", "نبتون"),
("ما القمر التابع للأرض؟", "القمر"),
("ما شكل الأرض؟", "كروي"),
("من بنى الأهرامات؟", "الفراعنة"),
("من مكتشف الجاذبية؟", "نيوتن"),
("من أول إنسان صعد للقمر؟", "نيل أرمسترونغ"),
("من قائد معركة حطين؟", "صلاح الدين"),
("من أول خليفة راشد؟", "أبو بكر الصديق"),
("من اكتشف أمريكا؟", "كولومبوس"),
("في أي عام سقطت الأندلس؟", "1492"),
("ما أقدم حضارة؟", "حضارة وادي الرافدين"),
("أين تقع الأهرامات؟", "مصر"),
("من بنى سور الصين العظيم؟", "الصينيون"),
("من كتب البؤساء؟", "فيكتور هوغو"),
("من شاعر العرب الأكبر؟", "المتنبي"),
("من كتب شكسبير؟", "ويليام شكسبير"),
("ما لغة القرآن؟", "العربية"),
("من كتب كليلة ودمنة؟", "ابن المقفع"),
("ما اسم أول كتاب في الإسلام؟", "القرآن"),
("ما علم البلاغة؟", "علم الفصاحة"),
("ما علم النحو؟", "قواعد اللغة العربية"),
("من كتب ألف ليلة وليلة؟", "غير معروف"),
("ما أشهر رواية عربية؟", "موسم الهجرة إلى الشمال"),
("كم عدد الصلوات المفروضة؟", "5"),
("من أول نبي؟", "آدم"),
("من آخر الأنبياء؟", "محمد"),
("ما قبلة المسلمين؟", "الكعبة"),
("ما كتاب المسلمين؟", "القرآن"),
("ما شهر الصيام؟", "رمضان"),
("كم عدد سور القرآن؟", "114"),
("أين نزل الوحي؟", "غار حراء"),
("ما أول مسجد في الإسلام؟", "مسجد قباء"),
("من أول مؤذن في الإسلام؟", "بلال"),
("ما الحيوان الأسرع؟", "الفهد"),
("ما أكبر حيوان في العالم؟", "الحوت الأزرق"),
("ما الحيوان الذي يغير لونه؟", "الحرباء"),
("ما الحيوان الذي ينام واقفاً؟", "الحصان"),
("ما طائر لا يطير؟", "النعامة"),
("ما صوت الأسد؟", "زئير"),
("ما الحيوان الذي له 3 قلوب؟", "الأخطبوط"),
("ما أطول عمر حيوان؟", "السلحفاة"),
("ما الحيوان الذي يُلقب بسفينة الصحراء؟", "الجمل"),
("ما أذكى حيوان بحري؟", "الدلفين"),
("ما عملة العراق؟", "الدينار"),
("ما عملة السعودية؟", "الريال"),
("ما عملة أمريكا؟", "الدولار"),
("ما عملة أوروبا؟", "اليورو"),
("ما أكبر دولة عربية؟", "الجزائر"),
("ما أصغر دولة عربية؟", "البحرين"),
("ما عاصمة الإمارات؟", "أبوظبي"),
("ما عاصمة الأردن؟", "عمان"),
("ما عاصمة لبنان؟", "بيروت"),
("ما عاصمة المغرب؟", "الرباط"),
("ما أعلى قمة في العالم العربي؟", "جبل توبقال"),
("ما أطول نهر في العالم العربي؟", "النيل"),
("ما أكبر بحر مغلق؟", "بحر قزوين"),
("ما أكبر دولة إفريقية؟", "الجزائر"),
("ليش الدجاجة تعبر الشارع؟", "لتصل للجهة الثانية"),
("شنو الحيوان اللي يضحك؟", "الضبع"),
("ليش السمك ما يدرس؟", "لأنه يعيش بالمدرسة 😂"),
("شنو الشيء اللي يمشي بدون رجلين؟", "الوقت"),
("ليش الكمبيوتر يبرد؟", "لأنه عنده مروحة"),
("شنو الحيوان اللي ما ينام؟", "الدلفين"),
("ليش القمر ما يتعب؟", "لأنه يدور في الفضاء"),
("شنو الشيء اللي كلما أخذت منه كبر؟", "الحفرة"),
("ليش الكتاب حزين؟", "لأنه فيه صفحات كثيرة"),
("شنو الشيء اللي له عين وما يشوف؟", "الإبرة"),
("شنو الشيء اللي يمشي بلا رجل؟", "الساعة"),
("ليش التفاح يضحك؟", "لأنه وقع من الشجرة 😂"),
("شنو الشيء اللي يكبر كلما نقص؟", "العمر"),
("ليش القلم ذكي؟", "لأنه يكتب أفكارك"),
("شنو الشيء اللي إذا دخل الماء ما يبتل؟", "الضوء"),
("ليش السماء زرقاء؟", "سؤال علمي 😂"),
("شنو الشيء اللي ما له بداية ولا نهاية؟", "الدائرة"),
("ليش الثلاجة باردة؟", "حتى تحفظ الأكل"),
("شنو الحيوان اللي يحب الرياضة؟", "حصان السباق"),
("ليش القطة ذكية؟", "لأنها تموء فقط 😺"),
("شنو الشيء اللي كلما أخذت منه نقص؟", "الحفرة"),
("ليش السيارة تمشي؟", "لأن عندها عجلات"),
("شنو الشيء اللي يطير بدون جناح؟", "الدخان"),
("ليش الماء ما يتكلم؟", "لأنه ساكت 😄"),
("شنو الشيء اللي ما يتبل؟", "الظل"),
("ليش القلم يكتب؟", "لأنه فيه حبر"),
("شنو الشيء اللي إذا شرب مات؟", "النار"),
("ليش الحاسبة ما تغلط؟", "لأنها آلة"),
("شنو الشيء اللي يشوفك وما تشوفه؟", "الكاميرا"),
("ليش الباب يفتح؟", "عشان يدخل الناس"),
("شنو الحيوان اللي يحب النوم؟", "القط"),
("ليش الهاتف ذكي؟", "لأنه فيه تطبيقات"),
("شنو الشيء اللي يكبر ويصغر بدون حركة؟", "العمر"),
("ليش الشمس حارة؟", "لأنها نجم"),
("شنو الشيء اللي يمشي بلا توقف؟", "الزمن"),
("ليش الإنسان يضحك؟", "لأنه فرحان"),
("شنو الشيء اللي له أسنان وما يعض؟", "المشط"),
("ليش البحر مالح؟", "سؤال قديم 😂"),
("شنو الشيء اللي يسمع بدون أذن؟", "الميكروفون"),
("ليش القمر أبيض؟", "يعكس ضوء الشمس"),
("شنو الشيء اللي يطير بلا جناح؟", "الوقت"),
("ليش الطاولة ثابتة؟", "لأنها ما تمشي"),
("شنو الشيء اللي يكسر بدون ما ينكسر؟", "الوعد"),
("ليش الجدار ما يمشي؟", "لأنه ثابت"),
("شنو الشيء اللي ما له صوت لكنه موجود؟", "الظل"),
("ليش الكتاب ثقيل؟", "لأنه مليان معلومات"),
("شنو الشيء اللي إذا شفته اختفى؟", "الظلام"),
("ليش العيون تبكي؟", "عاطفة"),
("شنو الشيء اللي يفتح بدون مفتاح؟", "العقل"),
("ليش الإنسان ينام؟", "للراحة 😴"),
("شنو الشيء اللي يمشي ويوقف بدون رجل؟", "الساعة"),
("ليش الرياح تهب؟", "تغير ضغط الهواء"),
("شنو الشيء اللي يكتب بدون يد؟", "الكمبيوتر"),
("ليش الأرض تدور؟", "لأنها كوكب"),
("شنو الشيء اللي يبرد ويشغل العالم؟", "التكييف"),
("ليش الورقة تطير؟", "خفيفة"),
("شنو الشيء اللي يكبر إذا صرخت عليه؟", "الصدى"),
("ليش البحر يتحرك؟", "الأمواج"),
("شنو الشيء اللي ما له ظل؟", "الضوء"),
("ليش القطار يمشي؟", "على السكة")
("شي إذا أخذت منه يكبر؟", "الحفرة"),
("شي يمشي بدون رجلين؟", "الساعة"),
("شي كلما أخذت منه نقص؟", "العمر"),
("شي إذا شرب مات؟", "النار"),
("شي له أسنان وما يعض؟", "المشط"),
("شي ما له صوت لكنه يسمعك؟", "الصدى"),
("شي إذا دخل الماء ما يبتل؟", "الضوء"),
("شي يطير بلا جناح؟", "الدخان"),
("شي كلما كبر صغر؟", "العمر"),
("شي إذا كسرته ما ينكسر؟", "الوعد"),
("شي يضحك بدون فم؟", "الوجه المرسوم"),
("شي يمشي ويقف بدون أرجل؟", "الساعة"),
("شي ما له بداية ولا نهاية؟", "الدائرة"),
("شي ما له قلب لكنه يعيش؟", "الساعة"),
("شي إذا فتحته ما ينغلق؟", "الكتاب"),
("شي إذا ضربته يرد عليك؟", "الكرة"),
("شي ما يتكلم لكن يفهمك؟", "العين"),
("شي إذا شفته اختفى؟", "الظلام"),
("شي يبرد العالم كله؟", "التكييف"),
("شي يكتب بدون يد؟", "الكمبيوتر"),
("شي إذا صرخت عليه يكبر؟", "الصدى"),
("شي إذا وقف ما يمشي؟", "الإنسان"),
("شي يمشي بلا توقف؟", "الزمن"),
("شي يطير بدون جناح؟", "الوقت"),
("شي ما له رجلين لكنه يجري؟", "الماء"),
("شي يفتح بدون مفتاح؟", "العقل"),
("شي له عين وما يشوف؟", "الإبرة"),
("شي إذا فقدته صعب يرجع؟", "الوقت"),
("شي ما له ظل؟", "الضوء"),
("شي يضحك إذا ضربته؟", "البالون"),
("شي يختفي إذا بحثت عنه؟", "النوم"),
("شي كل الناس عندهم واحد؟", "الاسم"),
("شي يكبر بدون أكل؟", "العمر"),
("شي يمشي على الجدران؟", "الظل"),
("شي يكتب لك بدون ورق؟", "الهاتف"),
("شي إذا فتحته طلع سر؟", "العقل"),
("شي ما له وزن لكنه يطير؟", "الفكرة"),
("شي إذا طاح ما ينكسر؟", "الظل"),
("شي يبردك في الصيف؟", "الهواء"),
("شي إذا لمسته يختفي؟", "الصابون"),
("شي ما له باب لكنه بيت؟", "بيت العنكبوت"),
("شي يضحكك بدون كلام؟", "النكتة"),
("شي إذا شفته تنسى كل شيء؟", "الصدمة"),
("شي ما له شكل لكنه موجود؟", "الخيال"),
("شي كلما أخذت منه زاد؟", "العلم"),
("شي إذا تحرك ما يوقف؟", "الوقت"),
("شي يركض بدون أرجل؟", "النهر"),
("شي إذا كبر صغر مكانه؟", "الحفرة"),
("شي يسمعك بدون أذن؟", "الميكروفون"),
("شي يفتح كل الأبواب؟", "المفتاح"),
("شي إذا كتبته اختفى؟", "القلم"),
("شي يضحك لما يقع؟", "الإنسان"),
("شي ما ينام أبداً؟", "القلب"),
("شي إذا شفته تحس بالبرد؟", "الثلج"),
("شي إذا دخلته خرجت منه أقوى؟", "التجربة"),
("شي ما له بداية لكن له نهاية؟", "الطريق"),
("شي إذا مسكته طار؟", "الصابون"),
("شي يختفي في النهار؟", "النجوم"),
("شي إذا ضربته يكبر؟", "البالون"),
("شي ما له صوت لكن يخوف؟", "الظلام"),
("شي يمشي في الليل فقط؟", "القط"),
("شي إذا شفته في المرآة يختفي؟", "أنت"),
("شي ما له شكل لكن يملأ المكان؟", "الهواء"),
("شي إذا فتحته يضحكك؟", "الهاتف"),
("شي يركض بدون توقف؟", "الزمن"),
("شي إذا طاح لا يتألم؟", "الكرة"),
("شي يطير لكن ليس طير؟", "الدخان"),
("شي إذا لمسته يختفي؟", "الفقاعة"),
("شي يكتب بدون حبر؟", "الكمبيوتر"),
("شي إذا فقدته ما يرجع؟", "الوقت"),

]

def get_question():
    return random.choice(QUESTIONS)

# ================= TITLES (POINT BASED) =================
def get_title(points):

    if points < 150:
        return "🌱 مبتدئ"

    level = (points - 150) // 200

    titles = [
        "🌿 متعلم",
        "⚡ نشيط",
        "🔥 متفاعل",
        "🚀 متقدم",
        "🎯 محترف",
        "⭐ مميز",
        "🏅 بطل",
        "🥇 نجم",
        "👑 قائد",
        "💎 خبير",
        "🏆 أسطورة",
        "⚔️ محارب",
        "🛡️ حارس",
        "🌟 سوبر ستار",
        "💥 خارق",
        "🎮 لاعب محترف",
        "🧩 محلل",
        "📚 مثقف",
        "🌍 رحّالة",
        "💠 أسطورة عليا"
    ]

    if level < len(titles):
        return titles[level]

    return "👑 ملك الأساطير"

# ================= ADMIN MEMORY =================
admin_state = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id == ADMIN_ID:

        keyboard = [
            [InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="admin_panel")]
        ]

        await update.message.reply_text(
            "🔥 أهلاً أدمن",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text("👋 أهلاً بك في البوت")

# ================= ADMIN PANEL =================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton("👥 الأعضاء", callback_data="users")]
    ]

    await q.message.reply_text(
        "🛠 لوحة الأدمن",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= USERS =================
async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    c.execute("SELECT user_id,name,title FROM users LIMIT 30")
    users = c.fetchall()

    keyboard = []

    for u in users:
        uid, name, title = u

        icon = "👑" if uid == ADMIN_ID else "🟢"

        keyboard.append([
            InlineKeyboardButton(f"{icon} {name}", callback_data=f"user_{uid}")
        ])

    await q.message.reply_text(
        "👥 قائمة الأعضاء:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= USER MENU =================
async def user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    keyboard = [
        [InlineKeyboardButton("📊 معلومات العضو", callback_data=f"info_{uid}")],
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data=f"addp_{uid}")],
        [InlineKeyboardButton("✏️ تعديل لقب", callback_data=f"title_{uid}")],
        [InlineKeyboardButton("🔓 إرجاع تلقائي", callback_data=f"unlock_{uid}")]
    ]

    await q.message.reply_text(
        "⚙️ إدارة العضو:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= INFO =================
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("SELECT name,points,title FROM users WHERE user_id=?", (uid,))
    row = c.fetchone()

    if row:
        name, points, title = row

        await q.message.reply_text(
            f"""👤 معلومات العضو

🧑 الاسم: {name}
💰 النقاط: {points}
🏅 اللقب: {title}
"""
        )

# ================= ADMIN STATE =================
admin_state = {}

# ================= ADD POINTS =================
async def add_points(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    admin_state[ADMIN_ID] = ("points", uid)

    await q.message.reply_text("💰 ارسل عدد النقاط")

# ================= SET TITLE =================
async def set_title(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    admin_state[ADMIN_ID] = ("title", uid)

    await q.message.reply_text("🏅 ارسل اللقب الجديد")

# ================= UNLOCK TITLE =================
async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    c.execute("UPDATE users SET title_locked=0 WHERE user_id=?", (uid,))
    conn.commit()

    await q.message.reply_text("🔓 تم تفعيل النظام التلقائي")

# ================= HANDLE =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    text = update.message.text.strip()
    name = update.effective_user.first_name

    # ================= ADMIN ACTION =================
    if uid == ADMIN_ID and ADMIN_ID in admin_state:

        action, target = admin_state[ADMIN_ID]

        if action == "points":

            try:
                amount = int(text)

                c.execute("SELECT points FROM users WHERE user_id=?", (target,))
                row = c.fetchone()

                if row:
                    new_points = row[0] + amount

                    c.execute(
                        "UPDATE users SET points=? WHERE user_id=?",
                        (new_points, target)
                    )

                    conn.commit()

                await update.message.reply_text("✅ تم إضافة النقاط")

            except:
                await update.message.reply_text("❌ خطأ")

            admin_state.pop(ADMIN_ID)
            return

        if action == "title":

            c.execute(
                "UPDATE users SET title=?, title_locked=1 WHERE user_id=?",
                (text, target)
            )

            conn.commit()

            await update.message.reply_text("🏅 تم تثبيت اللقب")

            admin_state.pop(ADMIN_ID)
            return

    # ================= REGISTER =================
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():

        c.execute(
            "INSERT INTO users VALUES (?,?,0,0,'🌱 مبتدئ',0)",
            (uid, name)
        )

        conn.commit()

    # ================= INFO =================
    if text == "معلوماتي":

        c.execute("SELECT points,messages,title FROM users WHERE user_id=?", (uid,))
        p, m, title = c.fetchone()

        await update.message.reply_text(
            f"""✨ ─── معلوماتك ─── ✨

👤 الاسم: {name}
💬 الرسائل: {m}
💰 النقاط: {p}
🏅 اللقب: {title}
"""
        )
        return

    # ================= QUESTION =================
    if text in ["سؤال", "سوال"]:

        q, a = get_question()

        c.execute("REPLACE INTO active_q VALUES (?,?)", (uid, a))
        conn.commit()

        await update.message.reply_text(f"❓ {q}")
        return

    # ================= ANSWER =================
    c.execute("SELECT answer FROM active_q WHERE user_id=?", (uid,))
    active = c.fetchone()

    if active:

        correct = active[0]

        if text.lower() == correct.lower():
            add = 5
            await update.message.reply_text("✅ صحيح +5 نقاط")
        else:
            add = 0
            await update.message.reply_text(f"❌ خطأ\nالإجابة: {correct}")

        c.execute("DELETE FROM active_q WHERE user_id=?", (uid,))
        conn.commit()

    else:
        add = 1

    # ================= UPDATE =================
    c.execute("SELECT points,messages,title_locked FROM users WHERE user_id=?", (uid,))
    p, m, locked = c.fetchone()

    old_title = get_title(p)

    p += add
    m += 1

    if locked == 0:
        new_title = get_title(p)
    else:
        new_title = old_title

    c.execute(
        "UPDATE users SET points=?,messages=?,title=? WHERE user_id=?",
        (p, m, new_title, uid)
    )

    conn.commit()

    # ================= ANNOUNCEMENT =================
    if locked == 0 and new_title != old_title:

        await update.message.reply_text(
            f"🎉 مبروك! حصلت على لقب: {new_title}"
        )

        if GROUP_ID:
            try:
                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=f"""
🎊 ترقية جديدة 🎊

👤 {name}
🏅 {new_title}

🔥 مبروك الترقية!
"""
                )
            except:
                pass

# ================= ROUTER =================
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    data = q.data

    if data == "admin_panel":
        await panel(update, context)

    elif data == "users":
        await show_users(update, context)

    elif data.startswith("user_"):
        await user_menu(update, context)

    elif data.startswith("info_"):
        await user_info(update, context)

    elif data.startswith("addp_"):
        await add_points(update, context)

    elif data.startswith("title_"):
        await set_title(update, context)

    elif data.startswith("unlock_"):
        await unlock(update, context)

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🚀 BOT FULL POINT SYSTEM RUNNING")
app.run_polling()
