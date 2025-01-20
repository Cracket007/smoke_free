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

def main():
    init_db()
    print("База данных инициализирована")
    
    register_commands(bot)
    setup_schedules()
    run_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
