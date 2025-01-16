from flask import Flask, request
import telebot
from bot_config import bot, TOKEN
from commands import register_commands
import os

app = Flask(__name__)

# Регистрируем команды бота
register_commands(bot)

# Обработчик вебхуков
@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok'

# Проверка работоспособности
@app.route('/')
def index():
    return 'Bot is running'

def main():
    # Удаляем старый вебхук и устанавливаем новый
    bot.remove_webhook()
    
    # Получаем URL приложения из переменной окружения (для Heroku)
    url = os.getenv('APP_URL', '')
    if url:
        bot.set_webhook(url=url + '/' + TOKEN)
        
        # Запускаем Flask сервер
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        print("Ошибка: не указан APP_URL в переменных окружения")

if __name__ == '__main__':
    main() 