import os
from datetime import datetime
from pydub import AudioSegment
from bot_config import bot, audio_files, voice_motivation_phrases, get_text_motivation, get_voice_motivation, TIMEZONE
import tempfile
import random
import pytz

def calculate_smoke_free_time(quit_time):
    """Вычисляет время без курения"""
    now = datetime.now(TIMEZONE)
    # Конвертируем время отказа в киевский часовой пояс если оно без зоны
    if quit_time.tzinfo is None:
        quit_time = TIMEZONE.localize(quit_time)
    
    # Проверяем, не в будущем ли дата
    if quit_time > now:
        return 0, 0, 0  # Возвращаем нули если дата в будущем
    
    delta = now - quit_time
    total_months = delta.days // 30
    years = total_months // 12
    months = total_months % 12
    days = delta.days % 30
    return years, months, days

def get_word_form(number, forms):
    if number % 10 == 1 and number % 100 != 11:
        return "singular"
    elif 2 <= number % 10 <= 4 and not (12 <= number % 100 <= 14):
        return "few"
    else:
        return "plural"

def get_number_files(number):
    """Получает список файлов для озвучивания числа"""
    files = []
    
    if number <= 20:
        # Для чисел до 20 используем готовые файлы
        files.append(audio_files["numbers"][str(number)])
    else:
        # Для чисел больше 20
        tens = (number // 10) * 10
        ones = number % 10
        
        if tens == 20:
            files.append(audio_files["twenty"])
        elif tens == 30:
            files.append(audio_files["thirty"])
            
        if ones > 0:
            files.append(audio_files["numbers"][str(ones)])
    
    return files

def generate_voice_message(years, months, days):
    """Генерирует список аудиофайлов для сообщения"""
    message_files = [audio_files["intro"]]
    parts = []
    
    # Собираем все части сообщения
    if years > 0:
        year_files = get_number_files(years)
        year_form = get_word_form(years, audio_files["year_forms"])
        parts.append(year_files + [audio_files["year_forms"][year_form]])
        
    if months > 0:
        month_files = get_number_files(months)
        month_form = get_word_form(months, audio_files["month_forms"])
        parts.append(month_files + [audio_files["month_forms"][month_form]])
        
    if days > 0:
        day_files = get_number_files(days)
        day_form = get_word_form(days, audio_files["day_forms"])
        parts.append(day_files + [audio_files["day_forms"][day_form]])
    
    # Собираем сообщение с "и" только перед последней частью
    for i, part in enumerate(parts):
        if i == len(parts) - 1 and i > 0:  # Если это последняя часть и не единственная
            message_files.append(audio_files["and"])
        message_files.extend(part)
    
    # Добавляем мотивирующую фразу
    motivation_text, motivation_key = get_voice_motivation()
    message_files.append(audio_files["motivation"][motivation_key])
    
    return message_files

def combine_audio_files(files):
    """Объединяет аудиофайлы в один"""
    try:
        # Загружаем первый файл
        combined = AudioSegment.from_ogg(files[0])
        
        # Добавляем остальные файлы
        for file in files[1:]:
            audio = AudioSegment.from_ogg(file)
            combined += audio
            
        return combined  # Возвращаем AudioSegment объект
        
    except Exception as e:
        print(f"❌ Ошибка при объединении аудио: {e}")
        raise

def format_duration(duration):
    """Форматирование продолжительности"""
    days = duration.days
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days} {'день' if days == 1 else 'дня' if 1 < days < 5 else 'дней'}")
    if hours > 0:
        parts.append(f"{hours} {'час' if hours == 1 else 'часа' if 1 < hours < 5 else 'часов'}")
    if minutes > 0:
        parts.append(f"{minutes} {'минуту' if minutes == 1 else 'минуты' if 1 < minutes < 5 else 'минут'}")
    
    return " и ".join(parts) if parts else "меньше минуты"

def send_status(chat_id, quit_time):
    """Отправляет текстовый и голосовой статус"""
    try:
        years, months, days = calculate_smoke_free_time(quit_time)
        
        # Проверяем, не в будущем ли дата
        if years == months == days == 0:
            bot.send_message(chat_id, "❗️ Дата отказа не может быть в будущем")
            return
            
        text_parts = []
        if years > 0:
            text_parts.append(f"{years} {'год' if years == 1 else 'года' if 1 < years < 5 else 'лет'}")
        if months > 0:
            text_parts.append(f"{months} {'месяц' if months == 1 else 'месяца' if 1 < months < 5 else 'месяцев'}")
        if days > 0:
            text_parts.append(f"{days} {'день' if days == 1 else 'дня' if 1 < days < 5 else 'дней'}")
        
        text_message = (
            f"🌟 Твой путь к здоровью:\n\n"
            f"✨ Уже {' '.join(text_parts)} свободы от курения!\n\n"
            f"{get_text_motivation()}"
        )
        bot.send_message(chat_id, text_message)
        
        send_voice_status(chat_id, quit_time)
        
    except Exception as e:
        print(f"❌ Ошибка отправки статуса: {e}")

def send_voice_status(chat_id, quit_time):
    """Отправляет голосовое сообщение о прогрессе"""
    try:
        if not os.path.exists('audio'):
            print("❌ Папка audio не найдена")
            return
            
        years, months, days = calculate_smoke_free_time(quit_time)
        
        # Получаем список файлов для сообщения
        message_files = generate_voice_message(years, months, days)
        
        # Комбинируем аудиофайлы
        combined = combine_audio_files(message_files)
        
        # Конвертируем в формат для голосовых сообщений
        combined = combined.set_channels(1)  # моно
        combined = combined.set_frame_rate(48000)  # 48кГц
        
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            # Экспортируем с параметрами для голосовых сообщений
            combined.export(
                temp_file.name,
                format='ogg',
                codec='libopus',
                parameters=[
                    '-ac', '1',      # моно
                    '-ar', '48000',  # частота 48кГц
                    '-b:a', '128k'   # битрейт 128кбит/с
                ]
            )
            
            # Отправляем файл
            with open(temp_file.name, 'rb') as audio:
                bot.send_voice(chat_id, audio)
                
        # Удаляем временный файл
        os.unlink(temp_file.name)
        
    except Exception as e:
        print(f"❌ Ошибка отправки голосового сообщения: {e}") 