from datetime import datetime
import schedule
import time
from threading import Thread
import signal
import sys
import telebot
import os
from dotenv import load_dotenv

from bot_config import bot, users
from commands import register_commands
from message_handler import send_status

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

# Флаг для корректного завершения
running = True

def signal_handler(sig, frame):
    global running
    print('\nЗавершение работы бота...')
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Ежедневные уведомления
def daily_notifications():
    print("Отправка ежедневных уведомлений...")
    for user_id, data in users.items():
        if "quit_date" in data:
            try:
                quit_time = datetime.strptime(data["quit_date"], "%Y-%m-%d %H:%M")
                send_status(data["chat_id"], quit_time)
            except Exception as e:
                print(f"Ошибка отправки уведомления пользователю {user_id}: {e}")

# Планировщик
schedule.every().day.at("15:00").do(daily_notifications)

def run_scheduler():
    while running:
        schedule.run_pending()
        time.sleep(60)

def main():
    # Регистрируем команды
    register_commands(bot)
    
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Основной цикл бота
    while running:
        try:
            print("Бот запущен...")
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(15)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
