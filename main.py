from datetime import datetime
import schedule
import time
from threading import Thread
import signal
import sys
import telebot

from bot_config import bot, users, TOKEN
from commands import register_commands
from message_handler import send_status

# Флаг для корректного завершения
running = True
bot_thread = None

def signal_handler(sig, frame):
    global running
    print('\nЗавершение работы бота...')
    running = False
    bot.stop_polling()
    if bot_thread and bot_thread.is_alive():
        bot_thread.join()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Регистрируем команды
register_commands(bot)

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
        time.sleep(60)  # Проверяем расписание каждую минуту

def main():
    global bot_thread
    
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    while True:
        try:
            print("Бот запущен...")
            bot.polling(none_stop=True, interval=1)
        except telebot.apihelper.ApiException as e:
            print(f"Ошибка API Telegram: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"Критическая ошибка: {e}")
            time.sleep(5)
            continue

if __name__ == "__main__":
    print("Бот запущен и готов к работе!")
    try:
        main()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
