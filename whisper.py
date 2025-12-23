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
from queue import Queue
import configparser
from pathlib import Path

__version__ = "1.4.12"

# --- Constants ---
PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_FILE = PROJECT_ROOT / "config.ini"


def load_configuration(config_path):
    if not config_path.exists():
        print(f"Error: Configuration file not found at '{config_path}'.")
        print("Please copy 'config.ini.template' to 'config.ini' and configure it.")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path)
    return config


config = load_configuration(CONFIG_FILE)

# Configuration parameters from config file
whisper_faster_path = config.get("paths", "whisper_faster_executable")

base_dir_raw = config.get("paths", "base_directory")
if os.path.isabs(base_dir_raw):
    base_dir = base_dir_raw
else:
    base_dir = str(PROJECT_ROOT / base_dir_raw)

model_path = config.get("paths", "model_directory")
hotkey = config.get("settings", "hotkey")
hotkey_fragment = config.get("settings", "hotkey_fragment", fallback="<ctrl>+<alt>+f")

os.makedirs(base_dir, exist_ok=True)  # Create a directory if it does not already exist

# Global state management
class State:
    IDLE = "IDLE"
    RECORDING = "RECORDING"
    PROCESSING = "PROCESSING"

current_state = State.IDLE
audio_data = []
recording_thread = None
copy_to_clipboard = False
fragment_mode = False
default_fragment_mode = False  # New global for tray setting
use_timestamp = False
model_selected = "base"
language_selected = None
beep_off = False
timestamp_str = ""
audio_file_path = ""
output_srt_path = ""
output_txt_path = ""
icon = None
last_click_time = 0

# Queue to store audio files for transcription
transcription_queue = Queue()
icon_update_queue = Queue()


def set_state(new_state):
    global current_state
    current_state = new_state
    
    if new_state == State.IDLE:
        update_icon_color("blue")
    elif new_state == State.RECORDING:
        update_icon_color("red")
    elif new_state == State.PROCESSING:
        update_icon_color("yellow")


def update_icon_color(color):
    icon_update_queue.put(color)


def update_icon():
    global icon
    while True:
        color = icon_update_queue.get()
        if icon is not None:
            img = Image.new("RGB", (16, 16), color)
            icon.icon = img
        icon_update_queue.task_done()


def record_audio(sample_rate=44100):
    global audio_data, audio_file_path
    stop_key = hotkey_fragment if fragment_mode else hotkey
    print(f"\nRecording started... Press {stop_key} again to stop.")
    
    # State is already set to RECORDING by on_activate before this thread starts
    audio_data.clear()

    def callback(indata, frames, time, status):
        audio_data.append(indata.copy())

    try:
        with sd.InputStream(
            samplerate=sample_rate, channels=1, dtype="int16", callback=callback
        ):
            while current_state == State.RECORDING:
                sd.sleep(100)
        
        if audio_data:
            full_audio = np.concatenate(audio_data, axis=0)
            write(audio_file_path, sample_rate, full_audio)
            print(f"Recording saved to {audio_file_path}")
            transcription_queue.put(audio_file_path)
            
            # After recording, check if we need to process
            # If queue has items, we go to PROCESSING
            set_state(State.PROCESSING)
        else:
            print("No audio data recorded.")
            # If no audio, go back to IDLE
            if transcription_queue.empty():
                set_state(State.IDLE)
            else:
                 set_state(State.PROCESSING)

    except Exception as e:
        print(f"An error occurred during recording: {e}")
        # Error recovery: check queue
        if transcription_queue.empty():
            set_state(State.IDLE)
        else:
            set_state(State.PROCESSING)


def run_transcription():
    global model_selected, language_selected, beep_off
    while True:
        audio_file_path = transcription_queue.get()
        try:
            # We are now strictly processing this item
            # Even if we were already in PROCESSING, this confirms it or maintains it
            if current_state != State.RECORDING:
                 set_state(State.PROCESSING)

            output_srt_path = os.path.splitext(audio_file_path)[0] + ".srt"
            output_txt_path = os.path.splitext(audio_file_path)[0] + ".txt"
            
            print(f"Starting transcription for {audio_file_path}...")

            spoken_lines = []

            try:
                # model_path is now loaded from config
                srt_command = [
                    whisper_faster_path,
                    audio_file_path,
                    "--task",
                    "transcribe",
                    "--model",
                    model_selected,
                    "--model_dir",
                    model_path,
                    "--output_dir",
                    os.path.dirname(output_srt_path),
                    "--output_format",
                    "srt",
                    "--threads",
                    "8",
                    "--sentence"
                ]
                if language_selected is not None:
                    srt_command.extend(["--language", language_selected])
                if beep_off:
                    srt_command.append("--beep_off")

                print(
                    f"\nFull command to execute transcription: \n{' '.join(srt_command)}\n"
                )
                subprocess.run(srt_command, check=True, capture_output=True, text=True)
                print("SRT transcription completed.")

                with open(output_srt_path, "r", encoding="utf-8") as srt_file:
                    for line in srt_file:
                        if (
                            "-->" not in line
                            and line.strip() != ""
                            and not line.strip().isdigit()
                        ):
                            spoken_lines.append(line.strip())
                with open(output_txt_path, "w", encoding="utf-8") as txt_file:
                    txt_file.write("\n".join(spoken_lines))
                print("TXT transcription created from SRT.")

                if copy_to_clipboard:
                    text_to_copy = "\n".join(spoken_lines)
                    if fragment_mode:
                        # Fragment mode: lowercase first char, remove trailing period
                        if text_to_copy:
                            # Lowercase first character
                            text_to_copy = text_to_copy[0].lower() + text_to_copy[1:]
                            # Remove trailing period (and possibly whitespace before it)
                            if text_to_copy.strip().endswith("."):
                                text_to_copy = text_to_copy.strip()[:-1]

                    pyperclip.copy(text_to_copy)
                    print("Transcription copied to clipboard.")
            except subprocess.CalledProcessError as e:
                print(f"Transcription error: {e.stderr}")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                transcription_queue.task_done()
                
                # After task is done, check if more work exists
                if transcription_queue.empty():
                    # Only switch to IDLE if we aren't currently recording new audio
                    if current_state != State.RECORDING:
                        set_state(State.IDLE)
                else:
                    # More items? Stay in PROCESSING (Yellow)
                    if current_state != State.RECORDING:
                        set_state(State.PROCESSING)

        except Exception as e:
            print(f"Error processing {audio_file_path}: {e}")
            transcription_queue.task_done()
            if transcription_queue.empty() and current_state != State.RECORDING:
                set_state(State.IDLE)


def generate_timestamp():
    return datetime.now().strftime("%Y%m%d%H%M%S")


def on_activate():
    global recording_thread, timestamp_str, audio_file_path, output_srt_path, output_txt_path, fragment_mode
    if current_state != State.RECORDING:
        set_state(State.RECORDING)
        
        # Determine mode based on how on_activate was called or set externally?
        # Actually, global hotkeys call specific functions.
        # We'll need to wrap this.
        # But for now, let's assume `fragment_mode` is set before calling `on_activate`
        # OR we change `on_activate` to accept an argument.
        # Since `keyboard.GlobalHotKeys` expects a callable without args usually...
        # We will create wrappers.
        
        if use_timestamp:
            timestamp_str = generate_timestamp()
        else:
            timestamp_str = ""
        audio_file_path = os.path.join(
            base_dir, f"{timestamp_str}-audio.wav" if timestamp_str else "audio.wav"
        )
        output_srt_path = os.path.join(
            base_dir, f"{timestamp_str}-audio.srt" if timestamp_str else "audio.srt"
        )
        output_txt_path = os.path.join(
            base_dir, f"{timestamp_str}-audio.txt" if timestamp_str else "audio.txt"
        )
        recording_thread = threading.Thread(target=record_audio)
        recording_thread.start()
    else:
        # Stop recording
        # We don't change state to IDLE here immediately; record_audio will handle
        # transitioning to PROCESSING or IDLE when it finishes saving logic.
        # But we DO need to signal the loop in record_audio to stop.
        # Since record_audio loops on `while current_state == State.RECORDING`, 
        # we can temporarily switch state or use a flag?
        # A clearer way with FSM: define a transition out of recording.
        # But `record_audio` is blocking on that state check.
        # Let's transition to PROCESSING immediately if we stop? 
        # Actually, record_audio finishes, saves, *then* queues.
        # So we should signal it to stop.
        
        # NOTE: To strictly follow FSM, an external event (hotkey) triggers a state change.
        # We'll set a temporary "Signal" or just rely on the fact that if we change
        # `current_state` to something else, `record_audio` loop will break.
        # Let's set it to PROCESSING. This effectively stops the recording loop.
        set_state(State.PROCESSING)
        print("Stopping recording...")


def restart_with_language(language):
    global icon
    # if current_state != State.IDLE:  # Optional: prevent restart if busy
    #     print("Please wait until idle...")
    #     return
    icon.stop()
    python = sys.executable
    script_to_run = __file__
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--language=")] + [f"--language={language}"]
    
    # Persist fragment mode setting
    if default_fragment_mode:
         if "--fragment" not in args:
            args.append("--fragment")
    else:
        if "--fragment" in args:
            args.remove("--fragment")

    print(f"\nRestarting with language: {language}\n")

    subprocess.Popen([python, "restart.py", script_to_run] + args)
    os._exit(0)


def create_icon():
    global icon
    # Initial icon is blue (IDLE) - handled by default in main/set_state or here
    image = Image.new("RGB", (16, 16), color="blue")
    icon = pystray.Icon(
        "Whisper",
        image,
        "Audio Recorder and Transcriber",
        menu=pystray.Menu(
            pystray.MenuItem("Recording on / off", on_activate, default=True),
            pystray.MenuItem(
                "Fragment Mode",
                toggle_fragment_mode,
                checked=lambda item: default_fragment_mode
            ),
            pystray.MenuItem("Restart", restart),
            pystray.MenuItem(
                "Set Language",
                pystray.Menu(
                    pystray.MenuItem("English", lambda: restart_with_language("en")),
                    pystray.MenuItem("Deutsch", lambda: restart_with_language("de")),
                    pystray.MenuItem("Russian", lambda: restart_with_language("ru")),
                    pystray.MenuItem("Ukrainian", lambda: restart_with_language("uk")),
                ),
            ),
            pystray.MenuItem("Exit", lambda: exit_app()),
        ),
    )
    icon.run()

def on_activate_primary():
    global fragment_mode
    if current_state != State.RECORDING:
        fragment_mode = default_fragment_mode
        mode_name = "FRAGMENT" if fragment_mode else "NORMAL"
        print(f"Starting {mode_name} recording (Tray Setting)...")
    on_activate()

def toggle_fragment_mode(icon, item):
    global default_fragment_mode
    default_fragment_mode = not default_fragment_mode

def on_activate_fragment():
    global fragment_mode
    if current_state != State.RECORDING:
        fragment_mode = True
        print("Starting FRAGMENT recording...")
    on_activate()


def restart():
    global icon
    icon.stop()
    python = sys.executable
    script_to_run = __file__

    print(f"\nRestarting...\n")
    
    # Reconstruct args based on current state
    args = [arg for arg in sys.argv[1:] if arg != "--fragment"]
    if default_fragment_mode:
        args.append("--fragment")

    subprocess.Popen([python, "restart.py", script_to_run] + args)
    os._exit(0)


def exit_app():
    """Function to handle cleanup and exit the application."""
    global recording_thread, transcription_queue, icon_update_queue
    if current_state == State.RECORDING:
        set_state(State.IDLE) # Break the loop
        recording_thread.join()
    transcription_queue.join()
    icon_update_queue.join()
    if icon:
        icon.stop()
    os._exit(0)


def main():
    global copy_to_clipboard, use_timestamp, model_selected, language_selected, beep_off, tray
    parser = argparse.ArgumentParser(
        description="Audio recorder and transcriber with Whisper."
    )
    parser.add_argument(
        "--clipboard", action="store_true", help="Copy transcribed text to clipboard."
    )
    parser.add_argument(
        "--timestamp", action="store_true", help="Use timestamp in file names."
    )
    parser.add_argument(
        "--model",  # Fixed typo from "modeel"
        choices=["base", "medium", "distil-large-v3", "large-v3-turbo"],  # Added "turbo" option
        default="base",
        help="Select Whisper model version (base, medium, or distil-large-v3, large-v3-turbo).",  # Updated help text
    )
    parser.add_argument(
        "--language",
        choices=["en", "de", "ru", "uk"],
        default=None,
        help="Select language for transcription.",
    )
    parser.add_argument(
        "--beep_off", action="store_true", help="Disable beep during transcription."
    )
    parser.add_argument("--tray", action="store_true", help="Enable system tray icon.")
    parser.add_argument("--fragment", action="store_true", help="Start with Fragment Mode enabled.")
    args = parser.parse_args()
    copy_to_clipboard = args.clipboard
    use_timestamp = args.timestamp
    model_selected = args.model
    language_selected = args.language
    beep_off = args.beep_off
    beep_off = args.beep_off
    tray = args.tray
    
    # Set initial state from CLI arg
    global default_fragment_mode
    default_fragment_mode = args.fragment

    print("Available audio devices:")
    print(sd.query_devices())

    # Start the transcription thread
    transcription_thread = threading.Thread(target=run_transcription, daemon=True)
    transcription_thread.start()

    # Start the icon update thread
    icon_update_thread = threading.Thread(target=update_icon, daemon=True)
    icon_update_thread.start()

    # Create the system tray icon if specified
    if tray:
        tray_thread = threading.Thread(target=create_icon)
        tray_thread.start()

    # Helper to create VK-based hotkeys for layout independence
    def create_vk_hotkey(hotkey_str, callback):
        # Parse the hotkey string into a set of keys
        keys = keyboard.HotKey.parse(hotkey_str)
        new_keys = set()
        for key in keys:
            if isinstance(key, keyboard.KeyCode) and key.char:
                # Convert a-z characters to their virtual key codes
                # This ensures we listen to the physical key, not the layout-dependent char
                if 'a' <= key.char.lower() <= 'z':
                    new_keys.add(keyboard.KeyCode.from_vk(ord(key.char.upper())))
                else:
                    new_keys.add(key)
            else:
                new_keys.add(key)
        return keyboard.HotKey(new_keys, callback)

    hk_primary = create_vk_hotkey(hotkey, on_activate_primary)
    hk_fragment = create_vk_hotkey(hotkey_fragment, on_activate_fragment)
    hotkeys = [hk_primary, hk_fragment]

    # variable to hold the listener instance so it can be used in callbacks
    listener = None

    def normalize(key):
        # Determine if we should use VK or canonical
        if isinstance(key, keyboard.KeyCode) and key.vk is not None:
             # For character keys, strictly use VK to avoid layout mismatches
             return keyboard.KeyCode.from_vk(key.vk)
        
        # For control keys (modifiers), use canonical to map Left/Right to generic
        if listener:
            return listener.canonical(key)
        
        return key

    def on_press(key):
        k = normalize(key)
        for hk in hotkeys:
            hk.press(k)

    def on_release(key):
        k = normalize(key)
        for hk in hotkeys:
            hk.release(k)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    with listener:
        print(f"\nListening for {hotkey} (Normal) and {hotkey_fragment} (Fragment) [Layout Independent]...")
        listener.join()


if __name__ == "__main__":
    main()
