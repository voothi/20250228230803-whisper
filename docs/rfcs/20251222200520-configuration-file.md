# 20251222200520

## Title
Externalizing Configuration

## Staging
Move variables that can be changed into the configuration file in the same way as it was done in another project @[20241206010110-piper-tts]

## Implementation Details
Moved hardcoded variables (`whisper_faster_path`, `base_dir`, `model_path`, `hotkey`) from `whisper.py` to a new `config.ini` file.
Added `configparser` to load settings dynamically.
The `config.ini` file now controls:
- Paths to the Whisper executable and models.
- Base directory for output.
- Global hotkey configuration.

## Status
- [x] Implemented in v1.1.0
