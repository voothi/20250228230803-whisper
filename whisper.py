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
import sys
import time

# Configuration parameters for paths
whisper_faster_path = r"C:\Users\voothi\AppData\Roaming\Subtitle Edit\Whisper\Purfview-Whisper-Faster\whisper-faster.exe"
base_dir = r"U:\voothi\20250228230803-whisper\tmp"
os.makedirs(base_dir, exist_ok=True)  # Create a directory if it does not already exist

# Global state management variables
transcribing = False
is_recording = False
audio_data = []
recording_thread = None
copy_to_clipboard = False
use_timestamp = False
model_selected = "base"
language_selected = None
timestamp_str = ""
audio_file_path = ""
output_srt_path = ""
output_txt_path = ""
icon = None

def update_icon_color():
    global icon, is_recording
    if icon is None:
        return
    color = 'red' if is_recording else 'blue'
    img = Image.new('RGB', (16, 16), color)
    # Use `icon.icon` to set the new image, pystray updates it automatically
    icon.icon = img  # No explicit `update()` method exists

def record_audio(sample_rate=44100):
    global is_recording, audio_data, audio_file_path
    print("\nRecording started... Press Ctrl + Alt + E again to stop.")
    is_recording = True
    update_icon_color()  # Change icon to red
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
        update_icon_color()  # Revert to blue

def run_transcription():
    global transcribing, output_srt_path, output_txt_path, model_selected, language_selected
    if transcribing:
        print("Transcription is already running.")
        return
    transcribing = True
    print("Starting transcription...")
    
    # Command to run the transcription
    try:
        model_path = r"C:\Users\voothi\AppData\Roaming\Subtitle Edit\Whisper\Purfview-Whisper-Faster\_models"
        srt_command = [
            whisper_faster_path,
            audio_file_path,
            "--model", model_selected,
            "--model_dir", model_path,
            "--output_dir", os.path.dirname(output_srt_path),
            "--output_format", "srt",
            "--threads", "4",
            "--sentence"
        ]
        if language_selected is not None:
            srt_command.extend(["--language", language_selected])

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
        update_icon_color()  # Immediate visual feedback on stop
        print("Stopping recording...")

def restart_with_language(language):
    global icon
    if is_recording or transcribing:  # Check if recording or transcribing is active
        print("Please wait until the current recording or transcription is finished before restarting.")
        return
    icon.stop()  # Stop the system tray icon
    python = sys.executable
    script_to_run = __file__
    args = sys.argv[1:] + [f"--language={language}"]
    
    print(f"\nRestarting with language: {language}\n")
    
    # Using subprocess to call the wrapper script
    subprocess.Popen([python, "restart.py", script_to_run] + args)
    os._exit(0)  # Terminate the current process

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
            pystray.MenuItem('Exit', lambda: exit_app())
        )
    )
    icon.run()

def restart():
    global icon
    if is_recording or transcribing:  # Check if busy with recording/transcribing
        print("Please finish current tasks before restarting.")
        return
    icon.stop()  # Stop the system tray icon
    python = sys.executable
    script_to_run = __file__
    
    print(f"\nRestarting...\n")
    
    # Using subprocess to call the wrapper script
    subprocess.Popen([python, "restart.py", script_to_run] + sys.argv[1:])
    os._exit(0)  # Terminate the current process

def exit_app():
    """Function to handle cleanup and exit the application."""
    global recording_thread, is_recording
    if is_recording:
        is_recording = False
        recording_thread.join()  # Wait for the recording thread to finish
    if icon:
        icon.stop()  # Stop the tray icon
    os._exit(0)  # Exit the application immediately after cleanup

def main():
    global copy_to_clipboard, use_timestamp, model_selected, language_selected, tray
    parser = argparse.ArgumentParser(description="Audio recorder and transcriber with Whisper.")
    parser.add_argument("--clipboard", action="store_true", help="Copy transcribed text to clipboard.")
    parser.add_argument("--timestamp", action="store_true", help="Use timestamp in file names.")
    parser.add_argument("--model", choices=["base", "medium"], default="base",
                        help="Select Whisper model version (base or medium).")
    parser.add_argument("--language", choices=["en", "de", "ru", "uk"], default=None,
                        help="Select language for transcription.")
    parser.add_argument("--tray", action="store_true", help="Enable system tray icon.")
    args = parser.parse_args()
    copy_to_clipboard = args.clipboard
    use_timestamp = args.timestamp
    model_selected = args.model
    language_selected = args.language
    tray = args.tray

    print("Available audio devices:")
    print(sd.query_devices())

    if tray:  # Create the system tray icon if specified
        tray_thread = threading.Thread(target=create_icon)
        tray_thread.start()

    with keyboard.GlobalHotKeys({'<ctrl>+<alt>+e': on_activate}) as listener:
        print("\nListening for Ctrl + Alt + E...")
        listener.join()

if __name__ == "__main__":
    main()