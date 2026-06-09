from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class OwnerKeyboards:
    
    @staticmethod
    def main_panel() -> InlineKeyboardMarkup:
        """لوحة التحكم الرئيسية"""
        keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="owner_stats"),
             InlineKeyboardButton("⚙️ إعدادات الأنظمة", callback_data="owner_settings")],
            [InlineKeyboardButton("👥 إدارة الأعضاء", callback_data="owner_users"),
             InlineKeyboardButton("🛡️ إدارة الحماية", callback_data="owner_protection")],
            [InlineKeyboardButton("🎮 إدارة الألعاب", callback_data="owner_games"),
             InlineKeyboardButton("🛒 إدارة السوق", callback_data="owner_market")],
            [InlineKeyboardButton("🎖️ إدارة الأوسمة", callback_data="owner_badges"),
             InlineKeyboardButton("🤖 الردود التلقائية", callback_data="owner_autoreply")],
            [InlineKeyboardButton("🏆 المسابقات", callback_data="owner_contests"),
             InlineKeyboardButton("📦 النسخ الاحتياطي", callback_data="owner_backup")],
            [InlineKeyboardButton("👑 إدارة المشرفين", callback_data="owner_admins"),
             InlineKeyboardButton("📢 إشعار للمجموعة", callback_data="owner_broadcast")],
            [InlineKeyboardButton("📜 السجلات", callback_data="owner_logs"),
             InlineKeyboardButton("🔄 إعادة تشغيل", callback_data="owner_restart")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def settings_panel() -> InlineKeyboardMarkup:
        """لوحة إعدادات الأنظمة"""
        keyboard = [
            [InlineKeyboardButton("🏆 نظام المستوى", callback_data="toggle_level"),
             InlineKeyboardButton("🎮 نظام الألعاب", callback_data="toggle_games")],
            [InlineKeyboardButton("🛒 نظام السوق", callback_data="toggle_market"),
             InlineKeyboardButton("🛡️ نظام الحماية", callback_data="toggle_protection")],
            [InlineKeyboardButton("⭐ المكافآت اليومية", callback_data="toggle_daily"),
             InlineKeyboardButton("🏅 نظام الأوسمة", callback_data="toggle_badges")],
            [InlineKeyboardButton("🤖 الردود الذكية", callback_data="toggle_autoreply"),
             InlineKeyboardButton("🎯 نظام المسابقات", callback_data="toggle_contests")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def users_panel(page: int = 0, users: list = None) -> InlineKeyboardMarkup:
        """لوحة إدارة الأعضاء (5 أعضاء في كل صفحة)"""
        keyboard = []
        
        if users:
            for user in users[page*5:(page+1)*5]:
                name = user['first_name'][:20]
                keyboard.append([InlineKeyboardButton(
                    f"👤 {name}", 
                    callback_data=f"user_{user['user_id']}"
                )])
        
        # أزرار التنقل
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⏪ السابق", callback_data=f"users_page_{page-1}"))
        if users and len(users) > (page+1)*5:
            nav_buttons.append(InlineKeyboardButton("التالي ⏩", callback_data=f"users_page_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع للرئيسية", callback_data="owner_back")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def user_control_panel(user_id: int, user_data: dict) -> InlineKeyboardMarkup:
        """لوحة التحكم بعضو معين"""
        keyboard = [
            [InlineKeyboardButton("💰 تعديل الرصيد", callback_data=f"edit_balance_{user_id}"),
             InlineKeyboardButton("🏷️ إضافة لقب", callback_data=f"add_title_{user_id}")],
            [InlineKeyboardButton("🎖️ منح وسام", callback_data=f"give_badge_{user_id}"),
             InlineKeyboardButton("⚠️ تحذير", callback_data=f"warn_user_{user_id}")],
            [InlineKeyboardButton("🔇 كتم", callback_data=f"mute_user_{user_id}"),
             InlineKeyboardButton("🚫 حظر", callback_data=f"ban_user_{user_id}")],
            [InlineKeyboardButton("👑 رفع مشرف", callback_data=f"make_admin_{user_id}"),
             InlineKeyboardButton("📊 الإحصائيات", callback_data=f"user_stats_{user_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_users")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def protection_panel() -> InlineKeyboardMarkup:
        """لوحة إعدادات الحماية"""
        keyboard = [
            [InlineKeyboardButton("🔗 منع الروابط", callback_data="protect_links"),
             InlineKeyboardButton("🤖 منع البوتات", callback_data="protect_bots")],
            [InlineKeyboardButton("📝 منع إعادة التوجيه", callback_data="protect_forward"),
             InlineKeyboardButton("🚫 الكلمات الممنوعة", callback_data="forbidden_words")],
            [InlineKeyboardButton("💧 مكافحة السبام", callback_data="anti_flood"),
             InlineKeyboardButton("📏 طول الرسالة", callback_data="max_length")],
            [InlineKeyboardButton("➕ إضافة كلمة ممنوعة", callback_data="add_forbidden_word"),
             InlineKeyboardButton("➖ حذف كلمة ممنوعة", callback_data="remove_forbidden_word")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def market_panel() -> InlineKeyboardMarkup:
        """لوحة إدارة السوق"""
        keyboard = [
            [InlineKeyboardButton("➕ إضافة عنصر", callback_data="add_market_item"),
             InlineKeyboardButton("➖ حذف عنصر", callback_data="remove_market_item")],
            [InlineKeyboardButton("💰 تعديل السعر", callback_data="edit_price"),
             InlineKeyboardButton("📋 قائمة العناصر", callback_data="list_items")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def games_panel() -> InlineKeyboardMarkup:
        """لوحة إدارة الألعاب"""
        keyboard = [
            [InlineKeyboardButton("🎲 حجر ورقة مقص", callback_data="game_rps"),
             InlineKeyboardButton("🔢 تخمين الرقم", callback_data="game_guess")],
            [InlineKeyboardButton("🎯 نرد", callback_data="game_dice"),
             InlineKeyboardButton("🎰 سلوتس", callback_data="game_slots")],
            [InlineKeyboardButton("💰 تعديل المكافأة", callback_data="edit_game_reward"),
             InlineKeyboardButton("📊 إحصائيات الألعاب", callback_data="game_stats")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def contests_panel() -> InlineKeyboardMarkup:
        """لوحة إدارة المسابقات"""
        keyboard = [
            [InlineKeyboardButton("➕ إنشاء مسابقة", callback_data="create_contest"),
             InlineKeyboardButton("📋 المسابقات النشطة", callback_data="active_contests")],
            [InlineKeyboardButton("🏆 إنهاء مسابقة", callback_data="end_contest"),
             InlineKeyboardButton("📊 نتائج المسابقة", callback_data="contest_results")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def auto_reply_panel() -> InlineKeyboardMarkup:
        """لوحة الردود التلقائية"""
        keyboard = [
            [InlineKeyboardButton("➕ إضافة رد", callback_data="add_auto_reply"),
             InlineKeyboardButton("📋 قائمة الردود", callback_data="list_auto_replies")],
            [InlineKeyboardButton("➖ حذف رد", callback_data="delete_auto_reply"),
             InlineKeyboardButton("🔄 تفعيل/تعطيل", callback_data="toggle_auto_reply")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def backup_panel() -> InlineKeyboardMarkup:
        """لوحة النسخ الاحتياطي"""
        keyboard = [
            [InlineKeyboardButton("📦 إنشاء نسخة احتياطية", callback_data="create_backup"),
             InlineKeyboardButton("📋 قائمة النسخ", callback_data="list_backups")],
            [InlineKeyboardButton("🔄 استعادة نسخة", callback_data="restore_backup"),
             InlineKeyboardButton("🗑️ حذف نسخة", callback_data="delete_backup")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admins_panel(admins: list) -> InlineKeyboardMarkup:
        """لوحة إدارة المشرفين"""
        keyboard = []
        for admin in admins:
            keyboard.append([InlineKeyboardButton(
                f"👑 {admin['first_name']}", 
                callback_data=f"admin_{admin['user_id']}"
            )])
        keyboard.append([InlineKeyboardButton("➕ إضافة مشرف", callback_data="add_admin")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")])
        return InlineKeyboardMarkup(keyboard)


class GameKeyboards:
    """أزرار الألعاب"""
    
    @staticmethod
    def rps_game() -> InlineKeyboardMarkup:
        """أزرار لعبة حجر ورقة مقص"""
        keyboard = [
            [
                InlineKeyboardButton("🗻 حجر", callback_data="game_rps_rock"),
                InlineKeyboardButton("📜 ورقة", callback_data="game_rps_paper"),
                InlineKeyboardButton("✂️ مقص", callback_data="game_rps_scissors")
            ],
            [InlineKeyboardButton("❌ إلغاء", callback_data="game_cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def guess_game() -> InlineKeyboardMarkup:
        """أزرار لعبة تخمين الرقم"""
        keyboard = [
            [
                InlineKeyboardButton("1", callback_data="guess_1"),
                InlineKeyboardButton("2", callback_data="guess_2"),
                InlineKeyboardButton("3", callback_data="guess_3"),
                InlineKeyboardButton("4", callback_data="guess_4"),
                InlineKeyboardButton("5", callback_data="guess_5")
            ],
            [
                InlineKeyboardButton("6", callback_data="guess_6"),
                InlineKeyboardButton("7", callback_data="guess_7"),
                InlineKeyboardButton("8", callback_data="guess_8"),
                InlineKeyboardButton("9", callback_data="guess_9"),
                InlineKeyboardButton("10", callback_data="guess_10")
            ],
            [InlineKeyboardButton("❌ إلغاء", callback_data="game_cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def games_menu() -> InlineKeyboardMarkup:
        """قائمة الألعاب الرئيسية"""
        keyboard = [
            [InlineKeyboardButton("🗻 حجر ورقة مقص 🗻", callback_data="game_rps_menu")],
            [InlineKeyboardButton("🎲 تخمين الرقم 🎲", callback_data="game_guess_menu")],
            [InlineKeyboardButton("🎯 نرد 🎯", callback_data="game_dice_menu")],
            [InlineKeyboardButton("🎰 سلوتس 🎰", callback_data="game_slots_menu")],
            [InlineKeyboardButton("❌ إغلاق", callback_data="game_close")]
        ]
        return InlineKeyboardMarkup(keyboard)
