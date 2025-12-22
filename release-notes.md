# Release Notes

## [v1.1.0] - 2025-12-22

### Added
-   **Configuration File Support**: Moved all configurable paths and settings to an external `config.ini` file. This allows for easier setup and portability without modifying the source code.
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
