import sounddevice as sd
from scipy.io.wavfile import write
from pynput import keyboard
import subprocess
import threading
import os
import numpy as np

# Parameters for paths and audio configurations
whisper_faster_path = r"C:\Users\voothi\AppData\Roaming\Subtitle Edit\Whisper\Purfview-Whisper-Faster\whisper-faster.exe"
audio_file_path = r"U:\voothi\20250228230803-whisper\tmp\audio.wav"
output_srt_path = r"U:\voothi\20250228230803-whisper\tmp\audio.srt"
output_txt_path = r"U:\voothi\20250228230803-whisper\tmp\audio.txt"

# Global variables for state management
transcribing = False
is_recording = False
audio_data = []  # Global list for audio data storage
recording_thread = None

def record_audio(filename, sample_rate=44100):
    """ Record audio from the microphone until stopped by the user. """
    global is_recording, audio_data
    
    print("Recording started... Press Ctrl + Alt + W again to stop.")
    is_recording = True

    try:
        audio_data.clear()  # Clear previous audio data
        # Start recording
        while is_recording:
            chunk = sd.rec(1024, samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()  # Wait until the chunk has been recorded
            audio_data.append(chunk)  # Store audio chunk in global list

        # If recording has stopped, finalize audio capture
        if audio_data:
            audio_data = np.concatenate(audio_data, axis=0)
            write(filename, sample_rate, audio_data)  # Write the full audio to a file
            print("Recording saved.")
        else:
            print("No audio data recorded.")

    except Exception as e:
        print(f"An error occurred during recording: {e}")

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

        # Create TXT output from the SRT
        spoken_lines = []
        with open(output_srt_path, 'r', encoding='utf-8') as srt_file:
            for line in srt_file:
                if '-->' not in line and line.strip() != "" and not line.strip().isdigit():
                    spoken_lines.append(line.strip())

        # Write collected lines to the TXT file
        with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write('\n'.join(spoken_lines))

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
        # Start recording if not currently recording
        recording_thread = threading.Thread(target=record_audio, args=(audio_file_path,))
        recording_thread.start()
    else:
        # Stop recording if currently recording
        is_recording = False
        print("Stopping the recording...")

def main():
    print("Available audio devices:")
    print(sd.query_devices())

    # Set up the keyboard listener for Ctrl + Alt + W
    with keyboard.GlobalHotKeys({'<ctrl>+<alt>+w': on_activate}) as listener:
        print("Listening for Ctrl + Alt + W...")
        listener.join()

if __name__ == "__main__":
    main()