import time
import schedule
from threading import Thread
import requests
from bot_config import bot
from commands import register_commands
from database import init_db
from scheduler import setup_schedules

def main():
    try:
        # Полный сброс состояния
        reset_webhook()
        
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
        
        # Запускаем бота в режиме polling с минимальными таймаутами
        bot.infinity_polling(timeout=10, long_polling_timeout=5, restart_on_error=True)
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        raise

if __name__ == "__main__":
    main()
