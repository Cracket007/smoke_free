import telebot
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

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
    "twenty": "audio/twenty.ogg",
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
    "and": "audio/and.ogg"
} 