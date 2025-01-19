import sqlite3
from datetime import datetime
import pytz

# Устанавливаем киевский часовой пояс
TIMEZONE = pytz.timezone('Europe/Kiev')

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            chat_id INTEGER,
            quit_date TEXT,
            notify_time TEXT DEFAULT '15:00'
        )
    ''')
    conn.commit()
    conn.close()

def save_user(user_id: str, name: str, chat_id: int, quit_date: str = None, notify_time: str = None):
    """Сохранение или обновление пользователя"""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        if notify_time:
            # Проверяем формат времени
            hours, minutes = map(int, notify_time.split(':'))
            if not (0 <= hours < 24 and 0 <= minutes < 60):
                raise ValueError("Неверный формат времени")
                
        c.execute('''
            INSERT OR REPLACE INTO users (user_id, name, chat_id, quit_date, notify_time)
            VALUES (?, ?, ?, ?, COALESCE(?, '15:00'))
        ''', (user_id, name, chat_id, quit_date, notify_time))
        
        conn.commit()
        print(f"✅ Сохранено время уведомлений {notify_time} для пользователя {name}")
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователя: {e}")
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
            'notify_time': user[4]
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
        'notify_time': user[4]
    } for user in users] 