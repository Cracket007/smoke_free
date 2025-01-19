from datetime import datetime
import schedule
import time
from threading import Thread
import signal
import sys
import os
import socket
import urllib3
from dotenv import load_dotenv

from bot_config import bot, TIMEZONE
from commands import register_commands
from message_handler import send_status, send_voice_status
from database import get_all_users, get_user, init_db

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

# Настройки подключения
socket.setdefaulttimeout(30)
urllib3.disable_warnings()

running = True

def signal_handler(sig, frame):
    global running
    print('\nЗавершение работы бота...')
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def send_notification(user_id):
    """Отправка уведомления конкретному пользователю"""
    try:
        user = get_user(user_id)
        if user and user.get('quit_date'):
            quit_time = datetime.strptime(user['quit_date'], "%Y-%m-%d %H:%M")
            # Отправляем голосовое сообщение
            send_voice_status(user['chat_id'], quit_time)
    except Exception as e:
        print(f"Ошибка отправки уведомления пользователю {user_id}: {e}")

def setup_schedules():
    """Настройка расписания для каждого пользователя"""
    schedule.clear()
    users = get_all_users()
    print(f"\n🔄 Настройка расписания уведомлений...")
    for user in users:
        if user.get('notify_time'):
            schedule.every().day.at(user['notify_time']).do(
                send_notification, user['user_id']
            )
            print(f"✅ Установлено уведомление для {user['name']} на {user['notify_time']} (Киев)")

def run_scheduler():
    last_check = {}  # Словарь для отслеживания последней отправки
    while running:
        try:
            now = datetime.now(TIMEZONE)
            current_time = now.strftime('%H:%M')
            print(f"⏰ Проверка расписания: {current_time}")
            
            # Проверяем всех пользователей
            users = get_all_users()
            for user in users:
                notify_time = user.get('notify_time')
                user_id = user['user_id']
                
                if notify_time and notify_time == current_time:
                    # Проверяем, не отправляли ли мы уже уведомление в эту минуту
                    last_notify = last_check.get(user_id, '')
                    if last_notify != current_time:
                        print(f"🔔 Отправка уведомления для {user['name']} в {current_time}")
                        send_notification(user_id)
                        last_check[user_id] = current_time
            
        except Exception as e:
            print(f"❌ Ошибка планировщика: {e}")
        time.sleep(40)  # Проверяем каждые 40 секунд

def run_bot():
    reconnect_delay = 15
    max_delay = 300
    
    while running:
        try:
            print("🔄 Попытка подключения к Telegram...")
            bot.polling(
                none_stop=True,
                interval=3,
                timeout=60,
                long_polling_timeout=60,
                allowed_updates=["message", "callback_query"]
            )
        except (socket.timeout, urllib3.exceptions.TimeoutError) as e:
            print(f"⚠️ Таймаут соединения: {e}")
            time.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, max_delay)
        except (ConnectionError, ConnectionResetError, ConnectionAbortedError) as e:
            print(f"⚠️ Ошибка соединения: {e}")
            time.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, max_delay)
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            time.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, max_delay)
        else:
            reconnect_delay = 15
            print("✅ Соединение восстановлено")

def main():
    init_db()
    print("База данных инициализирована")
    
    register_commands(bot)
    
    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    run_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
