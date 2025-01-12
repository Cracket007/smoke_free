from datetime import datetime
from bot_config import bot, users
from message_handler import send_status

def register_commands(bot):
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if str(user_id) not in users:
            users[str(user_id)] = {
                "name": message.from_user.first_name,
                "chat_id": chat_id,
                "quit_date": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            bot.reply_to(message, "Добро пожаловать! Вы зарегистрированы. Ваша дата отказа от курения установлена на текущий момент.")
        else:
            bot.reply_to(message, "Вы уже зарегистрированы!")

    @bot.message_handler(commands=['setdate'])
    def handle_setdate(message):
        try:
            user_id = str(message.from_user.id)
            if user_id not in users:
                bot.reply_to(message, "Сначала зарегистрируйтесь с помощью /start")
                return
                
            date_str = message.text.replace('/setdate', '').strip()
            datetime.strptime(date_str, "%Y-%m-%d %H:%M")  # Проверяем формат
            
            users[user_id]["quit_date"] = date_str
            bot.reply_to(message, f"Дата отказа от курения установлена на {date_str}")
        except ValueError:
            bot.reply_to(message, "Неверный формат даты. Используйте: YYYY-MM-DD HH:MM")

    @bot.message_handler(commands=['status'])
    def handle_status(message):
        user_id = str(message.from_user.id)
        if user_id not in users:
            bot.reply_to(message, "Сначала зарегистрируйтесь с помощью /start")
            return
            
        user = users[user_id]
        quit_time = datetime.strptime(user["quit_date"], "%Y-%m-%d %H:%M")
        send_status(user["chat_id"], quit_time) 