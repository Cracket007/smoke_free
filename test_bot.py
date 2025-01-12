import telebot

TOKEN = "6050730620:AAFpspSK0HHmi62rkldfaIZKL5w2m-2A30M"  # Вставьте ваш реальный токен
bot = telebot.TeleBot(TOKEN)

print("Получаем информацию о боте...")
try:
    bot_info = bot.get_me()
    print(f"Бот успешно подключен: @{bot_info.username}")
except Exception as e:
    print("Ошибка при подключении:", e) 