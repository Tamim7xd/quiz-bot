from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import json
import os
from datetime import datetime

from database import Database
from utils import NotificationManager
from keyboards.owner_keyboards import OwnerKeyboards
from config import Config

# حالات المحادثة
WAITING_ADD_ADMIN = 1
WAITING_ADD_ITEM = 2
WAITING_ADD_PRICE = 3
WAITING_ADD_REPLY_KEYWORD = 4
WAITING_ADD_REPLY_RESPONSE = 5
WAITING_ADD_FORBIDDEN_WORD = 6
WAITING_ADD_BADGE = 7
WAITING_CREATE_CONTEST = 8

class OwnerPanel:
    def __init__(self, db: Database):
        self.db = db
    
    async def owner_panel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """فتح لوحة تحكم المالك"""
        user_id = update.effective_user.id
        
        if user_id != Config.OWNER_ID:
            await update.message.reply_text("⛔ هذا الأمر خاص بمالك البوت فقط")
            return
        
        await update.message.reply_text(
            "👑 <b>لوحة تحكم المالك</b>\n\n"
            "مرحباً بك في لوحة التحكم الشاملة\n"
            "اختر الإعداد الذي تريد تعديله:",
            parse_mode='HTML',
            reply_markup=OwnerKeyboards.main_panel()
        )
    
    async def owner_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة أزرار لوحة المالك"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        if user_id != Config.OWNER_ID:
            await query.message.reply_text("⛔ هذا الأمر خاص بمالك البوت فقط")
            return
        
        data = query.data
        
        # القائمة الرئيسية
        if data == "owner_stats":
            await self.show_stats(query, context)
        
        elif data == "owner_settings":
            await query.message.edit_text(
                "⚙️ <b>إعدادات الأنظمة</b>\n\n"
                "اختر النظام الذي تريد تشغيله أو إيقافه:",
                parse_mode='HTML',
                reply_markup=OwnerKeyboards.settings_panel()
            )
        
        elif data == "owner_users":
            await self.show_users(query, context)
        
        elif data == "owner_protection":
            await query.message.edit_text(
                "🛡️ <b>إدارة الحماية</b>\n\n"
                "اختر الإعداد الذي تريد تعديله:",
                parse_mode='HTML',
                reply_markup=OwnerKeyboards.protection_panel()
            )
        
        elif data == "owner_games":
            await query.message.edit_text(
                "🎮 <b>إدارة الألعاب</b>\n\n"
                "اختر الإعداد الذي تريد تعديله:",
                parse_mode='HTML',
                reply_markup=OwnerKeyboards.games_panel()
            )
        
        elif data == "owner_market":
            await query.message.edit_text(
                "🛒 <b>إدارة السوق</b>\n\n"
                "اختر الإعداد الذي تريد تعديله:",
                parse_mode='HTML',
                reply_markup=OwnerKeyboards.market_panel()
            )
        
        elif data == "owner_badges":
            await self.show_badges(query, context)
        
        elif data == "owner_autoreply":
            await self.show_auto_reply_panel(query, context)
        
        elif data == "owner_contests":
            await query.message.edit_text(
                "🏆 <b>إدارة المسابقات</b>\n\n"
                "اختر الإعداد الذي تريد تعديله:",
                parse_mode='HTML',
                reply_markup=OwnerKeyboards.contests_panel()
            )
        
        elif data == "owner_backup":
            await self.show_backup_panel(query, context)
        
        elif data == "owner_admins":
            await self.show_admins(query, context)
        
        elif data == "owner_broadcast":
            context.user_data['broadcast'] = True
            await query.message.edit_text(
                "📢 <b>إرسال إشعار للمجموعة</b>\n\n"
                "أرسل الرسالة التي تريد إرسالها إلى المجموعة:\n"
                "(يمكنك استخدام HTML للـتنسيق)\n\n"
                "<i>أرسل /cancel للإلغاء</i>",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        elif data == "owner_logs":
            await self.show_logs(query, context)
        
        elif data == "owner_restart":
            await query.message.edit_text("🔄 جاري إعادة تشغيل البوت...")
            os._exit(0)
        
        elif data == "owner_back":
            await query.message.edit_text(
                "👑 <b>لوحة تحكم المالك</b>\n\n"
                "مرحباً بك في لوحة التحكم الشاملة\n"
                "اختر الإعداد الذي تريد تعديله:",
                parse_mode='HTML',
                reply_markup=OwnerKeyboards.main_panel()
            )
        
        # تبديل حالة الأنظمة
        elif data.startswith("toggle_"):
            await self.toggle_system(query, data)
        
        # إدارة الأعضاء
        elif data.startswith("users_page_"):
            page = int(data.split("_")[2])
            await self.show_users(query, context, page)
        
        elif data.startswith("user_"):
            user_id = int(data.split("_")[1])
            await self.show_user_control(query, context, user_id)
        
        # إدارة الحماية
        elif data == "forbidden_words":
            await self.show_forbidden_words(query, context)
        
        elif data == "add_forbidden_word":
            context.user_data['adding_word'] = True
            await query.message.edit_text(
                "➕ <b>إضافة كلمة ممنوعة</b>\n\n"
                "أرسل الكلمة التي تريد منعها:\n\n"
                "<i>أرسل /cancel للإلغاء</i>",
                parse_mode='HTML'
            )
            return WAITING_ADD_FORBIDDEN_WORD
        
        # إدارة السوق
        elif data == "add_market_item":
            context.user_data['adding_item'] = True
            await query.message.edit_text(
                "➕ <b>إضافة عنصر جديد للسوق</b>\n\n"
                "أرسل اسم العنصر (مثال: لقب ذهبي):\n\n"
                "<i>أرسل /cancel للإلغاء</i>",
                parse_mode='HTML'
            )
            return WAITING_ADD_ITEM
        
        # إدارة الردود التلقائية
        elif data == "add_auto_reply":
            context.user_data['adding_reply'] = True
            await query.message.edit_text(
                "➕ <b>إضافة رد تلقائي</b>\n\n"
                "أرسل الكلمة المفتاحية:\n\n"
                "<i>أرسل /cancel للإلغاء</i>",
                parse_mode='HTML'
            )
            return WAITING_ADD_REPLY_KEYWORD
        
        # إدارة المسابقات
        elif data == "create_contest":
            context.user_data['creating_contest'] = True
            await query.message.edit_text(
                "🏆 <b>إنشاء مسابقة جديدة</b>\n\n"
                "أرسل اسم المسابقة:\n\n"
                "<i>أرسل /cancel للإلغاء</i>",
                parse_mode='HTML'
            )
            return WAITING_CREATE_CONTEST
    
    async def show_stats(self, query, context):
        """عرض إحصائيات النظام"""
        stats = self.db.get_server_stats()
        
        stats_text = f"""
📊 <b>إحصائيات البوت</b>

👥 <b>المستخدمون</b>
• إجمالي المستخدمين: <b>{stats['total_users']:,}</b>
• إجمالي الرسائل: <b>{stats['total_messages']:,}</b>

💰 <b>الاقتصاد</b>
• إجمالي الرصيد المتداول: <b>{stats['total_balance']:,} 💰</b>

⚠️ <b>العقوبات</b>
• إجمالي التحذيرات: <b>{stats['total_warnings']}</b>

━━━━━━━━━━━━━━━━━━
🤖 <b>حالة الأنظمة</b>
"""
        for system, status in Config.SYSTEM_STATUS.items():
            emoji = "✅" if status else "❌"
            stats_text += f"• {emoji} {system}: {'مفعل' if status else 'معطل'}\n"
        
        await query.message.edit_text(stats_text, parse_mode='HTML')
        await query.message.reply_text(
            "🔙 للرجوع اضغط الزر أدناه",
            reply_markup=OwnerKeyboards.main_panel()
        )
    
    async def toggle_system(self, query, data):
        """تشغيل/إيقاف نظام"""
        system = data.replace("toggle_", "")
        
        system_map = {
            'level': 'level_system',
            'games': 'game_system',
            'market': 'market_system',
            'protection': 'protection_system',
            'daily': 'daily_system',
            'badges': 'badges_system',
            'autoreply': 'auto_reply_system',
            'contests': 'contests_system'
        }
        
        system_key = system_map.get(system, system)
        
        if system_key in Config.SYSTEM_STATUS:
            Config.SYSTEM_STATUS[system_key] = not Config.SYSTEM_STATUS[system_key]
            status = "مُفعل ✅" if Config.SYSTEM_STATUS[system_key] else "معطل ❌"
            
            await query.answer(f"تم {status}")
            await query.message.edit_text(
                f"⚙️ تم تغيير حالة النظام إلى: {status}",
                reply_markup=OwnerKeyboards.settings_panel()
            )
    
    async def show_users(self, query, context, page=0):
        """عرض قائمة المستخدمين"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, first_name, username FROM users ORDER BY join_date DESC LIMIT 100')
            users = cursor.fetchall()
        
        users_list = [dict(u) for u in users]
        
        if not users_list:
            await query.message.edit_text("لا يوجد مستخدمين مسجلين بعد")
            return
        
        # عرض 5 مستخدمين في كل صفحة
        start = page * 5
        end = start + 5
        page_users = users_list[start:end]
        
        text = "👥 <b>قائمة الأعضاء</b>\n\n"
        for i, user in enumerate(page_users, start + 1):
            text += f"{i}. {user['first_name']}\n"
            text += f"   └ @{user['username'] if user['username'] else 'لا يوجد'}\n"
        
        await query.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=OwnerKeyboards.users_panel(page, users_list)
        )
    
    async def show_user_control(self, query, context, target_id):
        """عرض لوحة التحكم بعضو معين"""
        user_data = self.db.get_user(target_id)
        if not user_data:
            await query.message.edit_text("المستخدم غير موجود")
            return
        
        text = f"""
👤 <b>التحكم في العضو</b>

<b>المعلومات:</b>
• الاسم: {user_data['first_name']}
• اليوزر: @{user_data['username'] if user_data['username'] else 'لا يوجد'}
• المستوى: {user_data['level']}
• الرصيد: {user_data['balance']:,} 💰
• التحذيرات: {user_data['warnings']}
"""
        await query.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=OwnerKeyboards.user_control_panel(target_id, user_data)
        )
    
    async def show_forbidden_words(self, query, context):
        """عرض الكلمات الممنوعة"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT word FROM forbidden_words')
            words = cursor.fetchall()
        
        if not words:
            text = "🚫 لا توجد كلمات ممنوعة حالياً"
        else:
            text = "🚫 <b>الكلمات الممنوعة</b>\n\n"
            for w in words:
                text += f"• {w['word']}\n"
        
        await query.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=OwnerKeyboards.protection_panel()
        )
    
    async def show_badges(self, query, context):
        """عرض الأوسمة"""
        text = "🎖️ <b>الأوسمة المتاحة</b>\n\n"
        
        for badge_key, badge_info in Config.BADGES.items():
            text += f"{badge_info['icon']} <b>{badge_info['name']}</b>\n"
            if 'days' in badge_info:
                text += f"   └ المطلوب: {badge_info['days']} يوم\n"
            elif 'messages' in badge_info:
                text += f"   └ المطلوب: {badge_info['messages']} رسالة\n"
            elif 'wins' in badge_info:
                text += f"   └ المطلوب: {badge_info['wins']} فوز\n"
            text += "\n"
        
        await query.message.edit_text(text, parse_mode='HTML')
        await query.message.reply_text(
            "🔙 للرجوع اضغط الزر أدناه",
            reply_markup=OwnerKeyboards.main_panel()
        )
    
    async def show_auto_reply_panel(self, query, context):
        """عرض لوحة الردود التلقائية"""
        replies = self.db.get_all_auto_replies()
        
        if replies:
            text = "🤖 <b>الردود التلقائية</b>\n\n"
            for r in replies[:10]:
                text += f"• <b>{r['keyword']}</b> → {r['response'][:30]}...\n"
        else:
            text = "🤖 لا توجد ردود تلقائية حالياً"
        
        await query.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=OwnerKeyboards.auto_reply_panel()
        )
    
    async def show_admins(self, query, context):
        """عرض قائمة المشرفين"""
        admin_ids = self.db.get_all_admins()
        admins = []
        
        for aid in admin_ids:
            user_data = self.db.get_user(aid)
            if user_data:
                admins.append(user_data)
        
        if not admins:
            text = "👑 لا يوجد مشرفين معينين حالياً\n(باستثناء المالك)"
        else:
            text = "👑 <b>قائمة المشرفين</b>\n\n"
            for admin in admins:
                text += f"• {admin['first_name']}\n"
                text += f"  └ @{admin['username'] if admin['username'] else 'لا يوجد'}\n"
        
        await query.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=OwnerKeyboards.admins_panel(admins)
        )
    
    async def show_backup_panel(self, query, context):
        """عرض لوحة النسخ الاحتياطي"""
        # إنشاء مجلد النسخ إذا لم يكن موجوداً
        os.makedirs(Config.BACKUP_PATH, exist_ok=True)
        
        backups = os.listdir(Config.BACKUP_PATH) if os.path.exists(Config.BACKUP_PATH) else []
        
        if backups:
            text = "📦 <b>النسخ الاحتياطية المتاحة</b>\n\n"
            for b in backups[-5:]:
                size = os.path.getsize(os.path.join(Config.BACKUP_PATH, b)) / 1024
                text += f"• {b} ({size:.1f} KB)\n"
        else:
            text = "📦 لا توجد نسخ احتياطية حالياً"
        
        await query.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=OwnerKeyboards.backup_panel()
        )
    
    async def show_logs(self, query, context):
        """عرض السجلات"""
        log_file = "bot_database.db"
        
        if os.path.exists(log_file):
            size = os.path.getsize(log_file) / 1024
            text = f"📜 <b>معلومات قاعدة البيانات</b>\n\n"
            text += f"• الملف: {log_file}\n"
            text += f"• الحجم: {size:.1f} KB\n"
            text += f"• تاريخ التعديل: {datetime.fromtimestamp(os.path.getmtime(log_file)).strftime('%Y-%m-%d %H:%M')}\n\n"
            text += "<i>يمكنك تصدير البيانات من لوحة النسخ الاحتياطي</i>"
        else:
            text = "لا توجد سجلات متاحة"
        
        await query.message.edit_text(
            text,
            parse_mode='HTML',
            reply_markup=OwnerKeyboards.main_panel()
        )
    
    async def handle_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة إرسال الإشعار"""
        if context.user_data.get('broadcast'):
            message_text = update.message.text
            
            if message_text == '/cancel':
                context.user_data['broadcast'] = False
                await update.message.reply_text("❌ تم إلغاء الإشعار")
                return
            
            await update.message.reply_text("📢 جاري إرسال الإشعار...")
            
            try:
                await context.bot.send_message(
                    chat_id=Config.GROUP_ID,
                    text=message_text,
                    parse_mode='HTML'
                )
                await update.message.reply_text("✅ تم إرسال الإشعار بنجاح")
            except Exception as e:
                await update.message.reply_text(f"❌ فشل الإرسال: {str(e)}")
            
            context.user_data['broadcast'] = False
    
    # ==================== دوال إضافة العناصر ====================
    
    async def handle_add_item(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة إضافة عنصر للسوق"""
        if context.user_data.get('adding_item'):
            name = update.message.text
            
            if name == '/cancel':
                context.user_data['adding_item'] = False
                await update.message.reply_text("❌ تم إلغاء الإضافة")
                return
            
            context.user_data['item_name'] = name
            context.user_data['waiting_price'] = True
            context.user_data['adding_item'] = False
            
            await update.message.reply_text(
                f"💰 تم حفظ اسم العنصر: {name}\n\n"
                "الآن أرسل سعر العنصر:"
            )
            return WAITING_ADD_PRICE
        
        elif context.user_data.get('waiting_price'):
            try:
                price = int(update.message.text)
            except ValueError:
                await update.message.reply_text("❌ السعر يجب أن يكون رقماً")
                return WAITING_ADD_PRICE
            
            name = context.user_data['item_name']
            
            with self.db.get_connection() as conn:
                conn.execute('''
                    INSERT INTO market_items (item_name, item_icon, price)
                    VALUES (?, '🎁', ?)
                ''', (name, price))
            
            context.user_data['waiting_price'] = False
            context.user_data['item_name'] = None
            
            await update.message.reply_text(f"✅ تم إضافة العنصر {name} بسعر {price:,} 💰")
            return
    
    async def handle_add_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة إضافة رد تلقائي"""
        if context.user_data.get('adding_reply'):
            keyword = update.message.text
            
            if keyword == '/cancel':
                context.user_data['adding_reply'] = False
                await update.message.reply_text("❌ تم إلغاء الإضافة")
                return
            
            context.user_data['reply_keyword'] = keyword
            context.user_data['adding_reply'] = False
            context.user_data['waiting_response'] = True
            
            await update.message.reply_text(
                f"🔑 تم حفظ الكلمة المفتاحية: {keyword}\n\n"
                "الآن أرسل الرد التلقائي:"
            )
            return WAITING_ADD_REPLY_RESPONSE
        
        elif context.user_data.get('waiting_response'):
            response = update.message.text
            
            if response == '/cancel':
                context.user_data['waiting_response'] = False
                await update.message.reply_text("❌ تم إلغاء الإضافة")
                return
            
            keyword = context.user_data['reply_keyword']
            self.db.add_auto_reply(keyword, response, update.effective_user.id)
            
            context.user_data['waiting_response'] = False
            context.user_data['reply_keyword'] = None
            
            await update.message.reply_text(f"✅ تم إضافة الرد التلقائي:\n\nكلمة: {keyword}\nرد: {response}")
            return
    
    async def handle_add_forbidden_word(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة إضافة كلمة ممنوعة"""
        if context.user_data.get('adding_word'):
            word = update.message.text.lower()
            
            if word == '/cancel':
                context.user_data['adding_word'] = False
                await update.message.reply_text("❌ تم إلغاء الإضافة")
                return
            
            self.db.add_forbidden_word(word, update.effective_user.id)
            context.user_data['adding_word'] = False
            
            await update.message.reply_text(f"✅ تم إضافة الكلمة الممنوعة: {word}")
            return
