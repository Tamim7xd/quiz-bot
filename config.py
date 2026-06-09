import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # التوكنات والمعرفات
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    OWNER_ID = int(os.getenv('OWNER_ID', 0)) if os.getenv('OWNER_ID') else 0
    GROUP_ID = int(os.getenv('GROUP_ID', 0)) if os.getenv('GROUP_ID') else 0
    
    # ChatGPT
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    USE_CHATGPT = os.getenv('USE_CHATGPT', 'False').lower() == 'true'
    
    # النسخ الاحتياطي
    BACKUP_INTERVAL_HOURS = int(os.getenv('BACKUP_INTERVAL_HOURS', 24))
    BACKUP_PATH = os.getenv('BACKUP_PATH', 'backups/')
    
    # إعدادات الاقتصاد
    MESSAGE_REWARD = 10          # نقاط لكل رسالة
    GAME_WIN_REWARD = 2500       # مكافأة الفوز باللعبة
    DAILY_STREAK_REWARDS = {
        1: 500, 2: 600, 3: 700, 4: 800, 5: 900,
        6: 1000, 7: 2000, 14: 5000, 30: 10000
    }
    MIN_FINE = 1000
    MAX_FINE = 5000
    LEVEL_UP_BONUS = 500
    
    # إعدادات الحماية
    PROTECTION_SETTINGS = {
        'block_links': True,
        'block_bots': True,
        'block_forward': True,
        'max_message_length': 500,
        'anti_flood_count': 5,
        'anti_flood_seconds': 3
    }
    
    # الأوسمة المتاحة
    BADGES = {
        'old_member': {'icon': '🏆', 'name': 'عضو قديم', 'days': 180},
        'active_member': {'icon': '💬', 'name': 'عضو نشط', 'messages': 1000},
        'game_champion': {'icon': '🎮', 'name': 'بطل الألعاب', 'wins': 50},
        'vip': {'icon': '👑', 'name': 'VIP', 'balance': 50000},
        'helper': {'icon': '🤝', 'name': 'مساعد', 'helps': 100},
        'generous': {'icon': '💰', 'name': 'كريم', 'donations': 10000}
    }
    
    # تشغيل/إيقاف الأنظمة
    SYSTEM_STATUS = {
        'level_system': True,
        'game_system': True,
        'market_system': True,
        'protection_system': True,
        'daily_system': True,
        'contests_system': True,
        'badges_system': True,
        'auto_reply_system': True,
        'welcome_system': True,
        'ai_system': False
    }
    
    # إعدادات الوقت
    NOTIFICATION_DURATION = 3  # ثواني
    
    # الأوامر العربية
    ARABIC_COMMANDS = {
        'حساب': 'profile',
        'ملفي': 'profile',
        'العاب': 'games',
        'لعبة': 'games',
        'العب': 'games',
        'سوق': 'market',
        'ماركت': 'market',
        'تحذير': 'warn',
        'خصم': 'fine',
        'كتم': 'mute',
        'مكافأة': 'reward',
        'مكافاة': 'reward',
        'طرد': 'kick',
        'حظر': 'ban',
        'عقوبات': 'punishments',
        'يومي': 'daily',
        'مستوى': 'level',
        'توب': 'top'
    }
