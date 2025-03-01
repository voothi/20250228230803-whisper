import sounddevice as sd
from scipy.io.wavfile import write
from pynput import keyboard
import subprocess
import threading
import os
import numpy as np
import argparse
import pyperclip
from datetime import datetime
import pystray
from PIL import Image
from io import BytesIO
import sys

# Configuration parameters
whisper_faster_path = r"C:\Users\voothi\AppData\Roaming\Subtitle Edit\Whisper\Purfview-Whisper-Faster\whisper-faster.exe"
base_dir = r"U:\voothi\20250228230803-whisper\tmp"
os.makedirs(base_dir, exist_ok=True)  # Create a directory if it does not exist

# Global variables for managing state and paths
transcribing = False
is_recording = False
audio_data = []
recording_thread = None
copy_to_clipboard = False
use_timestamp = False
model_selected = "base"  # Default value
language_selected = None  # Default value
timestamp_str = ""
audio_file_path = ""
output_srt_path = ""
output_txt_path = ""
icon = None

def record_audio(sample_rate=44100):
    global is_recording, audio_data, audio_file_path
    print("\nRecording started... Press Ctrl + Alt + W again to stop.")
    is_recording = True
    audio_data.clear()

    def callback(indata, frames, time, status):
        audio_data.append(indata.copy())

    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', callback=callback):
            while is_recording:
                sd.sleep(100)
        if audio_data:
            full_audio = np.concatenate(audio_data, axis=0)
            write(audio_file_path, sample_rate, full_audio)
            print(f"Recording saved to {audio_file_path}")
            run_transcription()
        else:
            print("No audio data recorded.")
    except Exception as e:
        print(f"An error occurred during recording: {e}")
    finally:
        is_recording = False

def run_transcription():
    global transcribing, output_srt_path, output_txt_path, model_selected, language_selected  # Ensure model_selected and language_selected are global
    if transcribing:
        print("Transcription is already running.")
        return
    transcribing = True
    print("Starting transcription...")
    try:
        model_path = r"C:\Users\voothi\AppData\Roaming\Subtitle Edit\Whisper\Purfview-Whisper-Faster\_models"
        srt_command = [
            whisper_faster_path,
            audio_file_path,
            "--model", model_selected,  # Use the updated model_selected value
            "--model_dir", model_path,
            "--output_dir", os.path.dirname(output_srt_path),
            "--output_format", "srt",
            "--threads", "4",
            "--sentence"
        ]
        # Add the --language argument only if language_selected is not None
        if language_selected is not None:
            srt_command.extend(["--language", language_selected])
        
        # Print the full command being executed
        print(f"\nFull command to execute transcription: \n{' '.join(srt_command)}\n")

        subprocess.run(srt_command, check=True, capture_output=True, text=True)
        print("SRT transcription completed.")

        spoken_lines = []
        with open(output_srt_path, 'r', encoding='utf-8') as srt_file:
            for line in srt_file:
                if '-->' not in line and line.strip() != "" and not line.strip().isdigit():
                    spoken_lines.append(line.strip())
        with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write('\n'.join(spoken_lines))
        print("TXT transcription created from SRT.")

        if copy_to_clipboard:
            pyperclip.copy('\n'.join(spoken_lines))
            print("Transcription copied to clipboard.")
    except subprocess.CalledProcessError as e:
        print(f"Transcription error: {e.stderr}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        transcribing = False

def generate_timestamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def on_activate():
    global recording_thread, is_recording, timestamp_str, audio_file_path, output_srt_path, output_txt_path
    if not is_recording:
        if use_timestamp:
            timestamp_str = generate_timestamp()
        else:
            timestamp_str = ""
        audio_file_path = os.path.join(base_dir, f"{timestamp_str}-audio.wav" if timestamp_str else "audio.wav")
        output_srt_path = os.path.join(base_dir, f"{timestamp_str}-audio.srt" if timestamp_str else "audio.srt")
        output_txt_path = os.path.join(base_dir, f"{timestamp_str}-audio.txt" if timestamp_str else "audio.txt")
        recording_thread = threading.Thread(target=record_audio)
        recording_thread.start()
    else:
        is_recording = False
        print("Stopping recording...")

def restart_with_language(language):
    global icon
    icon.stop()  # Останавливаем текущую иконку
    # Перезапуск скрипта с выбранным языком и другими аргументами командной строки
    python = sys.executable
    args = sys.argv[1:]
    args.append(f"--language={language}")
    
    print(f"\nRestarting with language: {language}\n")  # Condensed print statements
    
    subprocess.Popen([python, __file__] + args)
    sys.exit(0)  # Завершаем текущий процесс

def create_icon():
    global icon
    image = Image.new('RGB', (16, 16), color='blue')
    icon = pystray.Icon(
        "Whisper", 
        image, 
        "Audio Recorder and Transcriber", 
        menu=pystray.Menu(
            pystray.MenuItem('Record', on_activate),
            pystray.MenuItem('Restart', restart),
            pystray.MenuItem('Set Language', pystray.Menu(
                pystray.MenuItem('English', lambda: restart_with_language('en')),
                pystray.MenuItem('Deutsch', lambda: restart_with_language('de')),
                pystray.MenuItem('Russian', lambda: restart_with_language('ru')),
                pystray.MenuItem('Ukrainian', lambda: restart_with_language('uk')),
            )),
            pystray.MenuItem('Exit', lambda: icon.stop())
        )
    )
    icon.run()

def restart():
    global icon
    icon.stop()  # Останавливаем текущую иконку
    # Перезапуск скрипта с теми же аргументами командной строки
    python = sys.executable
    subprocess.Popen([python, __file__] + sys.argv[1:])
    sys.exit(0)  # Завершаем текущий процесс

def main():
    global copy_to_clipboard, use_timestamp, model_selected, language_selected, tray  # Add tray to global variables
    parser = argparse.ArgumentParser(description="Audio recorder and transcriber with Whisper.")
    parser.add_argument("--clipboard", action="store_true", help="Copy transcribed text to clipboard.")
    parser.add_argument("--timestamp", action="store_true", help="Use timestamp in file names.")
    parser.add_argument("--model", choices=["base", "medium"], default="base",  # Default model is "base"
                        help="Select Whisper model version (base or medium).")
    parser.add_argument("--language", choices=["en", "de", "ru", "uk"], default=None,  # No default language
                        help="Select language for transcription.")
    parser.add_argument("--tray", action="store_true", help="Enable system tray icon.")  # Add tray argument
    args = parser.parse_args()
    copy_to_clipboard = args.clipboard
    use_timestamp = args.timestamp
    model_selected = args.model  # Update model_selected with the parsed value
    language_selected = args.language  # Update language_selected with the parsed value
    tray = args.tray  # Update tray with the parsed value

    print("Available audio devices:")
    print(sd.query_devices())

    if tray:  # Check if tray should be created
        tray_thread = threading.Thread(target=create_icon)
        tray_thread.start()

    with keyboard.GlobalHotKeys({'<ctrl>+<alt>+w': on_activate}) as listener:
        print("\nListening for Ctrl + Alt + W...")
        listener.join()

if __name__ == "__main__":
    main()