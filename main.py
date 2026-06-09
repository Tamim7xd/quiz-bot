#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters
)

from config import Config
from database import Database
from handlers.user_commands import UserCommands
from handlers.admin_commands import AdminCommands
from handlers.owner_panel import OwnerPanel
from systems.protection_system import ProtectionSystem
from systems.welcome_system import WelcomeSystem

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# حالات المحادثة
WAITING_ADD_ADMIN = 1
WAITING_ADD_ITEM = 2
WAITING_ADD_PRICE = 3
WAITING_ADD_REPLY_KEYWORD = 4
WAITING_ADD_REPLY_RESPONSE = 5
WAITING_ADD_FORBIDDEN_WORD = 6
WAITING_BROADCAST = 7
WAITING_CREATE_CONTEST = 8

class AdvancedBot:
    def __init__(self):
        self.config = Config
        self.db = Database()
        self.user_commands = UserCommands(self.db)
        self.admin_commands = AdminCommands(self.db)
        self.owner_panel = OwnerPanel(self.db)
        self.protection_system = ProtectionSystem(self.db, self.config)
        self.welcome_system = WelcomeSystem(self.db, self.config)
        
        self.application = None
    
    async def error_handler(self, update, context):
        """معالجة الأخطاء"""
        logger.error(f"حدث خطأ: {context.error}")
        
        if update and update.effective_chat:
            await update.effective_chat.send_message(
                "⚠️ حدث خطأ في البوت، تم تسجيل الخطأ وسيتم إصلاحه قريباً"
            )
    
    def setup_handlers(self):
        """تسجيل جميع المعالجات"""
        
        # أوامر المستخدمين
        self.application.add_handler(CommandHandler("start", self.user_commands.start_command))
        self.application.add_handler(CommandHandler("حساب", self.user_commands.profile_command))
        self.application.add_handler(CommandHandler("ملفي", self.user_commands.profile_command))
        self.application.add_handler(CommandHandler("العاب", self.user_commands.games_command))
        self.application.add_handler(CommandHandler("لعبة", self.user_commands.games_command))
        self.application.add_handler(CommandHandler("العب", self.user_commands.games_command))
        self.application.add_handler(CommandHandler("سوق", self.user_commands.market_command))
        self.application.add_handler(CommandHandler("ماركت", self.user_commands.market_command))
        self.application.add_handler(CommandHandler("شراء", self.user_commands.buy_command))
        self.application.add_handler(CommandHandler("يومي", self.user_commands.daily_command))
        self.application.add_handler(CommandHandler("مستوى", self.user_commands.level_command))
        self.application.add_handler(CommandHandler("توب", self.user_commands.top_command))
        
        # أوامر المشرفين
        self.application.add_handler(CommandHandler("تحذير", self.admin_commands.warn_command))
        self.application.add_handler(CommandHandler("خصم", self.admin_commands.fine_command))
        self.application.add_handler(CommandHandler("كتم", self.admin_commands.mute_command))
        self.application.add_handler(CommandHandler("مكافأة", self.admin_commands.reward_command))
        self.application.add_handler(CommandHandler("مكافاة", self.admin_commands.reward_command))
        self.application.add_handler(CommandHandler("طرد", self.admin_commands.kick_command))
        self.application.add_handler(CommandHandler("حظر", self.admin_commands.ban_command))
        self.application.add_handler(CommandHandler("عقوبات", self.admin_commands.punishments_command))
        
        # أوامر المالك
        self.application.add_handler(CommandHandler("لوحة", self.owner_panel.owner_panel_command))
        self.application.add_handler(CommandHandler("owner", self.owner_panel.owner_panel_command))
        
        # معالج الأزرار
        self.application.add_handler(CallbackQueryHandler(self.owner_panel.owner_callback, pattern="^owner_"))
        self.application.add_handler(CallbackQueryHandler(self.owner_panel.owner_callback, pattern="^toggle_"))
        self.application.add_handler(CallbackQueryHandler(self.owner_panel.owner_callback, pattern="^users_page_"))
        self.application.add_handler(CallbackQueryHandler(self.owner_panel.owner_callback, pattern="^user_"))
        self.application.add_handler(CallbackQueryHandler(self.user_commands.game_callback, pattern="^game_"))
        self.application.add_handler(CallbackQueryHandler(self.user_commands.game_callback, pattern="^guess_"))
        
        # معالج المحادثات للإضافة
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.owner_panel.owner_callback, pattern="^add_market_item$"),
                CallbackQueryHandler(self.owner_panel.owner_callback, pattern="^add_auto_reply$"),
                CallbackQueryHandler(self.owner_panel.owner_callback, pattern="^add_forbidden_word$"),
            ],
            states={
                WAITING_ADD_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.owner_panel.handle_add_item)],
                WAITING_ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.owner_panel.handle_add_item)],
                WAITING_ADD_REPLY_KEYWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.owner_panel.handle_add_reply)],
                WAITING_ADD_REPLY_RESPONSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.owner_panel.handle_add_reply)],
                WAITING_ADD_FORBIDDEN_WORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.owner_panel.handle_add_forbidden_word)],
            },
            fallbacks=[CommandHandler("cancel", self.owner_panel.handle_add_item)],
        )
        self.application.add_handler(conv_handler)
        
        # معالج الإشعارات
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.owner_panel.handle_broadcast))
        
        # معالج الرسائل العادية (لنظام الحماية والردود)
        self.application.add_handler(MessageHandler(filters.ALL, self.user_commands.handle_message))
        
        # معالج الأخطاء
        self.application.add_error_handler(self.error_handler)
    
    async def initialize(self):
        """تهيئة البوت"""
        if not self.config.BOT_TOKEN:
            logger.error("❌ لم يتم إدخال توكن البوت! يرجى إدخال BOT_TOKEN في ملف .env")
            return False
        
        if self.config.OWNER_ID == 0:
            logger.error("❌ لم يتم إدخال معرف المالك! يرجى إدخال OWNER_ID في ملف .env")
            return False
        
        if self.config.GROUP_ID == 0:
            logger.error("❌ لم يتم إدخال معرف المجموعة! يرجى إدخال GROUP_ID في ملف .env")
            return False
        
        logger.info("✅ تم تهيئة البوت بنجاح")
        logger.info(f"📊 المالك: {self.config.OWNER_ID}")
        logger.info(f"👥 المجموعة: {self.config.GROUP_ID}")
        
        return True
    
    async def run(self):
        """تشغيل البوت"""
        if not await self.initialize():
            return
        
        # إنشاء التطبيق
        self.application = Application.builder().token(self.config.BOT_TOKEN).build()
        
        # تسجيل المعالجات
        self.setup_handlers()
        
        logger.info("🚀 بدء تشغيل البوت...")
        
        # بدء البوت
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("✅ البوت يعمل الآن!")
        
        # إبقاء البوت قيد التشغيل
        await asyncio.Event().wait()


def main():
    """الدالة الرئيسية"""
    bot = AdvancedBot()
    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
