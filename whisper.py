# whisper.py
import sounddevice as sd
from scipy.io.wavfile import write
from pynput import keyboard
import subprocess
import threading
import os

# Параметры
whisper_faster_path = r"C:\Users\voothi\AppData\Roaming\Subtitle Edit\Whisper\Purfview-Whisper-Faster\whisper-faster.exe"
audio_file_path = r"U:\voothi\20250228230803-whisper\input_audio_file.wav"
output_file_path = r"U:\voothi\20250228230803-whisper\output_transcript.txt"

# Глобальные переменные для отслеживания клавиш
current_keys = set()
transcribing = False

def record_audio(filename, duration=5, sample_rate=44100):
    try:
        print("Запись началась...")
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
        write(filename, sample_rate, audio_data)
        print("Запись сохранена.")
    except Exception as e:
        print(f"Ошибка записи: {e}")
        raise  # Перебрасываем исключение для видимости в on_press

def run_transcription():
    time.sleep(0.5)  # Даем время на сохранение файла
    # ... остальной код ...
    global transcribing
    if transcribing:
        print("Транскрибирование уже запущено.")
        return

    transcribing = True
    print("Начало транскрибирования...")

    try:
        # Укажите путь к модели
        model_path = r"C:\Tools\open-webui\venv\Lib\site-packages\open_webui\data\cache\whisper\models\models--Systran--faster-whisper-base\snapshots\ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66\model.bin"

        # Выполняем команду whisper-faster
        command = [
            whisper_faster_path,
            audio_file_path,
            "--model", model_path,
            "--output", output_file_path,
            # Добавьте другие необходимые параметры сюда
            # Например: "--initial-prompt", "Starting the meeting.",
            #           "--vad-filter", "--vad-threshold", "0.45",
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

def on_press(key):
    global current_keys
    try:
        if key == keyboard.Key.ctrl_l:
            current_keys.add(key)
        elif key == keyboard.Key.shift_l:
            current_keys.add(key)
        elif hasattr(key, 'char') and key.char is not None and key.char.lower() == 't':
            if keyboard.Key.ctrl_l in current_keys and keyboard.Key.shift_l in current_keys:
                print("Запуск записи и транскрибации...")
                # Запуск записи в отдельном потоке
                threading.Thread(target=lambda: record_audio(audio_file_path, duration=10)).start()
                # Запуск транскрибации с задержкой (дождаться окончания записи)
                threading.Thread(target=run_transcription).start()
                current_keys.clear()
    except Exception as e:
        print(f"Ошибка: {e}")

def on_release(key):
    global current_keys
    try:
        if key in current_keys:
            current_keys.remove(key)
            print(f"Отпущена клавиша: {key}")
        if key == keyboard.Key.esc:
            # Останавливаем прослушивание по нажатию Esc
            print("Нажата клавиша Esc. Выход.")
            return False
    except Exception as e:
        print(f"Произошла ошибка: {e}")

def main():
    print("Доступные аудиоустройства:")
    print(sd.query_devices())  # Покажет список устройств
    print("Программа запущена. Нажмите Ctrl + Shift + T...")
    # ... остальной код ...
    print("Программа запущена. Нажмите Ctrl + Shift + T для начала транскрибирования.")
    print("Нажмите Esc для выхода.")

    # Устанавливаем прослушивание клавиш
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()