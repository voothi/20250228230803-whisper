import sounddevice as sd
from scipy.io.wavfile import write
from pynput import keyboard
import subprocess
import threading
import os
import time
import numpy as np

# Parameters
whisper_faster_path = r"C:\Users\voothi\AppData\Roaming\Subtitle Edit\Whisper\Purfview-Whisper-Faster\whisper-faster.exe"
audio_file_path = r"U:\voothi\20250228230803-whisper\tmp\audio.wav"
output_srt_path = r"U:\voothi\20250228230803-whisper\tmp\audio.srt"
output_txt_path = r"U:\voothi\20250228230803-whisper\tmp\audio.txt"

# Global variables for tracking
transcribing = False
recording_thread = None
is_recording = False  # Track if we are currently recording

def record_audio(filename, sample_rate=44100):
    """ Record audio from the microphone and save it to the specified filename. """
    global is_recording
    
    is_recording = True
    audio_data = sd.rec(int(sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    print("Recording started... Press Ctrl + Alt + W again to stop.")
    
    while is_recording:
        sd.sleep(100)  # Sleep to keep the thread alive while recording
    
    sd.stop()  # Stop recording when is_recording is false
    write(filename, sample_rate, audio_data)
    print("Recording saved.")

def run_transcription():
    global transcribing
    if transcribing:
        print("Transcribing is already running.")
        return

    transcribing = True
    print("Starting transcription...")

    try:
        model_path = r"C:\Users\voothi\AppData\Roaming\Subtitle Edit\Whisper\Purfview-Whisper-Faster\_models"

        # Create SRT output
        srt_command = [
            whisper_faster_path,
            audio_file_path,
            "--model", "medium",
            "--model_dir", model_path,
            "--output_dir", os.path.dirname(output_srt_path),
            "--output_format", "srt",
            "--sentence",
        ]

        subprocess.run(srt_command, check=True, capture_output=True, text=True)
        print("SRT transcription completed.")

        # Now create TXT output from the SRT
        spoken_lines = []
        with open(output_srt_path, 'r', encoding='utf-8') as srt_file:
            for line in srt_file:
                # Skip timestamps and only write the spoken text lines
                if '-->' not in line and line.strip() != "" and not line.strip().isdigit():
                    spoken_lines.append(line.strip())  # Accumulate spoken lines

        # Write collected lines to the TXT file, joining with '\n'
        with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write('\n'.join(spoken_lines))  # Join lines without adding extra newline

        print("TXT transcription created from SRT.")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred during transcription: {e.stderr}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        transcribing = False

def on_activate():
    """Method called when the shortcut is pressed."""
    global recording_thread, is_recording

    if not is_recording:
        # Start recording if not already recording
        recording_thread = threading.Thread(target=record_audio, args=(audio_file_path,))
        recording_thread.start()
    else:
        # Stop recording if it is currently recording
        is_recording = False
        print("Stopping the recording...")

def main():
    print("Available audio devices:")
    print(sd.query_devices())

    # Set up the keyboard listener for Ctrl + Alt + W
    with keyboard.GlobalHotKeys({'<ctrl>+<alt>+w': on_activate}) as listener:
        listener.join()

if __name__ == "__main__":
    main()