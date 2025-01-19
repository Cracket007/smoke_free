import telebot
import os
from dotenv import load_dotenv
import random
from telebot import types
from datetime import datetime
import pytz

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

# Устанавливаем киевский часовой пояс
TIMEZONE = pytz.timezone('Europe/Kiev')

def get_current_time():
    """Получить текущее время в киевском часовом поясе"""
    return datetime.now(TIMEZONE)

if TOKEN is None:
    raise ValueError("Не найден BOT_TOKEN в файле .env")

bot = telebot.TeleBot(TOKEN)

# User data
users = {}

# Audio file paths
audio_files = {
    # Вступительная фраза
    "intro": "audio/intro.ogg",  # "Вы уже не курите"
    
    # Базовые числа (1-20, 30)
    "numbers": {str(i): f"audio/{i}.ogg" for i in range(1, 21)},
    "twenty": "audio/20.ogg",
    "thirty": "audio/30.ogg",
    
    # Слова для лет
    "year_forms": {
        "singular": "audio/year.ogg",     # год
        "few": "audio/years2-4.ogg",      # года
        "plural": "audio/years.ogg"       # лет
    },
    
    # Слова для месяцев
    "month_forms": {
        "singular": "audio/month.ogg",    # месяц
        "few": "audio/months2-4.ogg",     # месяца
        "plural": "audio/months.ogg"      # месяцев
    },
    
    # Слова для дней
    "day_forms": {
        "singular": "audio/day.ogg",      # день
        "few": "audio/days2-4.ogg",       # дня
        "plural": "audio/days.ogg"        # дней
    },
    
    # Слова для часов
    "hour_forms": {
        "singular": "audio/hour.ogg",     # час
        "few": "audio/hours2-4.ogg",      # часа
        "plural": "audio/hours.ogg"       # часов
    },
    
    # Соединительные слова
    "and": "audio/and.ogg",
    
    # Мотивирующие фразы
    "motivation": {
        "phrase1": "audio/phrase1.ogg",  # Я вами горжусь!
        "phrase2": "audio/phrase2.ogg",  # Вы молодец!
        "phrase3": "audio/phrase3.ogg",  # Так держать!
        "phrase4": "audio/phrase4.ogg",  # У вас отлично получается!
        "phrase5": "audio/phrase5.ogg",  # Каждый день - это победа!
        "phrase6": "audio/phrase6.ogg",  # Вы делаете правильный выбор!
        "phrase7": "audio/phrase7.ogg",  # Это достойно уважения!
        "phrase8": "audio/phrase8.ogg",
        "phrase9": "audio/phrase9.ogg",
        "phrase10": "audio/phrase10.ogg"   # Продолжайте в том же духе!
    }
} 

# Связь текстовых фраз с аудиофайлами
motivation_mapping = {
    "Я вами горжусь!": "phrase1",
    "Вы молодец!": "phrase2",
    "Так держать!": "phrase3",
    "У вас отлично получается!": "phrase4",
    "Каждый день - это победа!": "phrase5",
    "Вы делаете правильный выбор!": "phrase6",
    "Это достойно уважения!": "phrase7",
    "Ваша сила воли впечатляет!": "phrase8",
    "Здоровье важнее всего!": "phrase9",
    "Вы на правильном пути!": "phrase10"
} 

# Мотивирующие фразы
motivation_phrases = [
    "Я вами горжусь!",
    "Вы молодец!",
    "Так держать!",
    "У вас отлично получается!",
    "Каждый день - это победа!",
    "Вы делаете правильный выбор!",
    "Это достойно уважения!",
    "Ваша сила воли впечатляет!",
    "Здоровье важнее всего!",
    "Вы на правильном пути!"
] 

def get_motivational_message():
    """Получить случайное мотивационное сообщение"""
    return random.choice(motivation_phrases) 