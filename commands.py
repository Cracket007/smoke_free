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
            print(f"\n🔄 Запрос настроек от пользователя {user_id}")
            
            user = get_user(user_id)
            if not user:
                print(f"❌ Пользователь {user_id} не найден")
                bot.reply_to(message, "❗️ Сначала зарегистрируйтесь с помощью /start")
                return
            
            current_time = datetime.now(TIMEZONE)
            notify_time = user.get('notify_time')
            notifications_enabled = user.get('notifications_enabled', True)
            
            print(f"📱 Текущие настройки:")
            print(f"⏰ Время уведомлений: {notify_time}")
            print(f"🔔 Уведомления: {'включены' if notifications_enabled else 'выключены'}")
            
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
            
            # Определяем статус следующего уведомления только если время установлено
            next_notify_text = ""
            if notify_time and notifications_enabled:
                notify_hours, notify_minutes = map(int, notify_time.split(':'))
                notify_datetime = current_time.replace(hour=notify_hours, minute=notify_minutes)
                next_notify = "завтра" if current_time > notify_datetime else "сегодня"
                next_notify_text = f"\n📅 Следующее уведомление: {next_notify} в {notify_time}"
            
            status = "включены ✅" if notifications_enabled else "выключены ❌"
            time_status = f"⏰ Время отправки: {notify_time if notify_time else 'не установлено'}"
            
            bot.reply_to(
                message,
                f"⚙️ Настройки уведомлений:\n\n"
                f"🔔 Статус: {status}\n"
                f"{time_status}"
                f"{next_notify_text}\n\n"
                "Выберите действие:\n"
                "• Нажмите на время для изменения\n"
                "• Или введите своё время в формате ЧЧ:ММ\n"
                "• Используйте кнопки для включения/выключения",
                reply_markup=markup
            )
            
        except Exception as e:
            print(f"❌ Ошибка в настройках: {str(e)}")
            print(f"🔍 Детали ошибки: {type(e).__name__}")
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
            
            # Обработка включения/выключения уведомлений
            if text == '🔔 Включить уведомления':
                save_user(user_id, user['name'], user['chat_id'], 
                        user.get('quit_date'), '15:00', True)  # Устанавливаем время по умолчанию
                setup_schedules()  # Обновляем расписание
                
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                status_button = types.KeyboardButton('Сколько я не курю?')
                keyboard.add(status_button)
                
                bot.reply_to(message, "✅ Уведомления включены на 15:00!\nИзмените время в настройках /settings", reply_markup=keyboard)
                return
                
            if text == '🔕 Выключить уведомления':
                save_user(user_id, user['name'], user['chat_id'], 
                        user.get('quit_date'), None, False)  # Убираем время уведомлений
                setup_schedules()  # Обновляем расписание
                
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                status_button = types.KeyboardButton('Сколько я не курю?')
                keyboard.add(status_button)
                
                bot.reply_to(message, "❌ Уведомления выключены!", reply_markup=keyboard)
                return
            
            # Проверяем формат времени (ЧЧ:ММ)
            if ':' in text and len(text) == 5:
                try:
                    hours, minutes = map(int, text.split(':'))
                    if 0 <= hours < 24 and 0 <= minutes < 60:
                        if user.get('quit_date'):
                            # Включаем уведомления и устанавливаем время
                            save_user(user_id, user['name'], user['chat_id'],
                                    user.get('quit_date'), text, True)
                            setup_schedules()
                            
                            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                            status_button = types.KeyboardButton('Сколько я не курю?')
                            keyboard.add(status_button)
                            
                            bot.reply_to(
                                message, 
                                f"✨ Отлично! Буду отправлять уведомления каждый день в {text}\n"
                                "💪 Вместе мы сможем это сделать!",
                                reply_markup=keyboard
                            )
                        else:
                            bot.reply_to(
                                message,
                                "❗️ Сначала укажите дату отказа от курения"
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
                    bot.reply_to(
                        message,
                        "❌ Нельзя указать будущую дату.\n"
                        "📅 Укажите дату, когда вы уже бросили курить"
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