import sounddevice as sd
from scipy.io.wavfile import write
from pynput import keyboard
import subprocess
import threading
import os
import shutil
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

__version__ = "1.17.0"

# --- Constants ---
PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_FILE = PROJECT_ROOT / "config.ini"
SUPPORTED_EXTENSIONS = {'.wav', '.mp3', '.m4a', '.mp4', '.mkv', '.flac', '.ogg', '.aac'}


def get_unique_path(path):
    """Adds .1, .2, etc. to the filename if it already exists."""
    path = Path(path)
    if not path.exists():
        return str(path)

    parent = path.parent
    stem = path.stem
    suffix = path.suffix

    counter = 1
    while True:
        new_name = f"{stem}.{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return str(new_path)
        counter += 1


def get_files_from_clipboard():
    """Extracts valid existing audio/video files from clipboard text."""
    try:
        text = pyperclip.paste()
        if not text:
            return []

        lines = text.splitlines()
        found_files = []
        for line in lines:
            line = line.strip().strip('"')  # Remove quotes if copied from explorer
            if not line:
                continue
            path = Path(line)
            if path.exists() and path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                found_files.append(str(path))
        return found_files
    except Exception as e:
        print(f"Error reading clipboard: {e}")
        return []


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
    WAITING = "WAITING"

current_state = State.IDLE
audio_data = []
recording_thread = None
copy_to_clipboard = False
fragment_mode = False
default_fragment_mode = False  # New global for tray setting
file_scanner_enabled = False  # Toggle for clipboard processing
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
    elif new_state == State.WAITING:
        update_icon_color("gray")


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
            # Tuple: (path, skip_clipboard)
            transcription_queue.put((audio_file_path, False))
            
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
        queue_item = transcription_queue.get()
        # Handle both old (string) and new (tuple) queue items for robustness
        if isinstance(queue_item, tuple):
            audio_file_path, skip_clipboard = queue_item
        else:
            audio_file_path, skip_clipboard = queue_item, False

        try:
            # We are now strictly processing this item
            if current_state != State.RECORDING:
                set_state(State.PROCESSING)

            # Use a temporary directory for initial output to handle unique naming
            temp_output_dir = str(PROJECT_ROOT / "tmp")
            os.makedirs(temp_output_dir, exist_ok=True)

            # Expected name from whisper-faster (based on input filename)
            input_basename = os.path.basename(os.path.splitext(audio_file_path)[0])
            temp_srt_path = os.path.join(temp_output_dir, f"{input_basename}.srt")

            # Final output paths - use get_unique_path to handle existing files
            final_srt_base = os.path.splitext(audio_file_path)[0] + ".srt"
            final_srt_path = get_unique_path(final_srt_base)
            final_txt_path = os.path.splitext(final_srt_path)[0] + ".txt"

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
                    temp_output_dir,
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

                if os.path.exists(temp_srt_path):
                    # Move result to the final location with unique name
                    shutil.move(temp_srt_path, final_srt_path)
                    print(f"SRT transcription completed: {final_srt_path}")

                    with open(final_srt_path, "r", encoding="utf-8") as srt_file:
                        for line in srt_file:
                            if (
                                "-->" not in line
                                and line.strip() != ""
                                and not line.strip().isdigit()
                            ):
                                spoken_lines.append(line.strip())
                    with open(final_txt_path, "w", encoding="utf-8") as txt_file:
                        txt_file.write("\n".join(spoken_lines))
                    print(f"TXT transcription created: {final_txt_path}")

                    if copy_to_clipboard and not skip_clipboard:
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
                    elif copy_to_clipboard and skip_clipboard:
                        print("Skipping clipboard copy (batch processing).")
                else:
                    print(f"Error: Transcription output {temp_srt_path} was not created.")

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
    
    # Block new actions if waiting for console input (Always)
    if current_state == State.WAITING:
        print("Application is waiting for console input. Ignoring trigger.")
        return
    
    # In File Processing Mode, block while PROCESSING to ensure strictly sequential batch handling
    if file_scanner_enabled and current_state == State.PROCESSING:
        print("Application is busy processing files. Ignoring trigger.")
        return

    if current_state != State.RECORDING:
        # Check for files in clipboard if scanner mode is active
        if file_scanner_enabled:
            found_files = get_files_from_clipboard()
            if found_files:
                print(f"\n[Scanner] Found {len(found_files)} supported file(s) in clipboard:")
                for f in found_files:
                    print(f"  - {f}")

                # Console confirmation
                set_state(State.WAITING)
                confirm = input("Process these files? (y/n, default 'y'): ").lower().strip()
                if confirm in ('', 'y', 'yes'):
                    print("Adding files to transcription queue...")
                    # If more than 1 file, we set skip_clipboard to True
                    skip_cb = len(found_files) > 1
                    for f in found_files:
                        transcription_queue.put((f, skip_cb))
                    
                    # Ensure we are in PROCESSING state if we have items
                    if not transcription_queue.empty():
                        set_state(State.PROCESSING)
                    return # Skip microphone recording
                else:
                    print("File processing cancelled. Returning to IDLE.")
                    set_state(State.IDLE)
                    return # Skip both file processing and microphone recording

        set_state(State.RECORDING)

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
        # Signal recording loop to stop by transitioning state
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

    # Persist file scanner setting
    if file_scanner_enabled:
        if "--file-scanner" not in args:
            args.append("--file-scanner")
    else:
        if "--file-scanner" in args:
            args.remove("--file-scanner")

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
            pystray.MenuItem("Open Files", open_base_directory),
            pystray.MenuItem("Recording on / off", on_activate, default=True),
            pystray.MenuItem(
                "Fragment Mode",
                toggle_fragment_mode,
                checked=lambda item: default_fragment_mode
            ),
            pystray.MenuItem(
                "File Processing Mode",
                toggle_file_scanner,
                checked=lambda item: file_scanner_enabled
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

def toggle_file_scanner(icon, item):
    global file_scanner_enabled
    file_scanner_enabled = not file_scanner_enabled

def on_activate_fragment():
    global fragment_mode
    if current_state != State.RECORDING:
        fragment_mode = True
        print("Starting FRAGMENT recording...")
    on_activate()


def open_base_directory():
    try:
        os.startfile(base_dir)
    except Exception as e:
        print(f"Error opening directory: {e}")



def restart():
    global icon
    icon.stop()
    python = sys.executable
    script_to_run = __file__

    print(f"\nRestarting...\n")
    
    # Reset to original CLI args: clear language and dynamic mode flags
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--language=") 
            and arg not in ("--fragment", "--file-scanner")]

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
    parser.add_argument(
        "--file-scanner", action="store_true", help="Start with File Processing Mode enabled."
    )
    parser.add_argument(
        "files", nargs="*", help="Optional list of file paths to transcribe immediately."
    )
    args = parser.parse_args()
    copy_to_clipboard = args.clipboard
    use_timestamp = args.timestamp
    model_selected = args.model
    language_selected = args.language
    beep_off = args.beep_off
    tray = args.tray

    # Set initial state from CLI arg
    global default_fragment_mode, file_scanner_enabled
    default_fragment_mode = args.fragment
    file_scanner_enabled = args.file_scanner

    print("Available audio devices:")
    print(sd.query_devices())

    # Start the transcription thread
    transcription_thread = threading.Thread(target=run_transcription, daemon=True)
    transcription_thread.start()

    # If files were passed as arguments, queue them up
    if args.files:
        print(f"\nProcessing {len(args.files)} file(s) from arguments...")
        skip_cb = len(args.files) > 1
        for f in args.files:
            path = Path(f)
            if path.exists() and path.is_file():
                transcription_queue.put((str(path), skip_cb))
            else:
                print(f"Warning: File not found or invalid: {f}")

        # If not in tray mode, wait for queue to be empty and then exit
        if not tray:
            transcription_queue.join()
            print("All files processed. Exiting.")
            sys.exit(0)

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
