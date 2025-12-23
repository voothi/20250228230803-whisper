# Release Notes

## [v1.19.2] - 2025-12-23
### Documentation
- **RFC Traceability**: Standardized and linked all session RFCs to release notes for improved historical tracking.
- **Detailed Staging**: Updated the External Audio Processing RFC with specific ZID-to-requirement mappings for all 14 project stages.

## [v1.19.0] - 2025-12-23
### Added
- **External Audio File Processing**: Support for transcribing existing files via CLI arguments or Clipboard Scanner. ([RFC: 20251223125117](./docs/rfcs/20251223125117-external-audio-processing.md))
- **Clipboard Scanner Mode**: Automatically detect audio/video paths in clipboard and prompt for transcription.
- **Smart Naming Convention**: Integrated language postfixes (e.g., `.en.srt`) and collision handling (e.g., `.1.en.srt`).
- **Waiting State**: New tray icon color (**Gray**) indicates application is waiting for console input.
- **Input Blocking**: State-aware safety guards prevent triggers from interfering with active processing or input prompts.
- **Cross-Drive Support**: Reliable file handling across different disk partitions using `shutil.move`.
- **UI Persistence**: Smarter setting persistence when switching languages vs. full application restart.
- **Microphone Lockout**: Exclusive mode for "File Processing" to prevent concurrent state corruption.

## [v1.15.0] - 2025-12-23

### Added
-   **External Audio Processing**: Major update enabling transcription of existing files without recording. ([RFC: 20251223125117](./docs/rfcs/20251223125117-external-audio-processing.md))
-   **Clipboard Scanner Mode**: Toggleable mode to scan clipboard for file paths (MP3, WAV, MP4, etc.) and transcribe them upon hotkey press. Includes console-based confirmation.
-   **Multi-File CLI Support**: Pass multiple file paths directly as arguments (e.g., `python whisper.py file1.mp3 file2.wav`).
-   **Smart File Naming**: Implemented `get_unique_path` to handle existing output files by adding incrementing suffixes (`.1`, `.2`, etc.), preventing data overwrite.
-   **Temporary Processing**: Transcriptions are now performed in the `tmp` directory before being moved to their final location, improving file safety.

## [v1.14.16] - 2025-12-23

### Added
-   **Open Files Directory**: Added a "Open Files" menu item to the system tray context menu. This allows users to quickly open the directory containing their audio recordings and transcription files. ([RFC: 20251223121404](./docs/rfcs/20251223121404-open-directory-menu.md))


## [v1.4.14] - 2025-12-23

### Fixed
-   **Hotkey Reliability**: Fixed an issue where global hotkeys (`Ctrl+Alt+E`, `Ctrl+Alt+F`) would fail when using non-English keyboard layouts (e.g., Russian). The hotkeys are now layout-independent and trigger based on physical key usage. ([RFC: 20251223104014](./docs/rfcs/20251223104014-hotkey-fix.md))

## [v1.4.12] - 2025-12-23

### Added
-   **Fragment Mode Toggle**: Added a checkable option in the system tray menu to toggle "Fragment Mode" for the primary hotkey. ([RFC: 20251223012133](./docs/rfcs/20251223012133-fragment-mode-toggle.md))
    -   **Behavior**: When checked, the standard hotkey performs fragment transcription (lowercase, no period).
    -   **Persistence**: The state of this toggle is preserved even when switching languages (restarting the application).


## [v1.4.8] - 2025-12-23

### Documentation
-   **RFC Standardization**: Standardized all Request for Comment (RFC) documents to follow a consistent template and linked them directly from the release notes for better traceability. ([RFC: 20251223005037](./docs/rfcs/20251223005037-rfc-standardization.md))


## [v1.4.4] - 2025-12-23

### Changed
-   **Restart Behavior**: The "Restart" tray option now explicitly resets the application to its default state, removing any previously selected language overrides. ([RFC: 20251223002401](./docs/rfcs/20251223002401-restart-reset.md))

## [v1.4.2] - 2025-12-23

### Added
-   **Fragment Mode**: Introduced a new transcription mode for seamless integration into mid-sentence contexts (e.g., Anki cards, chat messages). ([RFC: 20251223000536](./docs/rfcs/20251223000536-fragment-mode.md))
    -   **Behavior**: Transcribed text automatically starts with a **lowercase** letter and has **no trailing period**.
    -   **Hotkey**: Triggered by a dedicated hotkey (Default: `<ctrl>+<alt>+f`).
    -   **Configuration**: Added `hotkey_fragment` setting to `config.ini` to customize this shortcut.
-   **Enhanced Feedback**: The console output now intelligently prompts the user with the correct hotkey to stop recording, depending on which mode (Normal vs. Fragment) is active.

## [v1.2.2] - 2025-12-22

### Architecture
-   **Automatic Programming Pattern (Functional FSM)**: Refactored the internal engine to use a robust Functional Finite State Machine. ([RFC: 20251222233401](./docs/rfcs/20251222233401-fsm-pattern.md))
    -   **Strict State Control**: The application now operates in strict `IDLE` (Blue), `RECORDING` (Red), or `PROCESSING` (Yellow) states.
    -   **Centralized Transitions**: All status changes flow through a single `set_state()` function, eliminating race conditions.
    -   **Reliability**: Sequential processing and tray icon updates are now guaranteed by the state machine logic.
-   **Dependencies**: Added `sounddevice` logic validation within the new state architecture.

## [v1.1.0] - 2025-12-22

### Added
-   **Configuration File Support**: Moved all configurable paths and settings to an external `config.ini` file. This allows for easier setup and portability without modifying the source code. ([RFC: 20251222200520](./docs/rfcs/20251222200520-configuration-file.md))
-   **Turbo Model Support**: Added support for the `large-v3-turbo` model.
    -   *Note*: The turbo model is currently the best choice for a balance of high transcription quality and processing speed.
-   **Project Restructure**: Organized codebase with `config.ini.template` and improved path handling via `pathlib`.

### Changed
-   Updated hardcoded paths in `whisper.py` to load dynamically from `config.ini`.
-   Refactored `restart.py` integration for smoother language switching.

---

## [v1.0.0] - Initial Version

### Features
-   Basic audio recording via global hotkeys.
-   Integration with Faster-Whisper executable.
-   System tray support with status indication.
-   Clipboard integration for transcribed text.
