# Whisper Audio Recorder & Transcriber

A powerful Python utility to record audio and transcribe it using the Faster-Whisper engine.

[![Version](https://img.shields.io/badge/version-v1.15.0-blue)](./release-notes.md) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This utility allows you to record your voice using a global hotkey and automatically transcribe it to text using OpenAI's Whisper models. It features system tray integration, clipboard support, and a highly configurable setup via `config.ini`.

**Note:** The **turbo** model (`large-v3-turbo`) is currently recommended as the best option for both quality and speed.

## Table of Contents

- [Whisper Audio Recorder & Transcriber](#whisper-audio-recorder--transcriber)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Installation and Setup](#installation-and-setup)
  - [Configuration](#configuration)
  - [Usage](#usage)
  - [License](#license)

---

## Features

-   **Global Hotkey**: Start and stop recording from anywhere using a configurable hotkey (default: `Ctrl+Alt+E`).
-   **Fragment Mode**: **NEW!** Dedicated hotkey (default: `Ctrl+Alt+F`) for transcribing text phrases (lowercase, no trailing period) - perfect for inserting into existing sentences.
-   **System Tray Integration**: Visual feedback with icon color changes (Red for recording, Yellow for processing, Blue for idle) and menu controls.
-   **Fragment Mode Toggle**: Toggle "Fragment Mode" directly from the tray menu to use the primary hotkey for fragment transcription without needing a separate shortcut.
-   **Configuration-Driven**: All paths and settings are managed in a `config.ini` file.
-   **Multiple Models**: Supports `base`, `medium`, `distil-large-v3`, and the high-performance `large-v3-turbo`.
-   **Multilingual**: Easy language switching (English, German, Russian, Ukrainian) via the tray menu or command line.
-   **Clipboard Support**: Automatically copy transcribed text to the clipboard.
-   **Sequential Processing**: Audio recordings are queued and processed sequentially, ensuring no data is lost even if you record multiple clips in rapid succession.
-   **External File Processing**: **NEW!** Transcribe existing audio/video files (MP3, MP4, WAV, etc.) by passing them as CLI arguments or using the Clipboard Scanner.
-   **Clipboard Scanner Mode**: **NEW!** Copy file paths to your clipboard and hit the hotkey to transcribe them. Includes console-based confirmation to prevent accidental triggers.
-   **Smart File Naming**: **NEW!** Automatically handles existing transcriptions by adding incrementing suffixes (e.g., `audit.srt` -> `audit.1.srt`), ensuring no work is overwritten.
-   **Timestamping**: Option to save files with timestamps.
-   **Robust Architecture**: Built on a Functional Finite State Machine (Automatic Programming Pattern) for rock-solid reliability and sequence handling.

## Architecture

The application uses a **Functional FSM (Finite State Machine)** to manage its internal logic, ensuring high reliability:

1.  **IDLE** (Blue Icon): Waiting for user input.
2.  **RECORDING** (Red Icon): capturing audio.
3.  **PROCESSING** (Yellow Icon): Transcribing audio queue.

This "Automatic Programming" pattern guarantees that recordings and transcriptions are always processed in the correct order, and the status icon always reflects the true state of the application.

[Return To Top](#table-of-contents)

## Prerequisites

1.  **Windows 11**: These instructions are tailored for and tested on Windows 11.
2.  **Python 3**: Python 3.8 or higher is recommended.
2.  **Purfview-Whisper-Faster**: The independent executable for Faster-Whisper.
3.  **Audio Backend**: A working microphone.

## Installation and Setup

**Step 1: Clone or Download**
Ensure you have the project files locally.

**Step 2: Install Python Dependencies**
```bash
pip install sounddevice scipy pynput pyperclip pystray Pillow numpy
```
*Note: You may need additional system libraries for audio (e.g., `portaudio` on Linux).*

**Step 3: Configure the Application**

1.  Find `config.ini.template` in the project directory.
2.  **Make a copy** and rename it to `config.ini`.
3.  Open `config.ini` and set the paths for your system:
    *   `whisper_faster_executable`: Full path to `whisper-faster.exe`.
    *   `model_directory`: Directory where your Whisper models are stored.
    *   `base_directory`: Where temporary audio and text files will be saved.

[Return To Top](#table-of-contents)

## Configuration

All settings are managed in `config.ini`.

**`[paths]` section**:
-   `whisper_faster_executable`: Absolute path to the backend executable.
-   `base_directory`: Directory for saving recordings (can be relative to script).
-   `model_directory`: Path where Whisper models are stored.

**`[settings]` section**:
-   `hotkey`: Global hotkey string (e.g., `<ctrl>+<alt>+e`).

[Return To Top](#table-of-contents)

## Usage

Run the script using Python:

```bash
python whisper.py [arguments]
```

### Command Line Arguments

| Argument        | Description                                                                 |
| :-------------- | :-------------------------------------------------------------------------- |
| `--model`       | Select Whisper model (`base`, `medium`, `distil-large-v3`, `large-v3-turbo`). Default: `base`. |
| `--language`    | Set language (`en`, `de`, `ru`, `uk`). Default: Auto-detect.                |
| `--clipboard`   | Copy transcribed text to clipboard automatically.                           |
| `--tray`        | Enable system tray icon.                                                    |
| `--timestamp`   | Add timestamps to filenames.                                                |
| `--beep_off`    | Disable beep sound during transcription.                                    |
| `--fragment`    | Start with Fragment Mode enabled (affects primary hotkey).                  |
| `--file-scanner` | Start with File Processing Mode (Clipboard Scanner) enabled.               |
| `files` (pos)    | List of file paths to transcribe immediately in CLI mode.                   |

### Example

Run with the recommended **turbo** model, system tray, and clipboard support:

```bash
python whisper.py --model large-v3-turbo --tray --clipboard
```

[Return To Top](#table-of-contents)

## License

[MIT](./LICENSE)

[Return To Top](#table-of-contents)
