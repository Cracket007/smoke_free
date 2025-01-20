import sqlite3
from datetime import datetime
import pytz

# Устанавливаем киевский часовой пояс
TIMEZONE = pytz.timezone('Europe/Kiev')

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Проверяем существование колонки notifications_enabled
    c.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'notifications_enabled' not in columns:
        # Добавляем колонку если её нет
        c.execute('ALTER TABLE users ADD COLUMN notifications_enabled BOOLEAN DEFAULT TRUE')
        print("✅ Добавлена колонка notifications_enabled")
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            chat_id INTEGER,
            quit_date TEXT,
            notify_time TEXT DEFAULT '15:00',
            notifications_enabled BOOLEAN DEFAULT TRUE
        )
    ''')
    conn.commit()
    conn.close()

def save_user(user_id: str, name: str, chat_id: int, quit_date: str = None, notify_time: str = None, notifications_enabled: bool = True):
    """Сохранение или обновление пользователя"""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        print(f"\n🔄 Сохранение пользователя:")
        print(f"👤 ID: {user_id}")
        print(f"📛 Имя: {name}")
        print(f"💬 Chat ID: {chat_id}")
        print(f"📅 Дата отказа: {quit_date}")
        print(f"⏰ Время уведомлений: {notify_time}")
        print(f"🔔 Уведомления включены: {notifications_enabled}")
        
        if notify_time:
            # Проверяем формат времени
            hours, minutes = map(int, notify_time.split(':'))
            if not (0 <= hours < 24 and 0 <= minutes < 60):
                raise ValueError("Неверный формат времени")
                
        c.execute('''
            INSERT OR REPLACE INTO users (user_id, name, chat_id, quit_date, notify_time, notifications_enabled)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, name, chat_id, quit_date, notify_time, notifications_enabled))
        
        conn.commit()
        print(f"✅ Пользователь успешно сохранен в БД")
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователя в БД: {str(e)}")
        print(f"🔍 Детали ошибки: {type(e).__name__}")
    finally:
        conn.close()

def get_user(user_id: str):
    """Получение данных пользователя"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return {
            'user_id': user[0],
            'name': user[1],
            'chat_id': user[2],
            'quit_date': user[3],
            'notify_time': user[4],
            'notifications_enabled': user[5]
        }
    return None

def get_all_users():
    """Получение всех пользователей"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users = c.fetchall()
    conn.close()
    return [{
        'user_id': user[0],
        'name': user[1],
        'chat_id': user[2],
        'quit_date': user[3],
        'notify_time': user[4],
        'notifications_enabled': user[5]
    } for user in users] 