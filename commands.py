from datetime import datetime
from bot_config import bot, TIMEZONE
from message_handler import send_status
from telebot import types
from database import save_user, get_user, get_all_users
from scheduler import setup_schedules

# В начале файла добавим словарь для хранения временных состояний
waiting_for_time = {}  # user_id -> future_date

def register_commands(bot):
    # Сначала регистрируем все команды
    commands = [
        types.BotCommand("start", "Начать использование бота"),
        types.BotCommand("status", "Узнать, сколько вы не курите"),
        types.BotCommand("setdate", "Изменить дату отказа"),
        types.BotCommand("settings", "Настройки уведомлений"),
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
            
            # Проверяем, не в будущем ли дата
            now = datetime.now(TIMEZONE)
            if quit_date > now:
                bot.reply_to(
                    message,
                    "❗️ Дата отказа не может быть в будущем\n"
                    "📅 Укажите сегодняшнюю или прошедшую дату"
                )
                return
            
            save_user(user_id, user['name'], user['chat_id'], 
                     quit_date.strftime("%Y-%m-%d %H:%M"))
                     
            bot.reply_to(
                message, 
                f"🎉 Отлично! Дата отказа установлена на {date_str}\n\n"
                "✨ Что дальше:\n"
                "💫 Нажми 'Сколько я не курю?' для проверки прогресса\n"
                "⚡️ Настрой уведомления командой /settings"
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

    @bot.message_handler(commands=['settings'])
    def handle_settings(message):
        try:
            user_id = str(message.from_user.id)
            user = get_user(user_id)
            if not user:
                bot.reply_to(message, "❗️ Сначала зарегистрируйтесь с помощью /start")
                return
            
            current_time = datetime.now(TIMEZONE)
            notify_time = user.get('notify_time', '15:00')
            notifications_enabled = user.get('notifications_enabled', True)
            
            # Создаем клавиатуру
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            times = ['09:00', '12:00', '15:00', '18:00', '21:00']
            time_buttons = [types.KeyboardButton(time) for time in times]
            on_button = types.KeyboardButton('🔔 Включить уведомления')
            off_button = types.KeyboardButton('🔕 Выключить уведомления')
            back_button = types.KeyboardButton('Сколько я не курю?')
            
            markup.add(*time_buttons)
            markup.add(on_button, off_button)
            markup.add(back_button)
            
            # Определяем статус следующего уведомления
            notify_hours, notify_minutes = map(int, notify_time.split(':'))
            notify_datetime = current_time.replace(hour=notify_hours, minute=notify_minutes)
            next_notify = "завтра" if current_time > notify_datetime else "сегодня"
            
            status = "включены ✅" if notifications_enabled else "выключены ❌"
            
            bot.reply_to(
                message,
                f"⚙️ Настройки уведомлений:\n\n"
                f"🔔 Статус: {status}\n"
                f"⏰ Время отправки: {notify_time}\n"
                f"📅 Следующее уведомление: {next_notify} в {notify_time}\n\n"
                "Выберите действие:\n"
                "• Нажмите на время для изменения\n"
                "• Или введите своё время в формате ЧЧ:ММ\n"
                "• Используйте кнопки для включения/выключения",
                reply_markup=markup
            )
            
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {str(e)}")

    @bot.message_handler(commands=['help'])
    def handle_help(message):
        help_text = (
            "✨ Мои команды:\n\n"
            "▫️ /start - Начать использование бота\n"
            "▫️ /status - Узнать, сколько вы не курите\n"
            "▫️ /setdate - Изменить дату отказа (ДД.ММ.ГГГГ)\n"
            "▫️ /settings - Настройки уведомлений\n"
            "▫️ /help - Показать это сообщение\n\n"
            "💫 Также ты можешь:\n"
            "🕒 Использовать кнопку 'Сколько я не курю?'\n"
            "📅 Отправить новую дату отказа в формате ДД.ММ.ГГГГ\n"
            "⏰ Выбрать удобное время для уведомлений\n\n"
            "💪 Вместе мы сможем все!"
        )
        bot.reply_to(message, help_text)

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
                        # Проверяем, ожидаем ли время от этого пользователя
                        if user_id in waiting_for_time:
                            future_date = waiting_for_time.pop(user_id)  # Удаляем состояние ожидания
                            
                            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                            status_button = types.KeyboardButton('Сколько я не курю?')
                            keyboard.add(status_button)
                            
                            bot.reply_to(
                                message,
                                f"😅 Функция напоминания о будущей дате ({future_date.strftime('%d.%m.%Y')}) "
                                f"в {text} не реализована.\n     Так как разработчику было впадло засорять базу данных и регистрировать планировщик задач.\n\n"
                                "💸Закинь лучше на сиги если есть пару капеек на крипте:\n"
                                "• TRC20: \nTLqypVzzWNuTSkfayS1W6rKKQYciSimxX5n\n"
                                "От души💋\n\n"
                                "А пока что укажите дату, когда вы уже бросили курить 😉",
                                reply_markup=keyboard
                            )
                            return
                        
                        # Проверяем, есть ли у пользователя будущая дата отказа
                        if user.get('quit_date'):
                            quit_time = datetime.strptime(user['quit_date'], "%Y-%m-%d %H:%M")
                            quit_time = TIMEZONE.localize(quit_time)
                            now = datetime.now(TIMEZONE)
                            
                            if quit_time > now:
                                # Сохраняем время напоминания о будущей дате
                                save_user(user_id, user['name'], user['chat_id'], 
                                        user.get('quit_date'), text)
                                
                                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                                status_button = types.KeyboardButton('Сколько я не курю?')
                                keyboard.add(status_button)
                                
                                bot.reply_to(
                                    message, 
                                    f"✨ Отлично! В {text} я напомню вам о том, что вы планируете бросить курить {quit_time.strftime('%d.%m.%Y')}\n\n"
                                    "💪 Вместе мы сможем это сделать!",
                                    reply_markup=keyboard
                                )
                                return
                        
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
                            f" Супер! Буду поддерживать тебя каждый день в {text}\n"
                            "✨ Время всегда можно изменить в настройках /settings",
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
                
                # Проверяем, не в будущем ли дата
                now = datetime.now(TIMEZONE)
                quit_date = TIMEZONE.localize(quit_date)  # Добавляем часовой пояс к дате отказа
                if quit_date > now:
                    # Сохраняем дату во временное хранилище
                    waiting_for_time[user_id] = quit_date
                    
                    # Создаем клавиатуру с кнопками времени
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
                    times = ['09:00', '12:00', '15:00', '18:00', '21:00']
                    buttons = [types.KeyboardButton(time) for time in times]
                    markup.add(*buttons)
                    
                    # Добавляем кнопку возврата
                    back_button = types.KeyboardButton('Сколько я не курю?')
                    markup.add(back_button)
                    
                    bot.reply_to(
                        message,
                        f"📅 {text} - эта дата еще не наступила\n\n"
                        "⏰ В какое время вы хотите получить напоминание о том, что собираетесь бросить курить?\n\n"
                        "• Нажмите на одну из кнопок\n"
                        "• Или введите своё время в формате ЧЧ:ММ\n\n"
                        "💫 Например: 10:30 или 20:00",
                        reply_markup=markup
                    )
                    return
                
                save_user(user_id, user['name'], user['chat_id'], 
                         quit_date.strftime("%Y-%m-%d %H:%M"))
                bot.reply_to(
                    message, 
                    f"🎉 Отлично! Дата отказа установлена на {text}\n\n"
                    "✨ Что дальше:\n"
                    "💫 Нажми кнопку 'Сколько я не курю?' или команду /status чтобы увидеть свой прогресс\n"
                    "⚡️ Настрой уведомления командой /settings чтобы получать поддержку каждый день\n\n"
                    "💪 Ты делаешь правильный выбор!"
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
                    "⚡️ /settings - настрой уведомления\n"
                    "❓ /help - все команды"
                )
            
            if user_id in waiting_for_time:
                # Если время некорректное, но мы ждали время от пользователя
                bot.reply_to(
                    message,
                    "❌ Некорректный формат времени!\n\n"
                    "⏰ Введите время в формате ЧЧ:ММ\n"
                    "• Часы: от 00 до 23\n"
                    "• Минуты: от 00 до 59\n\n"
                    "💫 Например: 10:30 или 20:00"
                )
                return
            
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка: {str(e)}") 