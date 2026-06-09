import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = 'bot_database.db'):
        self.db_path = db_path
        self.init_all_tables()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_all_tables(self):
        """إنشاء جميع الجداول المطلوبة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # جدول المستخدمين الأساسي
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    join_date TIMESTAMP,
                    last_active TIMESTAMP,
                    messages_count INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    xp INTEGER DEFAULT 0,
                    balance INTEGER DEFAULT 0,
                    warnings INTEGER DEFAULT 0,
                    fines_count INTEGER DEFAULT 0,
                    total_fines INTEGER DEFAULT 0,
                    badges TEXT DEFAULT '[]',
                    titles TEXT DEFAULT '[]',
                    daily_streak INTEGER DEFAULT 0,
                    last_daily TIMESTAMP,
                    total_daily_collected INTEGER DEFAULT 0,
                    games_won INTEGER DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    helps_count INTEGER DEFAULT 0,
                    donations_given INTEGER DEFAULT 0,
                    is_muted INTEGER DEFAULT 0,
                    mute_until TIMESTAMP,
                    is_banned INTEGER DEFAULT 0,
                    warning_details TEXT DEFAULT '[]'
                )
            ''')
            
            # جدول العقوبات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS punishments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    admin_id INTEGER,
                    punishment_type TEXT,
                    reason TEXT,
                    amount INTEGER,
                    duration TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # جدول التحذيرات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    admin_id INTEGER,
                    reason TEXT,
                    created_at TIMESTAMP
                )
            ''')
            
            # جدول الكتم
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mutes (
                    user_id INTEGER PRIMARY KEY,
                    admin_id INTEGER,
                    reason TEXT,
                    duration TEXT,
                    until TIMESTAMP,
                    created_at TIMESTAMP
                )
            ''')
            
            # جدول الألعاب
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_sessions (
                    user_id INTEGER PRIMARY KEY,
                    game_type TEXT,
                    game_data TEXT,
                    created_at TIMESTAMP
                )
            ''')
            
            # جدول السوق
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT UNIQUE,
                    item_icon TEXT,
                    price INTEGER,
                    stock INTEGER DEFAULT -1,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # جدول المشتريات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    item_id INTEGER,
                    purchase_date TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES market_items (id)
                )
            ''')
            
            # جدول المسابقات (17)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contests (
                    contest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    contest_type TEXT,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    prize_amount INTEGER,
                    status TEXT DEFAULT 'active',
                    winners TEXT DEFAULT '[]',
                    participants TEXT DEFAULT '[]',
                    scores TEXT DEFAULT '{}',
                    created_by INTEGER,
                    question TEXT,
                    correct_answer TEXT,
                    current_round INTEGER DEFAULT 1
                )
            ''')
            
            # جدول الأوسمة (19)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_badges (
                    user_id INTEGER,
                    badge_name TEXT,
                    awarded_date TIMESTAMP,
                    awarded_by INTEGER,
                    PRIMARY KEY (user_id, badge_name)
                )
            ''')
            
            # جدول الردود التلقائية (24)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auto_replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT UNIQUE,
                    response TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_by INTEGER,
                    created_at TIMESTAMP
                )
            ''')
            
            # جدول الكلمات الممنوعة
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forbidden_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT UNIQUE,
                    action TEXT DEFAULT 'delete'
                )
            ''')
            
            # جدول المشرفين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    added_by INTEGER,
                    added_date TIMESTAMP,
                    permissions TEXT DEFAULT '[]'
                )
            ''')
            
            # إضافة الأوسمة الافتراضية
            self.init_default_badges()
            
            # إضافة عناصر السوق الافتراضية
            self.init_default_market()
            
            # إضافة كلمات ممنوعة افتراضية
            self.init_default_forbidden_words()
    
    def init_default_badges(self):
        """إضافة الأوسمة الافتراضية"""
        cursor = self.get_connection().__enter__().cursor()
        default_badges = [
            ('🏆', 'عضو قديم', 'مرور 180 يوم على انضمامك', 'days', 180),
            ('💬', 'عضو نشط', 'إرسال 1000 رسالة', 'messages', 1000),
            ('🎮', 'بطل الألعاب', 'الفوز في 50 لعبة', 'wins', 50),
            ('👑', 'VIP', 'امتلاك 50000 نقطة', 'balance', 50000),
            ('🤝', 'مساعد', 'مساعدة 100 عضو', 'helps', 100),
            ('💰', 'كريم', 'تبرع بمبلغ 10000 نقطة', 'donations', 10000)
        ]
        for icon, name, desc, req_type, req_value in default_badges:
            cursor.execute('''
                INSERT OR IGNORE INTO user_badges (badge_name, badge_icon, badge_description, requirement_type, requirement_value)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, icon, desc, req_type, req_value))
    
    def init_default_market(self):
        """إضافة عناصر السوق الافتراضية"""
        cursor = self.get_connection().__enter__().cursor()
        default_items = [
            ('🌟', 'نجمة ذهبية', 5000),
            ('🎭', 'لقب مميز', 10000),
            ('💎', 'عضو ماسي', 25000),
            ('👑', 'لقب ملكي', 50000)
        ]
        for icon, name, price in default_items:
            cursor.execute('''
                INSERT OR IGNORE INTO market_items (item_icon, item_name, price)
                VALUES (?, ?, ?)
            ''', (icon, name, price))
    
    def init_default_forbidden_words(self):
        """إضافة كلمات ممنوعة افتراضية"""
        cursor = self.get_connection().__enter__().cursor()
        default_words = ['كس', 'عير', 'زبار', 'قحبة', 'منيك', 'خول', 'شرموطة']
        for word in default_words:
            cursor.execute('INSERT OR IGNORE INTO forbidden_words (word) VALUES (?)', (word,))
    
    # ==================== دوال المستخدمين ====================
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """الحصول على بيانات المستخدم"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def create_user(self, user_id: int, username: str, first_name: str, last_name: str = '') -> Dict:
        """إنشاء مستخدم جديد"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, join_date, last_active, balance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, now, now, 1000))
            return self.get_user(user_id)
    
    def update_user_activity(self, user_id: int):
        """تحديث نشاط المستخدم"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET messages_count = messages_count + 1, last_active = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
    
    def add_xp(self, user_id: int, amount: int) -> Tuple[int, bool]:
        """إضافة نقاط خبرة وتحقق من رفع المستوى"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT xp, level FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                return (0, False)
            
            new_xp = row['xp'] + amount
            current_level = row['level']
            new_level = current_level
            leveled_up = False
            
            # معادلة رفع المستوى: 100 * level
            while new_xp >= current_level * 100:
                new_xp -= current_level * 100
                current_level += 1
                leveled_up = True
            
            if leveled_up:
                new_level = current_level
                cursor.execute('''
                    UPDATE users SET xp = ?, level = ?, balance = balance + ?
                    WHERE user_id = ?
                ''', (new_xp, new_level, 500, user_id))
            else:
                cursor.execute('UPDATE users SET xp = ? WHERE user_id = ?', (new_xp, user_id))
            
            return (new_level, leveled_up)
    
    def update_balance(self, user_id: int, amount: int) -> int:
        """تحديث الرصيد (amount موجب للإضافة، سالب للخصم)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row['balance'] if row else 0
    
    def get_balance(self, user_id: int) -> int:
        """الحصول على الرصيد"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row['balance'] if row else 0
    
    # ==================== دوال التحذيرات ====================
    
    def add_warning(self, user_id: int, admin_id: int, reason: str = '') -> int:
        """إضافة تحذير للمستخدم"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # إضافة التحذير
            cursor.execute('''
                INSERT INTO warnings (user_id, admin_id, reason, created_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, admin_id, reason, now))
            
            # تحديث عدد التحذيرات في جدول المستخدمين
            cursor.execute('''
                UPDATE users SET warnings = warnings + 1,
                warning_details = json_insert(COALESCE(warning_details, '[]'), '$[#]', json_object('admin', ?, 'reason', ?, 'date', ?))
                WHERE user_id = ?
            ''', (admin_id, reason, now, user_id))
            
            cursor.execute('SELECT warnings FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row['warnings'] if row else 0
    
    def get_warnings(self, user_id: int) -> List[Dict]:
        """الحصول على تحذيرات المستخدم"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT w.*, u.first_name as admin_name
                FROM warnings w
                LEFT JOIN users u ON w.admin_id = u.user_id
                WHERE w.user_id = ?
                ORDER BY w.created_at DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def clear_warnings(self, user_id: int):
        """مسح جميع تحذيرات المستخدم"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM warnings WHERE user_id = ?', (user_id,))
            cursor.execute('UPDATE users SET warnings = 0, warning_details = "[]" WHERE user_id = ?', (user_id,))
    
    # ==================== دوال الكتم ====================
    
    def mute_user(self, user_id: int, admin_id: int, duration_seconds: int, reason: str = '') -> bool:
        """كتم مستخدم لفترة محددة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            until = (datetime.now() + timedelta(seconds=duration_seconds)).isoformat()
            cursor.execute('''
                INSERT OR REPLACE INTO mutes (user_id, admin_id, reason, duration, until, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, admin_id, reason, str(duration_seconds), until, datetime.now().isoformat()))
            cursor.execute('UPDATE users SET is_muted = 1, mute_until = ? WHERE user_id = ?', (until, user_id))
            return True
    
    def unmute_user(self, user_id: int) -> bool:
        """فك الكتم عن مستخدم"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM mutes WHERE user_id = ?', (user_id,))
            cursor.execute('UPDATE users SET is_muted = 0, mute_until = NULL WHERE user_id = ?', (user_id,))
            return True
    
    def is_muted(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """التحقق إذا كان المستخدم مكتوماً"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT mute_until FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row and row['mute_until']:
                until = datetime.fromisoformat(row['mute_until'])
                if until > datetime.now():
                    return (True, until.isoformat())
                else:
                    self.unmute_user(user_id)
            return (False, None)
    
    # ==================== دوال الألعاب ====================
    
    def save_game_session(self, user_id: int, game_type: str, game_data: dict):
        """حفظ جلسة لعبة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO game_sessions (user_id, game_type, game_data, created_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, game_type, json.dumps(game_data), datetime.now().isoformat()))
    
    def get_game_session(self, user_id: int) -> Optional[Dict]:
        """الحصول على جلسة اللعبة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM game_sessions WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['game_data'] = json.loads(data['game_data'])
                return data
            return None
    
    def clear_game_session(self, user_id: int):
        """مسح جلسة اللعبة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM game_sessions WHERE user_id = ?', (user_id,))
    
    def add_game_win(self, user_id: int):
        """تسجيل فوز في لعبة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET games_won = games_won + 1, games_played = games_played + 1,
                balance = balance + ?
                WHERE user_id = ?
            ''', (2500, user_id))
    
    def add_game_loss(self, user_id: int):
        """تسجيل خسارة في لعبة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET games_played = games_played + 1 WHERE user_id = ?', (user_id,))
    
    # ==================== دوال السوق ====================
    
    def get_market_items(self) -> List[Dict]:
        """الحصول على جميع عناصر السوق"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM market_items WHERE is_active = 1')
            return [dict(row) for row in cursor.fetchall()]
    
    def purchase_item(self, user_id: int, item_id: int) -> bool:
        """شراء عنصر من السوق"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT price, item_name FROM market_items WHERE id = ?', (item_id,))
            item = cursor.fetchone()
            if not item:
                return False
            
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            if not user or user['balance'] < item['price']:
                return False
            
            # خصم الرصيد
            cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (item['price'], user_id))
            
            # إضافة اللقب للمستخدم
            cursor.execute('SELECT titles FROM users WHERE user_id = ?', (user_id,))
            titles = json.loads(cursor.fetchone()['titles'] or '[]')
            titles.append(item['item_name'])
            cursor.execute('UPDATE users SET titles = ? WHERE user_id = ?', (json.dumps(titles), user_id))
            
            # تسجيل الشراء
            cursor.execute('''
                INSERT INTO purchases (user_id, item_id, purchase_date)
                VALUES (?, ?, ?)
            ''', (user_id, item_id, datetime.now().isoformat()))
            
            return True
    
    def get_user_titles(self, user_id: int) -> List[str]:
        """الحصول على ألقاب المستخدم"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT titles FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return json.loads(row['titles']) if row and row['titles'] else []
    
    # ==================== دوال المكافآت اليومية (16) ====================
    
    def claim_daily(self, user_id: int) -> Dict:
        """صرف المكافأة اليومية"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT daily_streak, last_daily, balance FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if not row:
                return {'success': False, 'message': 'المستخدم غير موجود'}
            
            now = datetime.now()
            last_daily = datetime.fromisoformat(row['last_daily']) if row['last_daily'] else None
            
            if last_daily and (now - last_daily).days == 0:
                return {'success': False, 'message': 'لقد حصلت على مكافأتك اليومية بالفعل'}
            
            # حساب الستريك
            if last_daily and (now - last_daily).days == 1:
                new_streak = row['daily_streak'] + 1
            else:
                new_streak = 1
            
            # حساب المكافأة
            from config import Config
            reward = Config.DAILY_STREAK_REWARDS.get(new_streak, 500)
            
            # تحديث البيانات
            cursor.execute('''
                UPDATE users SET 
                    daily_streak = ?,
                    last_daily = ?,
                    balance = balance + ?,
                    total_daily_collected = total_daily_collected + ?
                WHERE user_id = ?
            ''', (new_streak, now.isoformat(), reward, reward, user_id))
            
            return {
                'success': True,
                'streak': new_streak,
                'reward': reward,
                'new_balance': row['balance'] + reward
            }
    
    # ==================== دوال المسابقات (17) ====================
    
    def create_contest(self, name: str, contest_type: str, duration_hours: int, prize: int, created_by: int) -> int:
        """إنشاء مسابقة جديدة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            end = now + timedelta(hours=duration_hours)
            cursor.execute('''
                INSERT INTO contests (name, contest_type, start_date, end_date, prize_amount, created_by, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            ''', (name, contest_type, now.isoformat(), end.isoformat(), prize, created_by))
            return cursor.lastrowid
    
    def get_active_contest(self) -> Optional[Dict]:
        """الحصول على المسابقة النشطة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute('''
                SELECT * FROM contests 
                WHERE status = 'active' AND start_date <= ? AND end_date > ?
                ORDER BY contest_id DESC LIMIT 1
            ''', (now, now))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_contest_participant(self, contest_id: int, user_id: int):
        """إضافة مشارك للمسابقة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT participants FROM contests WHERE contest_id = ?', (contest_id,))
            row = cursor.fetchone()
            if row:
                participants = json.loads(row['participants'] or '[]')
                if user_id not in participants:
                    participants.append(user_id)
                    cursor.execute('UPDATE contests SET participants = ? WHERE contest_id = ?', 
                                 (json.dumps(participants), contest_id))
    
    def update_contest_score(self, contest_id: int, user_id: int, score: int):
        """تحديث نقاط المشارك في المسابقة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT scores FROM contests WHERE contest_id = ?', (contest_id,))
            row = cursor.fetchone()
            if row:
                scores = json.loads(row['scores'] or '{}')
                scores[str(user_id)] = scores.get(str(user_id), 0) + score
                cursor.execute('UPDATE contests SET scores = ? WHERE contest_id = ?', 
                             (json.dumps(scores), contest_id))
    
    # ==================== دوال الأوسمة (19) ====================
    
    def award_badge(self, user_id: int, badge_name: str, awarded_by: int) -> bool:
        """منح وسام لمستخدم"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO user_badges (user_id, badge_name, awarded_date, awarded_by)
                VALUES (?, ?, ?, ?)
            ''', (user_id, badge_name, datetime.now().isoformat(), awarded_by))
            return cursor.rowcount > 0
    
    def get_user_badges(self, user_id: int) -> List[Dict]:
        """الحصول على أوسمة المستخدم"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.*, ub.awarded_date 
                FROM user_badges ub
                JOIN badges b ON ub.badge_name = b.badge_name
                WHERE ub.user_id = ?
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def check_and_award_auto_badges(self, user_id: int):
        """التحقق تلقائياً ومنح الأوسمة المستحقة"""
        user = self.get_user(user_id)
        if not user:
            return
        
        from config import Config
        for badge_key, badge_info in Config.BADGES.items():
            earned = False
            
            if 'days' in badge_info and user['join_date']:
                join_date = datetime.fromisoformat(user['join_date'])
                days_passed = (datetime.now() - join_date).days
                if days_passed >= badge_info['days']:
                    earned = True
            
            elif 'messages' in badge_info and user['messages_count'] >= badge_info['messages']:
                earned = True
            
            elif 'wins' in badge_info and user['games_won'] >= badge_info['wins']:
                earned = True
            
            elif 'balance' in badge_info and user['balance'] >= badge_info['balance']:
                earned = True
            
            if earned:
                self.award_badge(user_id, badge_info['name'], 0)  # 0 = نظام آلي
    
    # ==================== دوال الردود التلقائية (24) ====================
    
    def add_auto_reply(self, keyword: str, response: str, admin_id: int) -> bool:
        """إضافة رد تلقائي"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO auto_replies (keyword, response, created_by, created_at, is_active)
                VALUES (?, ?, ?, ?, 1)
            ''', (keyword.lower(), response, admin_id, datetime.now().isoformat()))
            return True
    
    def get_auto_reply(self, message: str) -> Optional[str]:
        """الحصول على رد تلقائي بناءً على الكلمة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT keyword, response FROM auto_replies WHERE is_active = 1')
            replies = cursor.fetchall()
            
            msg_lower = message.lower()
            for reply in replies:
                if reply['keyword'] in msg_lower:
                    return reply['response']
            return None
    
    def get_all_auto_replies(self) -> List[Dict]:
        """الحصول على جميع الردود التلقائية"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM auto_replies ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_auto_reply(self, keyword: str) -> bool:
        """حذف رد تلقائي"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM auto_replies WHERE keyword = ?', (keyword.lower(),))
            return cursor.rowcount > 0
    
    # ==================== دوال الكلمات الممنوعة ====================
    
    def is_forbidden_word(self, text: str) -> bool:
        """التحقق من وجود كلمات ممنوعة في النص"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT word FROM forbidden_words')
            words = cursor.fetchall()
            
            text_lower = text.lower()
            for word in words:
                if word['word'] in text_lower:
                    return True
            return False
    
    def add_forbidden_word(self, word: str, admin_id: int) -> bool:
        """إضافة كلمة ممنوعة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO forbidden_words (word) VALUES (?)', (word.lower(),))
            return cursor.rowcount > 0
    
    def remove_forbidden_word(self, word: str) -> bool:
        """حذف كلمة ممنوعة"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM forbidden_words WHERE word = ?', (word.lower(),))
            return cursor.rowcount > 0
    
    # ==================== دوال المشرفين ====================
    
    def is_admin(self, user_id: int) -> bool:
        """التحقق إذا كان المستخدم مشرفاً"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None
    
    def add_admin(self, user_id: int, added_by: int) -> bool:
        """إضافة مشرف جديد"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO admins (user_id, added_by, added_date)
                VALUES (?, ?, ?)
            ''', (user_id, added_by, datetime.now().isoformat()))
            return cursor.rowcount > 0
    
    def remove_admin(self, user_id: int) -> bool:
        """إزالة مشرف"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
            return cursor.rowcount > 0
    
    def get_all_admins(self) -> List[int]:
        """الحصول على جميع المشرفين"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM admins')
            return [row['user_id'] for row in cursor.fetchall()]
    
    # ==================== دوال إحصائيات ====================
    
    def get_top_users(self, limit: int = 10, sort_by: str = 'messages_count') -> List[Dict]:
        """
