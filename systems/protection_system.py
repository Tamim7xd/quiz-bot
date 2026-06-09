import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from telegram import Update, ChatMember
from telegram.ext import ContextTypes

from database import Database
from config import Config
from utils import NotificationManager

class ProtectionSystem:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.user_messages: Dict[int, List[datetime]] = {}  # تتبع الرسائل لمكافحة السبام
        
    async def check_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Tuple[bool, str]:
        """
        التحقق من الرسالة وتطبيق الحماية
        إرجاع (مسموح, سبب المنع)
        """
        message = update.message
        user = message.from_user
        chat = message.chat
        
        # تجاهل رسائل المالك والمشرفين
        if user.id == self.config.OWNER_ID:
            return True, ""
        
        # التحقق من صلاحيات المشرف
        chat_member = await chat.get_member(user.id)
        if chat_member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            return True, ""
        
        # 1. التحقق من الكتم
        is_muted, until = self.db.is_muted(user.id)
        if is_muted:
            await message.delete()
            return False, "أنت مكتوم حالياً"
        
        # 2. التحقق من طول الرسالة
        if self.config.PROTECTION_SETTINGS.get('max_message_length', 500):
            if len(message.text) > self.config.PROTECTION_SETTINGS['max_message_length']:
                await message.delete()
                await NotificationManager.send_warning_notification(
                    message.bot, chat.id,
                    f"⚠️ {user.first_name}، رسالتك طويلة جداً (أقصى طول {self.config.PROTECTION_SETTINGS['max_message_length']} حرف)"
                )
                return False, "رسالة طويلة جداً"
        
        # 3. التحقق من الروابط
        if self.config.PROTECTION_SETTINGS.get('block_links', True):
            if self.contains_link(message.text):
                await message.delete()
                await NotificationManager.send_warning_notification(
                    message.bot, chat.id,
                    f"🔗 {user.first_name}، ممنوع إرسال الروابط في المجموعة"
                )
                return False, "رابط ممنوع"
        
        # 4. التحقق من البوتات
        if self.config.PROTECTION_SETTINGS.get('block_bots', True):
            if message.forward_from_bot or (message.text and 't.me/' in message.text.lower()):
                await message.delete()
                await NotificationManager.send_warning_notification(
                    message.bot, chat.id,
                    f"🤖 {user.first_name}، ممنوع إرسال بوتات أو روابط بوتات"
                )
                return False, "بوت ممنوع"
        
        # 5. التحقق من إعادة التوجيه
        if self.config.PROTECTION_SETTINGS.get('block_forward', True):
            if message.forward_date:
                await message.delete()
                await NotificationManager.send_warning_notification(
                    message.bot, chat.id,
                    f"📤 {user.first_name}، ممنوع إعادة توجيه الرسائل"
                )
                return False, "إعادة توجيه ممنوعة"
        
        # 6. التحقق من الكلمات الممنوعة
        if self.db.is_forbidden_word(message.text):
            await message.delete()
            # إضافة تحذير تلقائي
            warnings_count = self.db.add_warning(user.id, self.config.OWNER_ID, "كلمة ممنوعة")
            await NotificationManager.send_warning_notification(
                message.bot, chat.id,
                f"🚫 {user.first_name}، كلمة ممنوعة!\n"
                f"⚠️ تحذير #{warnings_count}"
            )
            
            # كتم تلقائي عند 3 تحذيرات
            if warnings_count >= 3:
                self.db.mute_user(user.id, self.config.OWNER_ID, 86400, "تجاوز 3 تحذيرات")
                await NotificationManager.send_warning_notification(
                    message.bot, chat.id,
                    f"🔇 تم كتم {user.first_name} تلقائياً لمدة 24 ساعة بسبب تكرار الكلمات الممنوعة"
                )
            return False, "كلمة ممنوعة"
        
        # 7. مكافحة السبام (Flood)
        if self.config.PROTECTION_SETTINGS.get('anti_flood_count', 5):
            if not self.check_flood(user.id):
                await message.delete()
                # كتم تلقائي لمدة 5 دقائق للسبام
                self.db.mute_user(user.id, self.config.OWNER_ID, 300, "سبام")
                await NotificationManager.send_warning_notification(
                    message.bot, chat.id,
                    f"💧 {user.first_name}، تم كتمك لمدة 5 دقائق بسبب الإرسال المتكرر"
                )
                return False, "سبام"
        
        # 8. التحقق من اللغة العربية فقط (اختياري)
        if self.config.PROTECTION_SETTINGS.get('block_arabic_only', False):
            if not self.is_arabic_text(message.text):
                await message.delete()
                await NotificationManager.send_warning_notification(
                    message.bot, chat.id,
                    f"🌐 {user.first_name}، يسمح فقط باللغة العربية في هذه المجموعة"
                )
                return False, "لغة غير مسموحة"
        
        return True, ""
    
    def contains_link(self, text: str) -> bool:
        """التحقق من وجود رابط في النص (جميع الصيغ)"""
        patterns = [
            r'https?://[^\s]+',           # http://, https://
            r'www\.[^\s]+',                # www.
            r't\.me/[^\s]+',               # t.me
            r'telegram\.me/[^\s]+',        # telegram.me
            r'telegram\.dog/[^\s]+',       # telegram.dog
            r'bit\.ly/[^\s]+',             # bit.ly
            r'goo\.gl/[^\s]+',             # goo.gl
            r'ow\.ly/[^\s]+',              # ow.ly
            r'is\.gd/[^\s]+',              # is.gd
            r'u\.to/[^\s]+',               # u.to
            r'cutt\.us/[^\s]+',            # cutt.us
            r'shor tlink\.com/[^\s]+',     # shortlink
            r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/\S*)?',  # domain.com
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # التحقق من نص تيليجرام المنقول
        if 'telegram.me' in text.lower() or 't.me' in text.lower():
            return True
        
        return False
    
    def check_flood(self, user_id: int) -> bool:
        """
        التحقق من السبام (عدد الرسائل في فترة زمنية)
        إرجاع False إذا كان سبام
        """
        now = datetime.now()
        
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        
        # حذف الرسائل القديمة
        self.user_messages[user_id] = [
            msg_time for msg_time in self.user_messages[user_id]
            if (now - msg_time).seconds < self.config.PROTECTION_SETTINGS['anti_flood_seconds']
        ]
        
        # التحقق من عدد الرسائل
        if len(self.user_messages[user_id]) >= self.config.PROTECTION_SETTINGS['anti_flood_count']:
            return False
        
        # إضافة الرسالة الحالية
        self.user_messages[user_id].append(now)
        return True
    
    def is_arabic_text(self, text: str) -> bool:
        """التحقق إذا كان النص عربياً بنسبة كبيرة"""
        arabic_chars = 0
        total_chars = 0
        
        for char in text:
            # الأحرف العربية والحركات
            if '\u0600' <= char <= '\u06FF' or char in '.,!?؟!،،؛':
                arabic_chars += 1
            if char.isalpha():
                total_chars += 1
        
        if total_chars == 0:
            return True
        
        return (arabic_chars / total_chars) > 0.6
    
    async def handle_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الأعضاء الجدد (منع البوتات)"""
        message = update.message
        
        for new_member in message.new_chat_members:
            # منع البوتات من الانضمام
            if new_member.is_bot:
                try:
                    await message.chat.ban_member(new_member.id)
                    await NotificationManager.send_warning_notification(
                        message.bot, message.chat.id,
                        f"🤖 تم طرد البوت {new_member.first_name} تلقائياً"
                    )
                except:
                    pass
                continue
    
    async def update_protection_settings(self, setting: str, value: bool):
        """تحديث إعدادات الحماية"""
        if setting in self.config.PROTECTION_SETTINGS:
            self.config.PROTECTION_SETTINGS[setting] = value
            return True
        return False
    
    def get_protection_status(self) -> Dict:
        """الحصول على حالة إعدادات الحماية"""
        return self.config.PROTECTION_SETTINGS
