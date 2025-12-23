# 20251223012133

## Title
Fragment Mode Tray Toggle and Persistence

## Staging
20251223012133
Create a setting option in the context menu of the tray icon to switch the operating mode of the utility using the usual global hotkey, as this works for the fragmented operating mode.

20251223013110
It is necessary that when selecting another language in the menu, the Fragment mode checkbox, if it was checked before selecting another language, so that it remains.

## Implementation Details
- **Tray Menu**: Added a "Fragment Mode" checkbox item.
- **Global State**: Introduced `default_fragment_mode` to track the user's preference.
- **Hotkey Behavior**: The primary hotkey now conditionally activates "Fragment Mode" (lowercase, no period) if the tray toggle is enabled.
- **Persistence**: Updated `restart.py` and argument parsing to pass the `--fragment` flag when restarting or switching languages, ensuring the toggle state is preserved.

## Status
- [x] Implemented in v1.4.12.
