import time
import schedule
from threading import Thread
import requests
from bot_config import bot
from commands import register_commands
from database import init_db
from scheduler import setup_schedules

def delete_webhook():
    """Удаляем вебхук, если он был установлен"""
    try:
        bot.delete_webhook()
        print("✅ Вебхук удален")
    except Exception as e:
        print(f"❌ Ошибка удаления вебхука: {str(e)}")

def run_scheduler():
    """Запуск планировщика в бесконечном цикле"""
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)
        except Exception as e:
            print(f"❌ Ошибка планировщика: {str(e)}")
            time.sleep(5)

def main():
    try:
        # Удаляем старый вебхук
        delete_webhook()
        time.sleep(1)  # Ждем немного
        
        # Инициализируем базу данных
        init_db()
        print("✅ База данных инициализирована")
        
        # Регистрируем команды
        register_commands(bot)
        print("✅ Команды зарегистрированы")
        
        # Настраиваем расписание
        setup_schedules()
        print("✅ Расписание настроено")
        
        # Запускаем планировщик в отдельном потоке
        scheduler_thread = Thread(target=run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        print("✅ Планировщик запущен")
        
        print("🚀 Бот запущен и готов к работе")
        
        # Запускаем бота с минимальным таймаутом
        bot.infinity_polling(timeout=10, long_polling_timeout=10)
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        raise

if __name__ == "__main__":
    main()
