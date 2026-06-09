from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus
import asyncio

from database import Database
from utils import NotificationManager, Utils
from config import Config

class AdminCommands:
    def __init__(self, db: Database):
        self.db = db
    
    async def is_admin_or_owner(self, update: Update, user_id: int) -> bool:
        """التحقق من صلاحيات المشرف أو المالك"""
        if user_id == Config.OWNER_ID:
            return True
        
        # التحقق من صلاحيات المشرف في المجموعة
        chat_member = await update.effective_chat.get_member(user_id)
        if chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
        
        # التحقق من قائمة المشرفين في قاعدة البيانات
        return self.db.is_admin(user_id)
    
    async def warn_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر تحذير - إضافة تحذير لعضو"""
        user_id = update.effective_user.id
        
        if not await self.is_admin_or_owner(update, user_id):
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "⚠️ هذا الأمر متاح فقط للمشرفين"
            )
            return
        
        args = context.args
        if not args:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "الاستخدام: <code>تحذير @username [السبب]</code>"
            )
            return
        
        # استخراج معرف المستخدم المستهدف
        target_username = args[0]
        reason = ' '.join(args[1:]) if len(args) > 1 else 'لا يوجد سبب'
        
        # البحث عن المستخدم
        target_user = None
        for entity in update.effective_message.entities:
            if entity.type == 'mention':
                username = update.effective_message.text[entity.offset:entity.offset + entity.length].replace('@', '')
                target_user = await update.effective_chat.get_member_by_username(username)
                break
        
        if not target_user:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "لم يتم العثور على المستخدم"
            )
            return
        
        # إضافة التحذير
        warnings_count = self.db.add_warning(target_user.user.id, user_id, reason)
        
        # إشعار التحذير المتطور
        await NotificationManager.send_warning_notification(
            update.effective_message.bot,
            update.effective_chat.id,
            f"⚠️ <b>تحذير للمستخدم {target_user.user.first_name}</b>\n\n"
            f"• المنفذ: @{update.effective_user.username or update.effective_user.first_name}\n"
            f"• السبب: {reason}\n"
            f"• عدد التحذيرات الآن: <b>{warnings_count}</b>\n\n"
            f"<i>3 تحذيرات = كتم تلقائي لمدة 24 ساعة</i>"
        )
        
        # كتم تلقائي عند 3 تحذيرات
        if warnings_count >= 3:
            until = self.db.mute_user(target_user.user.id, user_id, 86400, "تجاوز 3 تحذيرات")
            await NotificationManager.send_warning_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                f"🔇 <b>تم كتم {target_user.user.first_name} تلقائياً</b>\n"
                f"السبب: تجاوز 3 تحذيرات\n"
                f"المدة: 24 ساعة"
            )
    
    async def fine_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر خصم - خصم مبلغ من رصيد العضو"""
        user_id = update.effective_user.id
        
        if not await self.is_admin_or_owner(update, user_id):
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "⚠️ هذا الأمر متاح فقط للمشرفين"
            )
            return
        
        args = context.args
        if len(args) < 2:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "الاستخدام: <code>خصم @username المبلغ [السبب]</code>\n"
                f"أقل خصم: {Config.MIN_FINE} - أقصى خصم: {Config.MAX_FINE}"
            )
            return
        
        # استخراج البيانات
        target_username = args[0]
        try:
            amount = int(args[1])
        except ValueError:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "المبلغ يجب أن يكون رقماً"
            )
            return
        
        reason = ' '.join(args[2:]) if len(args) > 2 else 'لا يوجد سبب'
        
        # التحقق من المبلغ
        if amount < Config.MIN_FINE or amount > Config.MAX_FINE:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                f"المبلغ غير مسموح به\nأقل خصم: {Config.MIN_FINE} - أقصى خصم: {Config.MAX_FINE}"
            )
            return
        
        # البحث عن المستخدم
        target_user = None
        for entity in update.effective_message.entities:
            if entity.type == 'mention':
                username = update.effective_message.text[entity.offset:entity.offset + entity.length].replace('@', '')
                target_user = await update.effective_chat.get_member_by_username(username)
                break
        
        if not target_user:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "لم يتم العثور على المستخدم"
            )
            return
        
        # تطبيق الخصم
        new_balance = self.db.update_balance(target_user.user.id, -amount)
        
        # تحديث إحصائيات الخصومات
        with self.db.get_connection() as conn:
            conn.execute('''
                UPDATE users SET fines_count = fines_count + 1, total_fines = total_fines + ?
                WHERE user_id = ?
            ''', (amount, target_user.user.id))
        
        await NotificationManager.send_warning_notification(
            update.effective_message.bot,
            update.effective_chat.id,
            f"💰 <b>خصم من {target_user.user.first_name}</b>\n\n"
            f"• المنفذ: @{update.effective_user.username or update.effective_user.first_name}\n"
            f"• المبلغ: <b>{amount:,} 💰</b>\n"
            f"• السبب: {reason}\n"
            f"• الرصيد الجديد: <b>{new_balance:,} 💰</b>"
        )
    
    async def mute_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر كتم - كتم عضو لمدة محددة"""
        user_id = update.effective_user.id
        
        if not await self.is_admin_or_owner(update, user_id):
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "⚠️ هذا الأمر متاح فقط للمشرفين"
            )
            return
        
        args = context.args
        if len(args) < 2:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "الاستخدام: <code>كتم @username المدة [السبب]</code>\n\n"
                "المدة: 1ث، 1د، 1س، 1ي"
            )
            return
        
        # استخراج البيانات
        target_username = args[0]
        duration_str = args[1]
        reason = ' '.join(args[2:]) if len(args) > 2 else 'لا يوجد سبب'
        
        # تحويل المدة إلى ثواني
        duration_seconds = Utils.parse_time(duration_str)
        if not duration_seconds:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "صيغة المدة غير صحيحة\nمثال: 1ث، 1د، 1س، 1ي"
            )
            return
        
        # البحث عن المستخدم
        target_user = None
        for entity in update.effective_message.entities:
            if entity.type == 'mention':
                username = update.effective_message.text[entity.offset:entity.offset + entity.length].replace('@', '')
                target_user = await update.effective_chat.get_member_by_username(username)
                break
        
        if not target_user:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "لم يتم العثور على المستخدم"
            )
            return
        
        # تطبيق الكتم
        self.db.mute_user(target_user.user.id, user_id, duration_seconds, reason)
        
        duration_readable = Utils.format_time(duration_seconds)
        
        await NotificationManager.send_warning_notification(
            update.effective_message.bot,
            update.effective_chat.id,
            f"🔇 <b>تم كتم {target_user.user.first_name}</b>\n\n"
            f"• المنفذ: @{update.effective_user.username or update.effective_user.first_name}\n"
            f"• المدة: {duration_readable}\n"
            f"• السبب: {reason}\n\n"
            f"<i>لن يتمكن العضو من إرسال الرسائل حتى انتهاء المدة</i>"
        )
        
        # حذف رسالة العضو الحالية
        try:
            await update.message.delete()
        except:
            pass
    
    async def reward_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر مكافأة/مكافاة - إضافة مكافأة مالية لعضو"""
        user_id = update.effective_user.id
        
        if not await self.is_admin_or_owner(update, user_id):
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "⚠️ هذا الأمر متاح فقط للمشرفين"
            )
            return
        
        args = context.args
        if len(args) < 2:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "الاستخدام: <code>مكافأة @username المبلغ [السبب]</code>"
            )
            return
        
        # استخراج البيانات
        target_username = args[0]
        try:
            amount = int(args[1])
        except ValueError:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "المبلغ يجب أن يكون رقماً"
            )
            return
        
        reason = ' '.join(args[2:]) if len(args) > 2 else 'مكافأة من المشرف'
        
        # البحث عن المستخدم
        target_user = None
        for entity in update.effective_message.entities:
            if entity.type == 'mention':
                username = update.effective_message.text[entity.offset:entity.offset + entity.length].replace('@', '')
                target_user = await update.effective_chat.get_member_by_username(username)
                break
        
        if not target_user:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "لم يتم العثور على المستخدم"
            )
            return
        
        # إضافة المكافأة
        new_balance = self.db.update_balance(target_user.user.id, amount)
        
        await NotificationManager.send_success_notification(
            update.effective_message.bot,
            update.effective_chat.id,
            f"🎁 <b>مكافأة لـ {target_user.user.first_name}</b>\n\n"
            f"• المنفذ: @{update.effective_user.username or update.effective_user.first_name}\n"
            f"• المبلغ: <b>+{amount:,} 💰</b>\n"
            f"• السبب: {reason}\n"
            f"• الرصيد الجديد: <b>{new_balance:,} 💰</b>"
        )
    
    async def kick_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر طرد - طرد عضو من المجموعة"""
        user_id = update.effective_user.id
        
        if not await self.is_admin_or_owner(update, user_id):
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "⚠️ هذا الأمر متاح فقط للمشرفين"
            )
            return
        
        args = context.args
        if not args:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "الاستخدام: <code>طرد @username</code>"
            )
            return
        
        # البحث عن المستخدم
        target_username = args[0]
        target_user = None
        for entity in update.effective_message.entities:
            if entity.type == 'mention':
                username = update.effective_message.text[entity.offset:entity.offset + entity.length].replace('@', '')
                target_user = await update.effective_chat.get_member_by_username(username)
                break
        
        if not target_user:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "لم يتم العثور على المستخدم"
            )
            return
        
        # طرد العضو
        try:
            await update.effective_chat.ban_member(target_user.user.id)
            await update.effective_chat.unban_member(target_user.user.id)
            
            await NotificationManager.send_warning_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                f"🚫 <b>تم طرد {target_user.user.first_name}</b>\n\n"
                f"• المنفذ: @{update.effective_user.username or update.effective_user.first_name}"
            )
        except Exception as e:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                f"فشل طرد العضو: {str(e)}"
            )
    
    async def ban_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر حظر - حظر عضو من المجموعة"""
        user_id = update.effective_user.id
        
        if not await self.is_admin_or_owner(update, user_id):
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "⚠️ هذا الأمر متاح فقط للمشرفين"
            )
            return
        
        args = context.args
        if not args:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "الاستخدام: <code>حظر @username [السبب]</code>"
            )
            return
        
        # استخراج البيانات
        target_username = args[0]
        reason = ' '.join(args[1:]) if len(args) > 1 else 'لا يوجد سبب'
        
        # البحث عن المستخدم
        target_user = None
        for entity in update.effective_message.entities:
            if entity.type == 'mention':
                username = update.effective_message.text[entity.offset:entity.offset + entity.length].replace('@', '')
                target_user = await update.effective_chat.get_member_by_username(username)
                break
        
        if not target_user:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "لم يتم العثور على المستخدم"
            )
            return
        
        # حظر العضو
        try:
            await update.effective_chat.ban_member(target_user.user.id)
            
            # تسجيل الحظر في قاعدة البيانات
            with self.db.get_connection() as conn:
                conn.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (target_user.user.id,))
            
            await NotificationManager.send_warning_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                f"⛔ <b>تم حظر {target_user.user.first_name}</b>\n\n"
                f"• المنفذ: @{update.effective_user.username or update.effective_user.first_name}\n"
                f"• السبب: {reason}"
            )
        except Exception as e:
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                f"فشل حظر العضو: {str(e)}"
            )
    
    async def punishments_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر عقوبات - عرض العقوبات"""
        user_id = update.effective_user.id
        
        if not await self.is_admin_or_owner(update, user_id):
            await NotificationManager.send_error_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "⚠️ هذا الأمر متاح فقط للمشرفين"
            )
            return
        
        # الحصول على جميع المستخدمين الذين لديهم عقوبات
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, first_name, username, warnings
                FROM users
                WHERE warnings > 0 OR is_muted = 1 OR is_banned = 1
                ORDER BY warnings DESC
                LIMIT 10
            ''')
            users = cursor.fetchall()
        
        if not users:
            await NotificationManager.send_notification(
                update.effective_message.bot,
                update.effective_chat.id,
                "لا توجد عقوبات مسجلة حالياً",
                Config.NOTIFICATION_DURATION
            )
            return
        
        punishments_text = "⚠️ <b>قائمة المخالفين</b>\n\n"
        for user in users:
            punishments_text += f"👤 {user['first_name']}\n"
            punishments_text += f"└ التحذيرات: <b>{user['warnings']}</b>\n\n"
        
        await NotificationManager.send_notification(
            update.effective_message.bot,
            update.effective_chat.id,
            punishments_text,
            Config.NOTIFICATION_DURATION
        )
