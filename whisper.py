# whisper.py
import sounddevice as sd
from scipy.io.wavfile import write
from pynput import keyboard
import subprocess
import threading
import os
import time

# Параметры
whisper_faster_path = r"C:\Users\voothi\AppData\Roaming\Subtitle Edit\Whisper\Purfview-Whisper-Faster\whisper-faster.exe"
audio_file_path = r"U:\voothi\20250228230803-whisper\tmp\input_audio_file.wav"
output_file_path = r"U:\voothi\20250228230803-whisper\tmp\output_transcript.txt"

# Глобальные переменные для отслеживания
transcribing = False

def record_audio(filename, duration=10, sample_rate=44100):
    try:
        print("Запись началась...")
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()  # Ждем завершения записи
        write(filename, sample_rate, audio_data)
        print("Запись сохранена.")
    except Exception as e:
        print(f"Ошибка записи: {e}")

def run_transcription():
    global transcribing
    if transcribing:
        print("Транскрибирование уже запущено.")
        return

    transcribing = True
    print("Начало транскрибирования...")

    try:
        model_path = r"C:\Users\voothi\AppData\Roaming\Subtitle Edit\Whisper\Purfview-Whisper-Faster\_models"  # Замените на имя известной модели, как `base`, `small`, и т.д. 

        # Выполняем команду whisper-faster
        command = [
            whisper_faster_path,
            audio_file_path,
            "--model", "medium",  # Укажите модель
            "--model_dir", model_path,  # Укажите директорию модели
            "--output_dir", os.path.dirname(output_file_path),  # Укажите выходную директорию
            "--output_format", "txt",  # Укажите формат
        ]

        result = subprocess.run(command, check=True, capture_output=True, text=True)

        print("Транскрипция завершена.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Произошла ошибка при транскрибировании: {e.stderr}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        transcribing = False

def main():
    print("Доступные аудиоустройства:")
    print(sd.query_devices())  # Покажет список устройств

    # Запускаем запись сразу при запуске утилиты
    threading.Thread(target=record_audio, args=(audio_file_path, 10)).start()

    # Ждем, чтобы запись завершилась перед запуском транскрипции
    time.sleep(11)  # Увеличьте время, если необходимо, в зависимости от длины записи
    threading.Thread(target=run_transcription).start()

    print("Программа запущена. Запись и транскрипция выполняются.")
    print("Нажмите Esc для выхода.")

    # Устанавливаем прослушивание клавиш (не используется, но оставлено на случай, если потребуется)
    with keyboard.Listener(on_press=lambda key: None, on_release=lambda key: None) as listener:
        listener.join()

if __name__ == "__main__":
    main()