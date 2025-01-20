from datetime import datetime
import schedule
import time
from threading import Thread
import signal
import sys
import os
from dotenv import load_dotenv

from bot_config import bot, TIMEZONE
from commands import register_commands
from message_handler import send_status, send_voice_status
from database import get_all_users, get_user, init_db
from scheduler import setup_schedules

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

running = True

def signal_handler(sig, frame):
    global running
    print('\nЗавершение работы бота...')
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

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

def run_scheduler():
    """Запуск планировщика в бесконечном цикле"""
    while True:
        try:
            print("🔄 Проверка расписания...")
            schedule.run_pending()
            time.sleep(30)  # Проверка каждые 30 секунд
        except Exception as e:
            print(f"❌ Ошибка планировщика: {str(e)}")
            time.sleep(5)

def keep_alive():
    """Поддержание работы планировщика"""
    while True:
        try:
            print("🔄 Обновление расписания...")
            setup_schedules()
            time.sleep(7200)  # Обновление каждые 2 часа
        except Exception as e:
            print(f"❌ Ошибка обновления расписания: {str(e)}")
            time.sleep(5)

def main():
    try:
        # Инициализируем базу данных
        init_db()
        
        # Регистрируем команды
        register_commands(bot)
        
        # Настраиваем начальное расписание
        setup_schedules()
        
        # Запускаем планировщик в отдельном потоке
        scheduler_thread = Thread(target=run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        # Запускаем поддержку расписания в отдельном потоке
        keeper_thread = Thread(target=keep_alive)
        keeper_thread.daemon = True
        keeper_thread.start()
        
        print("🚀 Бот запущен")
        # Запускаем бота в бесконечном цикле с обработкой ошибок
        while True:
            try:
                bot.infinity_polling(timeout=60, long_polling_timeout=60)
            except Exception as e:
                print(f"❌ Ошибка бота: {str(e)}")
                time.sleep(5)
                continue
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        raise

if __name__ == "__main__":
    main()
