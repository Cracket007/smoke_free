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
            send_voice_status(user['chat_id'], quit_time)
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

def setup_schedules():
    """Настройка расписания для каждого пользователя"""
    try:
        schedule.clear()
        users = get_all_users()
        if not users:
            return
            
        now = datetime.now(TIMEZONE)
        
        for user in users:
            time = user.get('notify_time')
            if time:
                hours, minutes = map(int, time.split(':'))
                notify_time = now.replace(hour=hours, minute=minutes)
                
                schedule.every().day.at(time).do(
                    send_notification, 
                    user_id=user['user_id']
                ).tag(user['user_id'])
                
    except Exception as e:
        print(f"❌ Ошибка планировщика: {e}") 