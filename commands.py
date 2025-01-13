from datetime import datetime
from bot_config import bot, users
from message_handler import send_status
from telebot import types  # Добавим импорт

def register_commands(bot):
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if str(user_id) not in users:
            users[str(user_id)] = {
                "name": message.from_user.first_name,
                "chat_id": chat_id
            }
            
            # Создаем клавиатуру с кнопкой
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            status_button = types.KeyboardButton('Сколько я не курю?')
            keyboard.add(status_button)
            
            bot.reply_to(
                message, 
                "Добро пожаловать! Укажите дату отказа от курения в формате:\n"
                "ДД.ММ.ГГГГ\n"
                "Например: 07.01.2025",
                reply_markup=keyboard
            )
        else:
            bot.reply_to(message, "Вы уже зарегистрированы!")

    @bot.message_handler(func=lambda message: True)
    def handle_text(message):
        """Обработчик для текстовых сообщений"""
        try:
            user_id = str(message.from_user.id)
            if user_id not in users:
                bot.reply_to(message, "Сначала зарегистрируйтесь с помощью /start")
                return
            
            text = message.text.strip()
            
            # Проверяем нажатие кнопки или команду status
            if text == 'Сколько я не курю?' or text == '/status':
                if "quit_date" not in users[user_id]:
                    bot.reply_to(message, "Сначала укажите дату отказа от курения")
                    return
                user = users[user_id]
                quit_time = datetime.strptime(user["quit_date"], "%Y-%m-%d %H:%M")
                send_status(user["chat_id"], quit_time)
                return
            
            # Проверяем, является ли сообщение датой
            try:
                quit_date = datetime.strptime(text, "%d.%m.%Y")
                quit_date = quit_date.replace(hour=0, minute=0)
                users[user_id]["quit_date"] = quit_date.strftime("%Y-%m-%d %H:%M")
                bot.reply_to(message, f"Дата отказа от курения установлена на {text}")
                
            except ValueError:
                # Если это не дата и не команда, отправляем помощь
                bot.reply_to(
                    message, 
                    "Я могу помочь отслеживать время без курения.\n\n"
                    "Используйте:\n"
                    "• Кнопку 'Сколько я не курю?' или команду /status чтобы узнать ваш прогресс\n"
                    "• Отправьте дату в формате ДД.ММ.ГГГГ чтобы установить дату отказа от курения"
                )
            
        except Exception as e:
            bot.reply_to(message, f"Ошибка: {str(e)}")

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