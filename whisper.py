# whisper.py
from pynput import keyboard
import subprocess
import threading
import os

# Параметры
whisper_faster_path = r"C:\Users\voothi\AppData\Roaming\Subtitle Edit\Whisper\Purfview-Whisper-Faster\whisper-faster.exe"
audio_file_path = r".\input_audio_file.wav"
output_file_path = r".\output_transcript.txt"

# Глобальные переменные для отслеживания клавиш
current_keys = set()
transcribing = False

def run_transcription():
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
    try:
        if key == keyboard.Key.ctrl_l:
            current_keys.add(keyboard.Key.ctrl_l)
        elif key == keyboard.Key.alt_l:
            current_keys.add(keyboard.Key.alt_l)
        elif key.char == 'r' and keyboard.Key.ctrl_l in current_keys and keyboard.Key.alt_l in current_keys:
            print("Нажата комбинация Ctrl + Alt + R")
            # Запускаем транскрибирование в отдельном потоке
            threading.Thread(target=run_transcription).start()
    except AttributeError:
        pass

def on_release(key):
    if key in current_keys:
        current_keys.remove(key)
    if key == keyboard.Key.esc:
        # Останавливаем прослушивание по нажатию Esc
        return False

def main():
    print("Программа запущена. Нажмите Ctrl + Alt + R для начала транскрибирования.")
    print("Нажмите Esc для выхода.")

    # Устанавливаем прослушивание клавиш
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()