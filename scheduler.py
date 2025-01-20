from datetime import datetime
import schedule
from bot_config import TIMEZONE
from database import get_all_users, get_user
from message_handler import send_voice_status

def send_notification(user_id):
    """Отправка уведомления конкретному пользователю"""
    try:
        user = get_user(user_id)
        if user and user.get('quit_date'):
            quit_time = datetime.strptime(user['quit_date'], "%Y-%m-%d %H:%M")
            quit_time = TIMEZONE.localize(quit_time)  # Добавляем часовой пояс
            now = datetime.now(TIMEZONE)
            
            # Проверяем, не в будущем ли дата
            if quit_time > now:
                print(f"❌ Пропуск уведомления - дата в будущем: {quit_time}")
                return
            
            send_voice_status(user['chat_id'], quit_time)
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

def setup_schedules():
    """Настройка расписания для каждого пользователя"""
    try:
        print("\n🔄 Настройка расписания уведомлений:")
        schedule.clear()
        users = get_all_users()
        
        if not users:
            print("❌ Нет пользователей для настройки уведомлений")
            return
            
        for user in users:
            notify_time = user.get('notify_time')
            notifications_enabled = user.get('notifications_enabled', True)
            print(f"\n👤 Пользователь: {user['name']}")
            print(f"⏰ Время уведомлений: {notify_time}")
            print(f"🔔 Статус уведомлений: {'включены' if notifications_enabled else 'выключены'}")
            
            if notify_time and notifications_enabled:
                schedule.every().day.at(notify_time).do(
                    send_notification, 
                    user_id=user['user_id']
                ).tag(user['user_id'])
                print(f"✅ Уведомление запланировано на {notify_time}")
            else:
                print("❌ Уведомления не настроены")
                
    except Exception as e:
        print(f"❌ Ошибка настройки расписания: {str(e)}")
        print(f"🔍 Детали ошибки: {type(e).__name__}") 