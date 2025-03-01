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
        print("Transcribing is already running.")
        return

    transcribing = True
    print("Starting transcription...")

    try:
        model_path = r"C:\Users\voothi\AppData\Roaming\Subtitle Edit\Whisper\Purfview-Whisper-Faster\_models"  # Specify your model path

        # Create SRT output
        srt_command = [
            whisper_faster_path,
            audio_file_path,
            "--model", "medium",  # Use medium model
            "--model_dir", model_path,  # Specify model directory
            "--output_dir", os.path.dirname(output_srt_path),  # Output directory
            "--output_format", "srt",  # Output format for SRT
            "--sentence",
        ]

        subprocess.run(srt_command, check=True, capture_output=True, text=True)
        print("SRT transcription completed.")

        # Now create TXT output from the SRT
        with open(output_srt_path, 'r', encoding='utf-8') as srt_file, open(output_transcript_path, 'w', encoding='utf-8') as txt_file:
            for line in srt_file:
                # Skip timestamps and only write the spoken text lines
                if '-->' not in line and line.strip() != "":
                    txt_file.write(line.strip() + '\n')
        print("TXT transcription created from SRT.")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred during transcription: {e.stderr}")
    except Exception as e:
        print(f"An error occurred: {e}")
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