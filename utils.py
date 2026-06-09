import re
import asyncio
from datetime import datetime, timedelta
from typing import Tuple, Optional, List
from telegram import Bot, Message

class Utils:
    
    @staticmethod
    def parse_time(time_str: str) -> Optional[int]:
        """
        تحويل صيغة الوقت إلى ثواني
        مثال: 1ث = 1 ثانية، 1د = 60 ثانية، 1س = 3600 ثانية، 1ي = 86400 ثانية
        """
        if not time_str:
            return None
        
        patterns = [
            (r'^(\d+)ث$', 1),      # ثواني
            (r'^(\d+)د$', 60),     # دقائق
            (r'^(\d+)س$', 3600),   # ساعات
            (r'^(\d+)ي$', 86400),  # أيام
        ]
        
        for pattern, multiplier in patterns:
            match = re.match(pattern, time_str)
            if match:
                return int(match.group(1)) * multiplier
        
        return None
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """تحويل الثواني إلى صيغة مقروءة"""
        if seconds >= 86400:
            days = seconds // 86400
            return f"{days} يوم"
        elif seconds >= 3600:
            hours = seconds // 3600
            return f"{hours} ساعة"
        elif seconds >= 60:
            minutes = seconds // 60
            return f"{minutes} دقيقة"
        else:
            return f"{seconds} ثانية"
    
    @staticmethod
    def format_number(num: int) -> str:
        """تنسيق الأرقام (1000 -> 1,000)"""
        return f"{num:,}"
    
    @staticmethod
    def extract_mention(text: str) -> Optional[str]:
        """استخراج معرف المستخدم من نص (مثال: @username)"""
        match = re.search(r'@(\w+)', text)
        return match.group(1) if match else None
    
    @staticmethod
    def extract_user_id(text: str) -> Optional[int]:
        """استخراج معرف المستخدم من نص (مثال: [123456789])"""
        match = re.search(r'\[(\d+)\]', text)
        return int(match.group(1)) if match else None
    
    @staticmethod
    def remove_bad_words(text: str, bad_words: List[str]) -> str:
        """إزالة الكلمات البذيئة من النص"""
        for word in bad_words:
            text = re.sub(re.escape(word), '***', text, flags=re.IGNORECASE)
        return text
    
    @staticmethod
    def is_arabic_text(text: str) -> bool:
        """التحقق إذا كان النص عربياً بشكل أساسي"""
        arabic_chars = 0
        total_chars = 0
        
        for char in text:
            if '\u0600' <= char <= '\u06FF' or char in '.,!?؟!،':
                arabic_chars += 1
            if char.isalpha():
                total_chars += 1
        
        if total_chars == 0:
            return True
        
        return (arabic_chars / total_chars) > 0.5
    
    @staticmethod
    def contains_link(text: str) -> bool:
        """التحقق من وجود رابط في النص"""
        patterns = [
            r'https?://[^\s]+',
            r'www\.[^\s]+',
            r't\.me/[^\s]+',
            r'telegram\.me/[^\s]+',
            r'bit\.ly/[^\s]+',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def create_progress_bar(current: int, total: int, length: int = 10) -> str:
        """إنشاء شريط تقدم"""
        if total == 0:
            return '█' * length
        
        filled = int(length * current / total)
        empty = length - filled
        return '█' * filled + '░' * empty


class NotificationManager:
    """مدير الإشعارات المتطورة (يختفي بعد 3 ثواني)"""
    
    @staticmethod
    async def send_notification(
        bot: Bot,
        chat_id: int,
        message: str,
        duration: int = 3,
        parse_mode: str = 'HTML'
    ) -> None:
        """
        إرسال إشعار يختفي تلقائياً بعد مدة محددة
        """
        # تنسيق الإشعار
        formatted_msg = f"""
<b>📢 إشعار</b>

{message}

<code>⏱️ سيختفي هذا الإشعار تلقائياً بعد {duration} ثواني</code>
"""
        msg = await bot.send_message(
            chat_id=chat_id,
            text=formatted_msg,
            parse_mode=parse_mode
        )
        
        # حذف الإشعار بعد المدة المحددة
        await asyncio.sleep(duration)
        try:
            await msg.delete()
        except:
            pass
    
    @staticmethod
    async def send_success_notification(bot: Bot, chat_id: int, message: str, duration: int = 3):
        """إشعار نجاح"""
        formatted = f"✅ <b>نجاح</b>\n\n{message}"
        await NotificationManager.send_notification(bot, chat_id, formatted, duration)
    
    @staticmethod
    async def send_error_notification(bot: Bot, chat_id: int, message: str, duration: int = 3):
        """إشعار خطأ"""
        formatted = f"❌ <b>خطأ</b>\n\n{message}"
        await NotificationManager.send_notification(bot, chat_id, formatted, duration)
    
    @staticmethod
    async def send_warning_notification(bot: Bot, chat_id: int, message: str, duration: int = 3):
        """إشعار تحذير"""
        formatted = f"⚠️ <b>تحذير</b>\n\n{message}"
        await NotificationManager.send_notification(bot, chat_id, formatted, duration)
    
    @staticmethod
    async def send_profile_notification(
        bot: Bot,
        chat_id: int,
        user_id: int,
        username: str,
        first_name: str,
        level: int,
        balance: int,
        messages: int,
        warnings: int,
        fines: int,
        titles: list,
        duration: int = 3
    ):
        """إشعار الملف الشخصي المتطور"""
        
        titles_text = '\n'.join([f"• {title}" for title in titles]) if titles else "لا يوجد"
        
        formatted = f"""
👤 <b>{first_name}</b>
└ @{username if username else 'لا يوجد'}

━━━━━━━━━━━━━━━━
📊 <b>الإحصائيات</b>
• المستوى: <b>{level}</b>
• الرصيد: <b>{balance:,.0f} 💰</b>
• الرسائل: <b>{messages:,}</b>

━━━━━━━━━━━━━━━━
⚠️ <b>العقوبات</b>
• التحذيرات: <b>{warnings}</b>
• الخصومات: <b>{fines}</b>

━━━━━━━━━━━━━━━━
🏷️ <b>الألقاب</b>
{titles_text}
"""
        await NotificationManager.send_notification(bot, chat_id, formatted, duration)
