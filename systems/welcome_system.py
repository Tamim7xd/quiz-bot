from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from typing import Optional

from database import Database
from config import Config
from utils import NotificationManager

class WelcomeSystem:
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.welcome_message = """
🎉 <b>مرحباً بك {user_name}!</b>

نرحب بك في مجموعتنا 🏠

📋 <b>قوانين المجموعة:</b>
• احترام الجميع
• عدم إرسال الروابط
• عدم السب أو الشتم
• الالتزام بالآداب العامة

💡 <b>نصائح:</b>
• استخدم <code>حساب</code> لعرض ملفك الشخصي
• استخدم <code>العاب</code> للعب وربح النقود
• استخدم <code>يومي</code> للحصول على مكافأتك اليومية

🌟 <b>استمتع معنا!</b>
"""
    
    async def send_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """إرسال رسالة ترحيب للأعضاء الجدد"""
        if not self.config.SYSTEM_STATUS.get('welcome_system', True):
            return
        
        message = update.message
        
        for new_member in message.new_chat_members:
            # تجاهل الترحيب بالبوت نفسه
            if new_member.id == context.bot.id:
                continue
            
            # تجاهل البوتات الأخرى
            if new_member.is_bot:
                continue
            
            # تسجيل المستخدم الجديد في قاعدة البيانات
            if not self.db.get_user(new_member.id):
                self.db.create_user(
                    new_member.id,
                    new_member.username,
                    new_member.first_name,
                    new_member.last_name or ''
                )
            
            # تنسيق رسالة الترحيب
            welcome_text = self.welcome_message.format(
                user_name=new_member.first_name
            )
            
            # إرسال الترحيب
            await NotificationManager.send_success_notification(
                message.bot,
                message.chat.id,
                welcome_text,
                duration=10  # يختفي بعد 10 ثواني
            )
    
    async def set_custom_welcome(self, message: str, admin_id: int) -> bool:
        """تخصيص رسالة الترحيب"""
        if admin_id != self.config.OWNER_ID:
            return False
        
        self.welcome_message = message
        return True
    
    def get_welcome_message(self) -> str:
        """الحصول على رسالة الترحيب الحالية"""
        return self.welcome_message
