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

def record_audio(sample_rate=44100):
    """ Record audio from the microphone using a non-blocking stream. """
    global is_recording, audio_data
    
    print("Recording started... Press Ctrl + Alt + W again to stop.")
    is_recording = True
    audio_data.clear()  # Clear previous audio data
    
    def callback(indata, frames, time, status):
        """ Callback function to capture audio chunks. """
        audio_data.append(indata.copy())
    
    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', callback=callback):
            while is_recording:
                sd.sleep(100)  # Reduce CPU usage
        # After stopping, save the recorded audio
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
    global transcribing
    if transcribing:
        print("Transcription is already running.")
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
        with open(output_txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write('\n'.join(spoken_lines))
        print("TXT transcription created from SRT.")
    except subprocess.CalledProcessError as e:
        print(f"Transcription error: {e.stderr}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        transcribing = False

def on_activate():
    """ Toggle recording on/off with the same shortcut. """
    global recording_thread, is_recording
    if not is_recording:
        # Start a new recording thread
        recording_thread = threading.Thread(target=record_audio)
        recording_thread.start()
    else:
        # Signal the recording to stop
        is_recording = False
        print("Stopping recording...")

def main():
    print("Available audio devices:")
    print(sd.query_devices())
    # Set up the keyboard listener for Ctrl + Alt + W
    with keyboard.GlobalHotKeys({'<ctrl>+<alt>+w': on_activate}) as listener:
        print("Listening for Ctrl + Alt + W...")
        listener.join()

if __name__ == "__main__":
    main()