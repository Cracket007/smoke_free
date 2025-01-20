import time
import schedule
from threading import Thread
from bot_config import bot
from commands import register_commands
from database import init_db
from scheduler import setup_schedules

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
        
        # Запускаем бота
        bot.infinity_polling(timeout=20)
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        raise

if __name__ == "__main__":
    main()
