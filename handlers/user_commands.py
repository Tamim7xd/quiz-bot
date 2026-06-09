import asyncio
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from datetime import datetime, timedelta
import random
import json

from database import Database
from utils import NotificationManager, Utils
from keyboards.owner_keyboards import GameKeyboards
from config import Config

class UserCommands:
    def __init__(self, db: Database):
        self.db = db
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /start"""
        user = update.effective_user
        chat = update.effective_chat
        
        # تسجيل المستخدم إذا لم يكن موجوداً
        if not self.db.get_user(user.id):
            self.db.create_user(user.id, user.username, user.first_name, user.last_name or '')
        
        welcome_msg = f"""
🌟 <b>مرحباً بك {user.first_name}!</b>

أنا بوت إدارة متطور للمجموعات 🚀

<b>الأوامر المتاحة:</b>
• <code>حساب</code> - عرض ملفك الشخصي
• <code>العاب</code> - قائمة الألعاب
• <code>سوق</code> - شراء الألقاب
• <code>يومي</code> - الحصول على مكافأتك اليومية
• <code>مستوى</code> - عرض مستواك
• <code>توب</code> - ترتيب الأعضاء

<b>استمتع بتجربتك! 🎉</b>
"""
        await update.message.reply_text(welcome_msg, parse_mode='HTML')
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر حساب/ملفي - عرض الملف الشخصي"""
        user_id = update.effective_user.id
        
        # محاولة الحصول على معرف المستخدم المطلوب (إذا تم منشن)
        args = context.args
        target_id = user_id
        if args:
            mentioned_id = Utils.extract_user_id(' '.join(args))
            if mentioned_id:
                target_id = mentioned_id
        
        user_data = self.db.get_user(target_id)
        if not user_data:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "المستخدم غير موجود في قاعدة البيانات"
            )
            return
        
        # تحديث الأوسمة التلقائية
        self.db.check_and_award_auto_badges(target_id)
        
        # الحصول على الأوسمة
        badges = self.db.get_user_badges(target_id)
        badges_text = '\n'.join([f"{b['badge_icon']} {b['badge_name']}" for b in badges]) if badges else "لا يوجد"
        
        # الحصول على الألقاب
        titles = self.db.get_user_titles(target_id)
        titles_text = '\n'.join([f"🏷️ {t}" for t in titles]) if titles else "لا يوجد"
        
        # تنسيق الملف الشخصي
        profile_text = f"""
👤 <b>{user_data['first_name']}</b>
└ @{user_data['username'] if user_data['username'] else 'لا يوجد'}

━━━━━━━━━━━━━━━━━━━━
📊 <b>الإحصائيات</b>
• المستوى: <b>{user_data['level']}</b>
• الخبرة: <b>{user_data['xp']}/{user_data['level'] * 100}</b>
• الرصيد: <b>{user_data['balance']:,.0f} 💰</b>
• الرسائل: <b>{user_data['messages_count']:,}</b>
• الألعاب: <b>{user_data['games_won']} فوز / {user_data['games_played']} لعب</b>

━━━━━━━━━━━━━━━━━━━━
⚠️ <b>العقوبات</b>
• التحذيرات: <b>{user_data['warnings']}</b>
• عدد الخصومات: <b>{user_data['fines_count']}</b>
• إجمالي الخصومات: <b>{user_data['total_fines']:,.0f} 💰</b>

━━━━━━━━━━━━━━━━━━━━
🏅 <b>الأوسمة</b>
{badges_text}

━━━━━━━━━━━━━━━━━━━━
🏷️ <b>الألقاب المشتراة</b>
{titles_text}
"""
        await NotificationManager.send_profile_notification(
            update.effective_message.bot,
            update.effective_chat.id,
            target_id,
            user_data['username'],
            user_data['first_name'],
            user_data['level'],
            user_data['balance'],
            user_data['messages_count'],
            user_data['warnings'],
            user_data['fines_count'],
            titles,
            Config.NOTIFICATION_DURATION
        )
    
    async def games_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر العاب/لعبة/العب - عرض قائمة الألعاب"""
        msg = await update.message.reply_text(
            "🎮 <b>اختر لعبتك المفضلة</b>\n\n"
            "العب واربح <b>2,500 💰</b> عند الفوز!",
            parse_mode='HTML',
            reply_markup=GameKeyboards.games_menu()
        )
        
        # حفظ معرف الرسالة لحذفها لاحقاً
        context.user_data['games_menu_msg_id'] = msg.message_id
        
        # حذف القائمة بعد 3 ثواني إذا لم يختر شيئاً
        await asyncio.sleep(3)
        
        # التحقق إذا لم يتم الرد بعد
        if context.user_data.get('games_menu_active', True):
            try:
                await msg.delete()
            except:
                pass
            await NotificationManager.send_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "⏰ انتهت مهلة اختيار اللعبة، أعد كتابة <code>الالعاب</code> لبدء جديدة",
                2
            )
    
    async def market_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر سوق/ماركت - عرض السوق"""
        items = self.db.get_market_items()
        
        if not items:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "السوق فارغ حالياً"
            )
            return
        
        market_text = "🛒 <b>السوق</b>\n\n"
        for item in items:
            market_text += f"{item['item_icon']} {item['item_name']}\n"
            market_text += f"└ السعر: <b>{item['price']:,} 💰</b>\n\n"
        
        market_text += "\n<i>استخدم الأمر التالي للشراء:</i>\n"
        market_text += "<code>شراء [رقم العنصر]</code>"
        
        await NotificationManager.send_notification(
            update.effective_message.bot,
            update.effective_chat.id,
            market_text,
            Config.NOTIFICATION_DURATION
        )
    
    async def buy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """شراء عنصر من السوق"""
        args = context.args
        if not args:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "الاستخدام: <code>شراء [رقم العنصر]</code>"
            )
            return
        
        try:
            item_id = int(args[0])
        except ValueError:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "يرجى إدخال رقم العنصر الصحيح"
            )
            return
        
        user_id = update.effective_user.id
        
        # الحصول على العنصر
        items = self.db.get_market_items()
        item = next((i for i in items if i['id'] == item_id), None)
        
        if not item:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "العنصر غير موجود"
            )
            return
        
        # محاولة الشراء
        success = self.db.purchase_item(user_id, item_id)
        
        if success:
            await NotificationManager.send_success_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                f"تم شراء <b>{item['item_name']}</b> بنجاح!\n"
                f"تم خصم <b>{item['price']:,} 💰</b> من رصيدك"
            )
        else:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "رصيدك غير كافٍ لشراء هذا العنصر"
            )
    
    async def daily_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر يومي - المكافأة اليومية (النظام 16)"""
        user_id = update.effective_user.id
        
        result = self.db.claim_daily(user_id)
        
        if result['success']:
            streak = result['streak']
            reward = result['reward']
            
            # رسالة خاصة لليوم 7 و 14 و 30
            bonus_msg = ""
            if streak in [7, 14, 30]:
                bonus_msg = f"\n🎉 <b>إنجاز! لقد وصلت إلى {streak} يوم متتالي!</b>"
            
            await NotificationManager.send_success_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                f"⭐ <b>المكافأة اليومية</b>\n\n"
                f"• الستريك الحالي: <b>{streak} يوم</b>\n"
                f"• المكافأة: <b>{reward:,} 💰</b>\n"
                f"• الرصيد الجديد: <b>{result['new_balance']:,} 💰</b>"
                f"{bonus_msg}"
            )
        else:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                result['message']
            )
    
    async def level_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر مستوى - عرض المستوى والخبرة"""
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        
        if not user_data:
            await update.message.reply_text("يرجى البدء أولاً باستخدام /start")
            return
        
        xp_needed = user_data['level'] * 100
        progress = Utils.create_progress_bar(user_data['xp'], xp_needed)
        
        level_text = f"""
📊 <b>مستواك</b>

👤 {user_data['first_name']}
• المستوى: <b>{user_data['level']}</b>
• الخبرة: <b>{user_data['xp']} / {xp_needed}</b>

{progress} <code>{user_data['xp']}/{xp_needed}</code>

<i>كل {user_data['level'] * 100} نقطة خبرة = مستوى جديد + 500 💰</i>
"""
        await NotificationManager.send_notification(
            update.effective_message.bot,
            update.effective_chat.id,
            level_text,
            Config.NOTIFICATION_DURATION
        )
    
    async def top_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر توب - عرض الترتيب"""
        top_users = self.db.get_top_users(10, 'messages_count')
        
        if not top_users:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "لا يوجد مستخدمين مسجلين بعد"
            )
            return
        
        top_text = "🏆 <b>ترتيب الأعضاء النشطين</b>\n\n"
        
        for i, user in enumerate(top_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            name = user['first_name'][:15]
            top_text += f"{medal} {name} - <b>{user['messages_count']:,}</b> رسالة\n"
        
        await NotificationManager.send_notification(
            update.effective_message.bot,
            update.effective_chat.id,
            top_text,
            Config.NOTIFICATION_DURATION
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل العادية"""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        
        # التحقق من الكتم
        is_muted, until = self.db.is_muted(user.id)
        if is_muted:
            await message.delete()
            await NotificationManager.send_warning_notification(
                message.bot,
                chat.id,
                f"أنت مكتوم حتى {Utils.format_time_remaining(until)}"
            )
            return
        
        # تسجيل المستخدم
        if not self.db.get_user(user.id):
            self.db.create_user(user.id, user.username, user.first_name, user.last_name or '')
        
        # تحديث نشاط المستخدم
        self.db.update_user_activity(user.id)
        
        # إضافة نقاط خبرة
        new_level, leveled_up = self.db.add_xp(user.id, 10)
        
        if leveled_up:
            await NotificationManager.send_success_notification(
                message.bot,
                chat.id,
                f"🎉 <b>تهانينا {user.first_name}!</b>\n\n"
                f"لقد وصلت إلى المستوى <b>{new_level}</b>\n"
                f"ومكافأة <b>500 💰</b>"
            )
        
        # التحقق من الأوسمة التلقائية
        self.db.check_and_award_auto_badges(user.id)
        
        # الرد التلقائي على الكلمات المفتاحية
        if Config.SYSTEM_STATUS.get('auto_reply_system', True):
            reply = self.db.get_auto_reply(message.text)
            if reply:
                await message.reply_text(reply)
    
    async def game_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أزرار الألعاب"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        if data == "game_cancel" or data == "game_close":
            await query.message.delete()
            context.user_data['games_menu_active'] = False
            return
        
        # حجر ورقة مقص
        if data.startswith("game_rps_"):
            await self.play_rps(query, context, data)
        
        # تخمين الرقم
        elif data.startswith("guess_"):
            await self.play_guess(query, context, data)
        
        # ألعاب أخرى
        elif data == "game_rps_menu":
            await query.message.edit_text(
                "🗻 <b>لعبة حجر ورقة مقص</b>\n\nاختر رمزك:",
                parse_mode='HTML',
                reply_markup=GameKeyboards.rps_game()
            )
        
        elif data == "game_guess_menu":
            await query.message.edit_text(
                "🎲 <b>لعبة تخمين الرقم</b>\n\nاختر رقماً من 1 إلى 10:",
                parse_mode='HTML',
                reply_markup=GameKeyboards.guest_game()
            )
    
    async def play_rps(self, query, context, data):
        """تنفيذ لعبة حجر ورقة مقص"""
        user_choice = data.split("_")[2]
        choices = {'rock': '🗻 حجر', 'paper': '📜 ورقة', 'scissors': '✂️ مقص'}
        bot_choice = random.choice(['rock', 'paper', 'scissors'])
        
        # تحديد الفائز
        if user_choice == bot_choice:
            result = "🤝 تعادل"
            win = False
        elif (user_choice == 'rock' and bot_choice == 'scissors') or \
             (user_choice == 'paper' and bot_choice == 'rock') or \
             (user_choice == 'scissors' and bot_choice == 'paper'):
            result = "🎉 فوز!"
            win = True
        else:
            result = "😢 خسارة"
            win = False
        
        if win:
            self.db.add_game_win(query.from_user.id)
            self.db.update_balance(query.from_user.id, 2500)
            reward_msg = "\n\n💰 <b>+2,500 💰</b>"
        else:
            self.db.add_game_loss(query.from_user.id)
            reward_msg = ""
        
        await query.message.edit_text(
            f"🎮 <b>لعبة حجر ورقة مقص</b>\n\n"
            f"أنت: {choices[user_choice]}\n"
            f"البوت: {choices[bot_choice]}\n\n"
            f"<b>{result}</b>{reward_msg}",
            parse_mode='HTML'
        )
        
        await asyncio.sleep(3)
        await query.message.delete()
    
    async def play_guess(self, query, context, data):
        """تنفيذ لعبة تخمين الرقم"""
        user_guess = int(data.split("_")[1])
        secret = random.randint(1, 10)
        
        if user_guess == secret:
            result = "🎉 فوز!"
            win = True
        else:
            result = f"😢 خسارة... الرقم الصحيح كان {secret}"
            win = False
        
        if win:
            self.db.add_game_win(query.from_user.id)
            self.db.update_balance(query.from_user.id, 2500)
            reward_msg = "\n\n💰 <b>+2,500 💰</b>"
        else:
            self.db.add_game_loss(query.from_user.id)
            reward_msg = ""
        
        await query.message.edit_text(
            f"🎲 <b>لعبة تخمين الرقم</b>\n\n"
            f"تخمينك: {user_guess}\n"
            f"الرقم السري: {secret}\n\n"
            f"<b>{result}</b>{reward_msg}",
            parse_mode='HTML'
        )
        
        await asyncio.sleep(3)
        await query.message.delete()
