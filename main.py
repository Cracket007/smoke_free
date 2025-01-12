from datetime import datetime
import schedule
import time
from threading import Thread
import signal
import sys

from bot_config import bot, users
from commands import register_commands
from message_handler import send_status

# Флаг для корректного завершения
running = True
bot_thread = None  # Добавляем глобальную переменную для потока бота

def signal_handler(sig, frame):
    """Обработчик сигнала Ctrl+C"""
    global running
    print('\nЗавершение работы бота...')
    running = False
    
    # Останавливаем бот
    bot.stop_polling()
    
    # Ждем завершения потока бота
    if bot_thread and bot_thread.is_alive():
        bot_thread.join()
    
    sys.exit(0)

# Регистрируем обработчик Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# Регистрируем команды
register_commands(bot)

# Scheduled notifications
def scheduled_notifications():
    for user_id, data in users.items():
        quit_time = datetime.strptime(data["quit_date"], "%Y-%m-%d %H:%M")
        send_status(data["chat_id"], quit_time)

# Schedule periodic notifications
schedule.every(6).hours.do(scheduled_notifications)

# Run the bot and scheduler
def run():
    while running:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    print("Бот запущен и готов к работе!")
    # Run the bot in a separate thread
    bot_thread = Thread(target=lambda: bot.polling(none_stop=True))
    bot_thread.daemon = True  # Делаем поток демоном
    bot_thread.start()
    
    try:
        run()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
