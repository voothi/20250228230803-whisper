# Release Notes

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
