from datetime import datetime
from bot_config import bot, TIMEZONE
from message_handler import send_status
from telebot import types
from database import save_user, get_user, get_all_users
from scheduler import setup_schedules

def register_commands(bot):
    # Сначала регистрируем все команды
    commands = [
        types.BotCommand("start", "Начать использование бота"),
        types.BotCommand("status", "Узнать, сколько вы не курите"),
        types.BotCommand("settime", "Настроить время уведомлений"),
        types.BotCommand("setdate", "Изменить дату отказа"),
        types.BotCommand("check", "Проверить настройки уведомлений"),
        types.BotCommand("help", "Показать справку"),
    ]
    bot.set_my_commands(commands)

    @bot.message_handler(commands=['start'])
    def handle_start(message):
        user_id = str(message.from_user.id)
        chat_id = message.chat.id
        name = message.from_user.first_name
        
        user = get_user(user_id)
        if not user:
            save_user(user_id, name, chat_id)
            
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            status_button = types.KeyboardButton('Сколько я не курю?')
            keyboard.add(status_button)
            
            welcome_text = (
                "✨ Привет! Рад познакомиться! 👋\n\n"
                "📅 Давай начнем с даты отказа от курения:\n"
                "• Формат: ДД.ММ.ГГГГ\n"
                "• Пример: 07.01.2025\n\n"
                "❓ Используй /help чтобы узнать все мои возможности"
            )
            
            bot.reply_to(message, welcome_text, reply_markup=keyboard)
        else:
            bot.reply_to(
                message, 
                "🌟 С возвращением!\n💫 Используй /help чтобы увидеть все команды"
            )

    @bot.message_handler(commands=['setdate'])
    def handle_setdate(message):
        try:
            user_id = str(message.from_user.id)
            user = get_user(user_id)
            if not user:
                bot.reply_to(message, "❗️ Сначала зарегистрируйтесь с помощью /start")
                return
                
            date_str = message.text.replace('/setdate', '').strip()
            if not date_str:
                bot.reply_to(
                    message, 
                    "❗️ Для начала укажи дату отказа от курения\n📅 Например: 19.01.2025"
                )
                return
                
            quit_date = datetime.strptime(date_str, "%d.%m.%Y")
            quit_date = quit_date.replace(hour=0, minute=0)
            
            save_user(user_id, user['name'], user['chat_id'], 
                     quit_date.strftime("%Y-%m-%d %H:%M"))
                     
            bot.reply_to(
                message, 
                f"🎉 Отлично! Дата отказа установлена на {date_str}\n\n"
                "✨ Что дальше:\n"
                "💫 Нажми 'Сколько я не курю?' для проверки прогресса\n"
                "⚡️ Настрой уведомления командой /settime"
            )
        except ValueError:
            bot.reply_to(
                message, 
                "❗️ Упс! Неверный формат даты\n\n"
                "📅 Используй формат: ДД.ММ.ГГГГ\n"
                "💫 Например: 19.01.2025"
            )

    @bot.message_handler(commands=['status'])
    def handle_status(message):
        user_id = str(message.from_user.id)
        user = get_user(user_id)
        if not user:
            bot.reply_to(message, "Сначала зарегистрируйтесь с помощью /start")
            return
            
        if not user.get('quit_date'):
            bot.reply_to(message, "Сначала укажите дату отказа от курения")
            return
            
        quit_time = datetime.strptime(user['quit_date'], "%Y-%m-%d %H:%M")
        send_status(user['chat_id'], quit_time)

    @bot.message_handler(commands=['settime'])
    def handle_settime(message):
        try:
            user_id = str(message.from_user.id)
            user = get_user(user_id)
            if not user:
                bot.reply_to(message, "❗️ Сначала зарегистрируйтесь с помощью /start")
                return
            
            if not user.get('quit_date'):
                bot.reply_to(
                    message, 
                    "❗️ Сначала укажите дату отказа от курения в формате ДД.ММ.ГГГГ\n"
                    "Например: 19.01.2025"
                )
                return
            
            # Создаем клавиатуру с кнопками времени
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
            times = ['09:00', '12:00', '15:00', '18:00', '21:00']
            buttons = [types.KeyboardButton(time) for time in times]
            markup.add(*buttons)
            
            # Добавляем кнопку возврата
            back_button = types.KeyboardButton('Сколько я не курю?')
            markup.add(back_button)
            
            current_time = user.get('notify_time', '15:00')
            bot.reply_to(
                message,
                f"⚡️ Текущее время уведомлений: {current_time}\n\n"
                "🕒 Выбери удобное время для уведомлений:\n"
                "• Нажмите на одну из кнопок\n"
                "• Или введите своё время в формате ЧЧ:ММ\n\n"
                "💫 Например: 10:30 или 20:00\n\n"
                "✨ Буду поддерживать тебя каждый день в выбранное время!"
            )
            
        except Exception as e:
            print(f"Ошибка в handle_settime: {e}")  # Добавим логирование
            bot.reply_to(message, f"❌ Ошибка: {str(e)}")

    @bot.message_handler(commands=['help'])
    def handle_help(message):
        help_text = (
            "✨ Мои команды:\n\n"
            "🔹 /start - Начать использование бота\n"
            "🔹 /status - Узнать, сколько вы не курите\n"
            "🔹 /settime - Настроить время уведомлений\n"
            "🔹 /setdate - Изменить дату отказа (ДД.ММ.ГГГГ)\n"
            "🔹 /check - Проверить настройки уведомлений\n"
            "🔹 /help - Показать это сообщение\n\n"
            "💫 Также ты можешь:\n"
            "• Использовать кнопку 'Сколько я не курю?' 🕒\n"
            "• Отправить новую дату отказа в формате ДД.ММ.ГГГГ 📅\n"
            "• Выбрать удобное время для уведомлений ⏰\n\n"
            "🌟 Я буду поддерживать тебя каждый день!\n"
            "💪 Вместе мы сможем все!"
        )
        bot.reply_to(message, help_text)

    @bot.message_handler(commands=['check'])
    def handle_check(message):
        try:
            user_id = str(message.from_user.id)
            user = get_user(user_id)
            if not user:
                bot.reply_to(message, "❗️ Сначала зарегистрируйтесь с помощью /start")
                return
            
            current_time = datetime.now(TIMEZONE)
            notify_time = user.get('notify_time', '15:00')
            
            # Определяем, будет ли уведомление сегодня или завтра
            notify_hours, notify_minutes = map(int, notify_time.split(':'))
            notify_datetime = current_time.replace(hour=notify_hours, minute=notify_minutes)
            
            if current_time > notify_datetime:
                next_notify = "завтра"
            else:
                next_notify = "сегодня"
            
            bot.reply_to(
                message,
                f"⏰ Текущее время (Киев): {current_time.strftime('%H:%M')}\n"
                f"�� Время уведомлений: {notify_time}\n"
                f"🔔 Следующее уведомление будет отправлено {next_notify} в {notify_time}"
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {str(e)}")

    @bot.message_handler(func=lambda message: True)
    def handle_text(message):
        try:
            user_id = str(message.from_user.id)
            user = get_user(user_id)
            
            if not user:
                bot.reply_to(message, "❗️ Сначала зарегистрируйтесь с помощью /start")
                return
            
            text = message.text.strip()
            
            # Проверяем формат времени (ЧЧ:ММ)
            if ':' in text and len(text) == 5:
                try:
                    hours, minutes = map(int, text.split(':'))
                    if 0 <= hours < 24 and 0 <= minutes < 60:
                        if not user.get('quit_date'):
                            bot.reply_to(
                                message,
                                "❗️ Сначала укажите дату отказа от курения в формате ДД.ММ.ГГГГ\n"
                                "Например: 19.01.2025"
                            )
                            return
                            
                        save_user(user_id, user['name'], user['chat_id'], 
                                user.get('quit_date'), text)
                        
                        # Перенастраиваем расписание после изменения времени
                        setup_schedules()
                        
                        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                        status_button = types.KeyboardButton('Сколько я не курю?')
                        keyboard.add(status_button)
                        
                        bot.reply_to(
                            message, 
                            f"�� Супер! Буду поддерживать тебя каждый день в {text}\n"
                            "✨ Время всегда можно изменить командой /settime",
                            reply_markup=keyboard
                        )
                        return
                except ValueError:
                    pass
            
            if text == 'Сколько я не курю?' or text == '/status':
                if not user.get('quit_date'):
                    bot.reply_to(message, "❗️ Сначала укажите дату отказа от курения")
                    return
                quit_time = datetime.strptime(user['quit_date'], "%Y-%m-%d %H:%M")
                send_status(user['chat_id'], quit_time)
                return
            
            try:
                quit_date = datetime.strptime(text, "%d.%m.%Y")
                quit_date = quit_date.replace(hour=0, minute=0)
                save_user(user_id, user['name'], user['chat_id'], 
                         quit_date.strftime("%Y-%m-%d %H:%M"))
                bot.reply_to(
                    message, 
                    f"📅 Дата отказа от курения установлена на {text}\n"
                    "Теперь вы можете:\n"
                    "• Узнать свой прогресс кнопкой 'Сколько я не курю?'\n"
                    "• Настроить время уведомлений командой /settime"
                )
                
            except ValueError:
                bot.reply_to(
                    message, 
                    "🌟 Привет! Я помогу отслеживать твой прогресс.\n\n"
                    "✨ Мои возможности:\n"
                    "🎯 Показываю твой прогресс\n"
                    "⏰ Отправляю ежедневные уведомления\n"
                    "🎤 Поддерживаю голосовыми сообщениями\n\n"
                    "📱 Как пользоваться:\n"
                    "💫 Нажми 'Сколько я не курю?' для проверки\n"
                    "📅 Отправь дату отказа (ДД.ММ.ГГГГ)\n"
                    "⚡️ /settime - настрой время уведомлений\n"
                    "❓ /help - все команды"
                )
            
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {str(e)}") 