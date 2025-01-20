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
from scheduler import setup_schedules

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
        print(f"🔔 Начинаем отправку уведомления для user_id: {user_id}")
        user = get_user(user_id)
        if user and user.get('quit_date'):
            print(f"✅ Найден пользователь: {user['name']}")
            quit_time = datetime.strptime(user['quit_date'], "%Y-%m-%d %H:%M")
            print(f"📅 Дата отказа: {quit_time}")
            send_voice_status(user['chat_id'], quit_time)
            print(f"✨ Уведомление отправлено для {user['name']}")
        else:
            print(f"⚠️ Пользователь не найден или нет даты отказа: {user_id}")
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления пользователю {user_id}: {e}")

def test_schedule():
    now = datetime.now(TIMEZONE)
    print(f"🎯 Тестовое срабатывание в {now.strftime('%H:%M:%S')}")

def setup_schedules():
    """Настройка расписания для каждого пользователя"""
    try:
        schedule.clear()
        users = get_all_users()
        print(f"\n🔄 Настройка расписания уведомлений...")
        
        # Добавляем тестовую задачу
        schedule.every().minute.do(test_schedule)
        print("✅ Добавлена тестовая задача (каждую минуту)")
        
        if not users:
            print("⚠️ Нет пользователей в базе данных")
            return
            
        for user in users:
            notify_time = user.get('notify_time')
            if notify_time:
                print(f"📋 Настройка для {user['name']}: {notify_time}")
                job = schedule.every().day.at(notify_time).do(send_notification, user['user_id'])
                print(f"✅ Установлено уведомление для {user['name']} на {notify_time} (Киев)")
                # Проверяем, когда будет следующий запуск
                next_run = job.next_run
                print(f"📅 Следующий запуск: {next_run}")
            else:
                print(f"⚠️ Не задано время уведомлений для {user['name']}")
                
        print(f"📊 Всего задач в планировщике: {len(schedule.jobs)}")
        
    except Exception as e:
        print(f"❌ Ошибка настройки расписания: {e}")

def run_bot():
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=bot.polling, kwargs={
        'none_stop': True,
        'interval': 3,
        'timeout': 60
    })
    bot_thread.daemon = True
    bot_thread.start()
    
    # Основной цикл для планировщика
    while running:
        try:
            schedule.run_pending()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        time.sleep(1)

def main():
    init_db()
    print("База данных инициализирована")
    
    register_commands(bot)
    setup_schedules()  # Добавляем настройку расписания
    run_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
