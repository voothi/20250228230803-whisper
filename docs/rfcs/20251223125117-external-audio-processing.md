# 20251223125117

## Title
External Audio File Processing

## Staging
20251223125117
20251223141313
20251223141912
20251223142524
20251223142739
20251223143040
20251223143406
20251223143858
20251223144311
20251223145538
20251223150019
20251223150249
20251223150831
20251223151452

## Description
Comprehensive implementation of external file processing capabilities, transitioning the utility from a pure voice recorder to a dual-purpose transcription engine. This includes clipboard scanning, multi-file CLI support, advanced naming conventions, and robust state management for safety.

## Implementation Details

### Core Functionality
- **Clipboard Scanner**: Detects supported audio/video files in the clipboard. When active, hitting the hotkey triggers a console confirmation to process these files sequentially.
- **CLI Batch Processing**: Added support for positional arguments to process multiple files in sequence (e.g., `python whisper.py file1.mp3 file2.wav`).
- **Cross-Drive Reliability**: Replaced `os.replace` with `shutil.move` to prevent failures when moving processed files between different logical drives (e.g., `U:` to `C:`).
- **Exclusive Modes**: When "File Processing Mode" is active, microphone recording is locked out to prevent concurrent state conflicts.

### Naming & State Management
- **Smart Naming Convention**: Output files now use `.lang.srt` postfixes (e.g., `.en.srt`). Incrementing version counters are placed *before* the language (e.g., `.1.en.srt`).
- **Input Blocking**: Implemented state-aware input guards. In File Mode, triggers are blocked during `WAITING` and `PROCESSING`. In Normal Mode, sequential recording remains active during `PROCESSING`.
- **Waiting State (Gray Icon)**: Added a new `WAITING` state with a gray tray icon to clearly indicate when the application requires user input in the console.
- **Persistence Logic**: Settings like "File Processing Mode" are persisted when switching languages but reset during a full "Restart" to ensure a clean slate.

### Workflow & Control
- **Console-First Interaction**: Maintained a pure console interaction for prompts (y/n) to avoid heavy GUI dependencies (tkinter).
- **Graceful Abort**: Cancelling file processing (typing `n`) returns the app to `IDLE` instead of falling back to recording.

## Status
- [x] Implemented in v1.19.0.
