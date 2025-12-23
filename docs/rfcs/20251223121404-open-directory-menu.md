# 20251223121404

## Title
Open Files Directory Menu Item

## Staging
20251223121404
Add a menu item that allows you to go to the directory with files.
base_directory

## Implementation Details
### Analytics
- **User Friction**: Identifying output files (WAV, SRT, TXT) required manual navigation to the `base_directory`, which is often nested or temporary (`tmp`). This slowed down the workflow for users verifying or moving their transcriptions.
- **Environment**: The target OS is Windows, which suggests a preference for native file explorer integration.

### Decisions
- **Native Integration**: Decided to use `os.startfile(base_dir)`. This choice leverages the Windows shell to open the directory, providing a familiar and reliable user experience compared to manually invoking `subprocess.run(["explorer", ...])`.
- **Menu Hierarchy**: Placed the "Open Files" item at the very top of the system tray menu. This decision reflects the high frequency of this use case and ensures it is the easiest item to locate.
- **Robustness**: Wrapped the directory opening in a try-except block. Even if the `base_directory` is deleted or inaccessible, the application logic continues without interruption, merely logging the failure to the console.


## Status
- [x] Implemented in v1.14.16.
