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
("ما عاصمة ألمانيا؟", "برلين"),
("ما عاصمة إيطاليا؟", "روما"),
("ما عاصمة تركيا؟", "أنقرة"),
("ما عاصمة روسيا؟", "موسكو"),
("ما عاصمة الصين؟", "بكين"),

("ما أكبر قارة في العالم؟", "آسيا"),
("ما أصغر قارة؟", "أستراليا"),
("ما أكبر محيط؟", "المحيط الهادئ"),
("ما أطول نهر؟", "النيل"),
("ما أعلى جبل؟", "إيفرست"),
("ما أكبر دولة مساحة؟", "روسيا"),
("ما أصغر دولة؟", "الفاتيكان"),
("كم عدد قارات العالم؟", "7"),
("ما أكبر بحر مغلق؟", "بحر قزوين"),
("ما الدولة التي تسمى بلد الشمس المشرقة؟", "اليابان"),

("ما عملة العراق؟", "الدينار"),
("ما عملة السعودية؟", "الريال"),
("ما عملة أمريكا؟", "الدولار"),
("ما عملة أوروبا؟", "اليورو"),
("ما عملة اليابان؟", "الين"),

("ما أكبر دولة عربية؟", "الجزائر"),
("ما أصغر دولة عربية؟", "البحرين"),
("ما عاصمة الإمارات؟", "أبوظبي"),
("ما عاصمة الأردن؟", "عمان"),
("ما عاصمة لبنان؟", "بيروت"),

("ما أعلى قمة في العالم؟", "إيفرست"),
("ما أكبر صحراء في العالم؟", "الصحراء الكبرى"),
("ما أقرب كوكب للشمس؟", "عطارد"),
("ما أبعد كوكب؟", "نبتون"),
("ما أكبر كوكب؟", "المشتري"),

("ما القمر التابع للأرض؟", "القمر"),
("ما مركز النظام الشمسي؟", "الشمس"),
("ما لون السماء؟", "أزرق"),
("ما غاز التنفس؟", "الأكسجين"),
("ما رمز الماء؟", "H2O"),

("من أول إنسان صعد للقمر؟", "نيل أرمسترونغ"),
("من مكتشف الجاذبية؟", "نيوتن"),
("من بنى الأهرامات؟", "الفراعنة"),
("من قائد معركة حطين؟", "صلاح الدين"),
("من أول نبي؟", "آدم"),

("ما كتاب المسلمين؟", "القرآن"),
("ما قبلة المسلمين؟", "الكعبة"),
("ما شهر الصيام؟", "رمضان"),
("كم عدد الصلوات؟", "5"),
("كم عدد سور القرآن؟", "114"),

("ما الحيوان الأسرع؟", "الفهد"),
("ما أكبر حيوان؟", "الحوت الأزرق"),
("ما الحيوان الذي يغير لونه؟", "الحرباء"),
("ما الحيوان الذي ينام واقفاً؟", "الحصان"),
("ما طائر لا يطير؟", "النعامة"),

("ما صوت الأسد؟", "زئير"),
("ما الحيوان الذي له 3 قلوب؟", "الأخطبوط"),
("ما أذكى حيوان بحري؟", "الدلفين"),
("ما الحيوان الذي يُسمى سفينة الصحراء؟", "الجمل"),
("ما الحيوان الذي يعيش في الصحراء؟", "الجمل"),

("ما أطول نهر في العالم؟", "النيل"),
("ما أطول نهر في العراق؟", "دجلة"),
("ما عاصمة المغرب؟", "الرباط"),
("ما عاصمة تونس؟", "تونس"),
("ما عاصمة ليبيا؟", "طرابلس"),

("ما أكبر قارة؟", "آسيا"),
("ما أصغر قارة؟", "أستراليا"),
("ما أكبر دولة في إفريقيا؟", "الجزائر"),
("ما أكبر دولة في أوروبا؟", "روسيا"),
("ما أصغر دولة في العالم؟", "الفاتيكان"),

("ما لغة القرآن؟", "العربية"),
("من كتب شكسبير؟", "ويليام شكسبير"),
("من كتب البؤساء؟", "فيكتور هوغو"),
("من شاعر العرب الأكبر؟", "المتنبي"),
("من كتب كليلة ودمنة؟", "ابن المقفع"),

("ما أول مسجد في الإسلام؟", "مسجد قباء"),
("من أول مؤذن؟", "بلال"),
("ما أول كتاب في الإسلام؟", "القرآن"),
("ما أعلى جبل في العالم العربي؟", "جبل توبقال"),
("ما أطول نهر عربي؟", "النيل"),

("ما عاصمة العراق؟", "بغداد"),
("ما عاصمة السعودية؟", "الرياض"),
("ما عاصمة مصر؟", "القاهرة"),
("ما عاصمة فرنسا؟", "باريس"),
("ما عاصمة اليابان؟", "طوكيو"),
("ما عاصمة ألمانيا؟", "برلين"),
("ما عاصمة إيطاليا؟", "روما"),
("ما عاصمة تركيا؟", "أنقرة"),
("ما عاصمة روسيا؟", "موسكو"),
("ما عاصمة الصين؟", "بكين"),

("ما أكبر قارة في العالم؟", "آسيا"),
("ما أصغر قارة؟", "أستراليا"),
("ما أكبر محيط؟", "المحيط الهادئ"),
("ما أطول نهر؟", "النيل"),
("ما أعلى جبل؟", "إيفرست"),
("ما أكبر دولة مساحة؟", "روسيا"),
("ما أصغر دولة؟", "الفاتيكان"),
("كم عدد قارات العالم؟", "7"),
("ما أكبر بحر مغلق؟", "بحر قزوين"),
("ما الدولة التي تسمى بلد الشمس المشرقة؟", "اليابان"),

("ما عملة العراق؟", "الدينار"),
("ما عملة السعودية؟", "الريال"),
("ما عملة أمريكا؟", "الدولار"),
("ما عملة أوروبا؟", "اليورو"),
("ما عملة اليابان؟", "الين"),

("ما أكبر دولة عربية؟", "الجزائر"),
("ما أصغر دولة عربية؟", "البحرين"),
("ما عاصمة الإمارات؟", "أبوظبي"),
("ما عاصمة الأردن؟", "عمان"),
("ما عاصمة لبنان؟", "بيروت"),

("ما أعلى قمة في العالم؟", "إيفرست"),
("ما أكبر صحراء في العالم؟", "الصحراء الكبرى"),
("ما أقرب كوكب للشمس؟", "عطارد"),
("ما أبعد كوكب؟", "نبتون"),
("ما أكبر كوكب؟", "المشتري"),

("ما القمر التابع للأرض؟", "القمر"),
("ما مركز النظام الشمسي؟", "الشمس"),
("ما لون السماء؟", "أزرق"),
("ما غاز التنفس؟", "الأكسجين"),
("ما رمز الماء؟", "H2O"),

("من أول إنسان صعد للقمر؟", "نيل أرمسترونغ"),
("من مكتشف الجاذبية؟", "نيوتن"),
("من بنى الأهرامات؟", "الفراعنة"),
("من قائد معركة حطين؟", "صلاح الدين"),
("من أول نبي؟", "آدم"),

("ما كتاب المسلمين؟", "القرآن"),
("ما قبلة المسلمين؟", "الكعبة"),
("ما شهر الصيام؟", "رمضان"),
("كم عدد الصلوات؟", "5"),
("كم عدد سور القرآن؟", "114"),

("ما الحيوان الأسرع؟", "الفهد"),
("ما أكبر حيوان؟", "الحوت الأزرق"),
("ما الحيوان الذي يغير لونه؟", "الحرباء"),
("ما الحيوان الذي ينام واقفاً؟", "الحصان"),
("ما طائر لا يطير؟", "النعامة"),

("ما صوت الأسد؟", "زئير"),
("ما الحيوان الذي له 3 قلوب؟", "الأخطبوط"),
("ما أذكى حيوان بحري؟", "الدلفين"),
("ما الحيوان الذي يُسمى سفينة الصحراء؟", "الجمل"),
("ما الحيوان الذي يعيش في الصحراء؟", "الجمل"),

("ما أطول نهر في العالم؟", "النيل"),
("ما أطول نهر في العراق؟", "دجلة"),
("ما عاصمة المغرب؟", "الرباط"),
("ما عاصمة تونس؟", "تونس"),
("ما عاصمة ليبيا؟", "طرابلس"),

("ما أكبر قارة؟", "آسيا"),
("ما أصغر قارة؟", "أستراليا"),
("ما أكبر دولة في إفريقيا؟", "الجزائر"),
("ما أكبر دولة في أوروبا؟", "روسيا"),
("ما أصغر دولة في العالم؟", "الفاتيكان"),

("ما لغة القرآن؟", "العربية"),
("من كتب شكسبير؟", "ويليام شكسبير"),
("من كتب البؤساء؟", "فيكتور هوغو"),
("من شاعر العرب الأكبر؟", "المتنبي"),
("من كتب كليلة ودمنة؟", "ابن المقفع"),

("ما أول مسجد في الإسلام؟", "مسجد قباء"),
("من أول مؤذن؟", "بلال"),
("ما أول كتاب في الإسلام؟", "القرآن"),
("ما أعلى جبل في العالم العربي؟", "جبل توبقال"),
("ما أطول نهر عربي؟", "النيل"),

("ليش السمك ما يدرس؟", "لأنه يعيش بالمدرسة 😂"),
("ليش القمر ما ينام؟", "لأنه يدور 😂"),
("ليش الكمبيوتر يبرد؟", "لأنه عنده مروحة"),
("ليش التفاح يضحك؟", "لأنه وقع من الشجرة 😂"),
("شنو الشيء اللي يمشي بلا رجل؟", "الوقت"),
("ما هي أكبر دولة في العالم من حيث السكان؟", "الهند"),
("ما هي عاصمة كندا؟", "أوتاوا"),
("ما هي عاصمة أستراليا؟", "كانبرا"),
("ما هي عملة اليابان؟", "الين"),
("ما هو أطول نهر في إفريقيا؟", "النيل"),
("ما هو أصغر كوكب في النظام الشمسي؟", "عطارد"),
("ما هو أكبر كوكب في النظام الشمسي؟", "المشتري"),
("ما هي أسرع طائرة في العالم؟", "طائرة SR-71"),
("ما هو عدد أيام السنة الكبيسة؟", "366"),
("ما هو عدد شهور السنة؟", "12"),

("ما هي أطول سلسلة جبال في العالم؟", "الأنديز"),
("ما هي أكبر محيطات العالم؟", "المحيط الهادئ"),
("ما هي لغة البرازيل الرسمية؟", "البرتغالية"),
("ما هي عاصمة إسبانيا؟", "مدريد"),
("ما هي عاصمة إيطاليا؟", "روما"),
("ما هي عاصمة بريطانيا؟", "لندن"),
("ما هو أقرب كوكب للأرض؟", "الزهرة"),
("ما هو أكبر حيوان بري؟", "الفيل"),
("ما هو أسرع حيوان بري؟", "الفهد"),
("ما هو الحيوان الذي لا يشرب الماء؟", "الكنغر الجرابي (تقريباً)"),
("ما هو الحيوان الذي ينام أكثر شيء؟", "الكوالا"),
("ما هو عدد القارات؟", "7"),
("ما هي أكبر قارة؟", "آسيا"),
("ما هي أصغر قارة؟", "أستراليا"),
("ما هو البحر الذي يفصل بين إفريقيا وأوروبا؟", "البحر المتوسط"),
("ما هي عاصمة تونس؟", "تونس"),
("ما هي عاصمة ليبيا؟", "طرابلس"),
("ما هي عاصمة السودان؟", "الخرطوم"),
("ما هي عاصمة اليمن؟", "صنعاء"),
("ما هي عاصمة سوريا؟", "دمشق"),
("ما هي عاصمة فلسطين؟", "القدس"),
("ما هي عاصمة إيران؟", "طهران"),
("ما هي عاصمة الهند؟", "نيودلهي"),
("ما هي عاصمة الصين؟", "بكين"),
("ما هي عاصمة كوريا الجنوبية؟", "سول"),
("ما هي أكبر دولة في إفريقيا؟", "الجزائر"),
("ما هي أصغر دولة في العالم؟", "الفاتيكان"),
("ما هو الحيوان الذي يلقب بسفينة الصحراء؟", "الجمل"),
("ما هو الحيوان الذي يغير جلده؟", "الأفعى"),
("ما هو الطائر الذي لا يطير؟", "النعامة"),
("ما هو العضو المسؤول عن ضخ الدم؟", "القلب"),
("ما هو أكبر عضو في جسم الإنسان؟", "الجلد"),
("ما هو عدد أسنان الإنسان البالغ؟", "32"),
("ما هو الغاز الذي نتنفسه؟", "الأكسجين"),
("ما هو الغاز الأكثر وجوداً في الهواء؟", "النيتروجين"),
("ما هو علم دراسة الفلك؟", "علم الفضاء"),
("ما هو علم الأحياء؟", "دراسة الكائنات الحية"),
("ما هو علم الفيزياء؟", "دراسة المادة والطاقة"),
("ما هو أول مسجد في الإسلام؟", "مسجد قباء"),
("ما هي أول غزوة في الإسلام؟", "غزوة بدر"),
("ما هو شهر رمضان؟", "شهر الصيام"),
("ما هي القبلة؟", "الكعبة"),
("كم عدد الصلوات المفروضة؟", "5"),
("ما هي ليلة القدر؟", "ليلة خير من ألف شهر"),
("ما هو القرآن؟", "كتاب الله"),
("من هو أول إنسان؟", "آدم"),
("من هو خاتم الأنبياء؟", "محمد"),
("ما هي معركة بدر؟", "أول معركة في الإسلام"),
("ما هي معركة أحد؟", "معركة بين المسلمين وقريش"),
("ما هي الدولة التي اخترعت الإنترنت؟", "أمريكا"),
("ما هو أكبر بحر في العالم؟", "بحر الفلبين"),
("ما هو أطول جسر في العالم؟", "جسر دانيانغ"),
("ما هو أسرع قطار في العالم؟", "شنغهاي ماجليف"),
("ما هو أكبر سد في العالم؟", "سد الخوانق الثلاثة"),
("ما هي أكبر جزيرة في العالم؟", "جرينلاند"),
("ما هي أكبر صحراء؟", "الصحراء الكبرى"),
("ما هو الحيوان الذي لا ينام؟", "الدلفين"),
("ما هو الحيوان الذي يعيش في الماء والبر؟", "الضفدع"),
("ما هو الحيوان الذي يضحك؟", "الضبع"),
("ما هو الحيوان الذي يموت إذا فتح فمه؟", "السمك البخاخ"),
("ما هو الحيوان الذي له 3 قلوب؟", "الأخطبوط"),
("ما هو الحيوان الذي له 8 أذرع؟", "الأخطبوط"),
("ما هو الحيوان الأبطأ في العالم؟", "الكسلان"),
("ما هو أطول حيوان في العالم؟", "الزرافة"),
("ما هو أكبر طائر في العالم؟", "النعامة"),
("ما هو أصغر طائر؟", "طائر الطنان"),
("ما هو الحيوان الذي يرى في الليل؟", "البومة"),
("ما هو الحيوان الذي ينام واقفاً؟", "الحصان"),
("ما هي أكبر دولة عربية؟", "الجزائر"),
("ما هي أصغر دولة عربية؟", "البحرين"),
("ما هي عاصمة العراق؟", "بغداد"),
("ما هي عملة العراق؟", "الدينار"),
("ما هي عملة أمريكا؟", "الدولار"),
("ما هي عملة أوروبا؟", "اليورو"),
("ما هو أطول نهر في العالم؟", "النيل"),
("ما هو ثاني أطول نهر؟", "الأمازون"),
("ما هي أكبر دولة في آسيا؟", "الصين"),
("ما هي أكبر دولة في أوروبا؟", "روسيا"),
("ما هو عدد أيام الأسبوع؟", "7"),
("ما هو عدد ساعات اليوم؟", "24"),
("ما هو أقرب نجم للأرض؟", "الشمس"),
("ما هو أكبر كوكب قزم؟", "بلوتو"),
("ما هو لون الدم؟", "أحمر"),
("ما هو لون السماء؟", "أزرق"),
("ما هو أسرع شيء في الكون؟", "الضوء"),
("ما هي سرعة الضوء؟", "300000 كم/ث"),
("ما هو الشيء الذي إذا كثر غلا؟", "الماء (في بعض السياقات)"),
("ما هو الشيء الذي إذا نقص زاد؟", "الحفرة"),
("ما هو الشيء الذي لا ظل له؟", "الضوء"),
("ما هو الشيء الذي لا صوت له؟", "الظل"),
("ما هو الشيء الذي يمشي بلا أرجل؟", "الوقت"),
("ما هو الشيء الذي لا يمشي إلا بالضرب؟", "المسمار")
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
