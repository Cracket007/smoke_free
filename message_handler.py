import os
from datetime import datetime
from moviepy.editor import concatenate_audioclips, AudioFileClip
from bot_config import bot, audio_files
import tempfile

def calculate_smoke_free_time(quit_time):
    now = datetime.now()
    delta = now - quit_time
    total_months = delta.days // 30
    years = total_months // 12
    months = total_months % 12
    days = delta.days % 30
    hours = delta.seconds // 3600
    return years, months, days, hours

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

def generate_voice_message(years, months, days, hours):
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

    # Добавляем часы
    if hours > 0:
        if years > 0 or months > 0 or days > 0:
            message_files.append(audio_files["and"])
        message_files.extend(get_number_files(hours))
        form = get_word_form(hours, audio_files["hour_forms"])
        message_files.append(audio_files["hour_forms"][form])

    return message_files

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

def send_status(chat_id, quit_time):
    try:
        if not os.path.exists('audio'):
            bot.send_message(chat_id, "Ошибка: директория audio не найдена")
            return

        years, months, days, hours = calculate_smoke_free_time(quit_time)
        voice_files = generate_voice_message(years, months, days, hours)
        
        # Проверяем наличие всех файлов
        for file in voice_files:
            if not os.path.exists(file):
                bot.send_message(chat_id, f"Ошибка: файл {file} не найден")
                return
        
        try:
            combined_file = combine_audio_files(voice_files)
            
            with open(combined_file, 'rb') as audio:
                bot.send_voice(chat_id, audio)
            
            os.unlink(combined_file)
            
            # Формируем текстовое сообщение
            text_parts = []
            if years > 0:
                text_parts.append(f"{years} г.")
            if months > 0:
                text_parts.append(f"{months} мес.")
            if days > 0:
                text_parts.append(f"{days} дн.")
            if hours > 0:
                text_parts.append(f"{hours} ч.")
            
            text_message = f"Вы не курите уже {' '.join(text_parts)}"
            bot.send_message(chat_id, text_message)
            
        except Exception as audio_error:
            bot.send_message(chat_id, f"Ошибка при обработке аудио: {str(audio_error)}")
        
    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {str(e)}") 