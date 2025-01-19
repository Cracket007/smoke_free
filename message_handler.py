import os
from datetime import datetime
from moviepy.editor import concatenate_audioclips, AudioFileClip
from bot_config import bot, audio_files, motivation_phrases, motivation_mapping, get_motivational_message, TIMEZONE
import tempfile
import random
import pytz

def calculate_smoke_free_time(quit_time):
    """Вычисляет время без курения"""
    now = datetime.now(TIMEZONE)
    # Конвертируем время отказа в киевский часовой пояс если оно без зоны
    if quit_time.tzinfo is None:
        quit_time = TIMEZONE.localize(quit_time)
    
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
    """Возвращает список файлов для озвучки числа"""
    if number <= 20:
        return [audio_files["numbers"][str(number)]]
    elif number == 30:
        return [audio_files["thirty"]]
    else:  # 21-29
        return [audio_files["twenty"], audio_files["numbers"][str(number - 20)]]

def generate_voice_message(years, months, days):
    message_files = [audio_files["intro"]]
    
    # Добавляем годы
    if years > 0:
        message_files.extend(get_number_files(years))
        form = get_word_form(years, audio_files["year_forms"])
        message_files.append(audio_files["year_forms"][form])

    # Добавляем месяцы
    if months > 0:
        if years > 0:
            message_files.append(audio_files["and"])
        message_files.extend(get_number_files(months))
        form = get_word_form(months, audio_files["month_forms"])
        message_files.append(audio_files["month_forms"][form])

    # Добавляем дни
    if days > 0:
        if years > 0 or months > 0:
            message_files.append(audio_files["and"])
        message_files.extend(get_number_files(days))
        form = get_word_form(days, audio_files["day_forms"])
        message_files.append(audio_files["day_forms"][form])

    # Добавляем мотивирующую фразу
    motivation_text = random.choice(motivation_phrases)
    motivation_key = motivation_mapping[motivation_text]
    message_files.append(audio_files["motivation"][motivation_key])

    return message_files, motivation_text  # Возвращаем также текст фразы

def combine_audio_files(files):
    """Объединяет несколько .ogg файлов в один"""
    audio_clips = [AudioFileClip(file) for file in files]
    combined = concatenate_audioclips(audio_clips)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
        combined.write_audiofile(temp_file.name)
        for clip in audio_clips:
            clip.close()
        combined.close()
        return temp_file.name

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
    """Отправка статуса о времени без курения"""
    try:
        if not os.path.exists('audio'):
            print("❌ Ошибка: директория audio не найдена")
            return

        # Конвертируем время отказа в киевский часовой пояс если оно без зоны
        if quit_time.tzinfo is None:
            quit_time = TIMEZONE.localize(quit_time)

        years, months, days = calculate_smoke_free_time(quit_time)
        voice_files, motivation = generate_voice_message(years, months, days)
        
        # Проверяем наличие всех файлов
        for file in voice_files:
            if not os.path.exists(file):
                print(f"❌ Ошибка: файл {file} не найден")
                return
        
        try:
            combined_file = combine_audio_files(voice_files)
            
            with open(combined_file, 'rb') as audio:
                bot.send_voice(chat_id, audio)
            
            os.unlink(combined_file)
            
            # Формируем только текст с годами, месяцами и днями
            text_parts = []
            if years > 0:
                text_parts.append(f"{years} {'год' if years == 1 else 'года' if 1 < years < 5 else 'лет'}")
            if months > 0:
                text_parts.append(f"{months} {'месяц' if months == 1 else 'месяца' if 1 < months < 5 else 'месяцев'}")
            if days > 0:
                text_parts.append(f"{days} {'день' if days == 1 else 'дня' if 1 < days < 5 else 'дней'}")
            
            text_message = f"🚭 Вы не курите уже {' '.join(text_parts)}"
            bot.send_message(chat_id, text_message)
            
        except Exception as audio_error:
            print(f"❌ Ошибка при обработке аудио: {audio_error}")
            
    except Exception as e:
        print(f"❌ Ошибка отправки статуса: {e}")
        bot.send_message(chat_id, "❌ Произошла ошибка при подсчете времени")

def send_voice_status(chat_id, quit_time):
    """Отправка голосового статуса о времени без курения"""
    try:
        if not os.path.exists('audio'):
            print("❌ Ошибка: директория audio не найдена")
            return

        years, months, days = calculate_smoke_free_time(quit_time)
        voice_files, motivation = generate_voice_message(years, months, days)
        
        # Проверяем наличие всех файлов
        for file in voice_files:
            if not os.path.exists(file):
                print(f"❌ Ошибка: файл {file} не найден")
                return
        
        try:
            combined_file = combine_audio_files(voice_files)
            
            with open(combined_file, 'rb') as audio:
                bot.send_voice(chat_id, audio)
            
            os.unlink(combined_file)
            
        except Exception as audio_error:
            print(f"❌ Ошибка при обработке аудио: {audio_error}")
            
    except Exception as e:
        print(f"❌ Ошибка отправки голосового статуса: {e}") 