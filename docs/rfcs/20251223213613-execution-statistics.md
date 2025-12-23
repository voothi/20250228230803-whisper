# 20251223213613

## Title
Execution Statistics and Logging

## Staging
- **20251223213613**: Initial request to implement execution timing for each entry, suggesting reliance on ZID/OS data or adding a key. Decided to implement internal timing within the application.
- **20251223222152**: Refinement to change the log file format from `.log` (text) to `.tsv` (Tab-Separated Values) for better compatibility with spreadsheet software.
- **20251223223003**: Requirement to add headers to the TSV file. Implemented logic to auto-create headers for new files and manually updated the existing file.

## Description
Implementation of a comprehensive statistical logging system to track the performance of the transcription process. This feature provides users with real-time feedback on "Wait Time" (queue duration) and "Processing Time" (Whisper engine duration) via the console, and maintains a persistent history in a structured TSV file.

## Implementation Details
- **Timestamp Tracking**: Updated `transcription_queue` to store a 3-tuple `(path, skip_clipboard, queued_at)`. The `queued_at` timestamp is captured at the moment of insertion (recording end, clipboard scan, or CLI arg parsing).
- **Duration Calculation**: 
    - `Wait Duration` = `Start Processing Time` - `Queue Time`
    - `Process Duration` = `End Processing Time` - `Start Processing Time`
- **Console Output**: Displays filename and durations if `--stats` flag is active: `[Stats] File: ... | Wait: ... | Process: ...`.
- **TSV Logging**: 
    - File: `tmp/execution.tsv`
    - Format: `Timestamp\tFilename\tWait(s)\tProcess(s)\tModel\tLanguage`
    - Header Management: Automatically writes the header row if the file is new or empty.
- **CLI Control**: Added `--stats` argument to toggle this feature (default: off).

## Status
- [x] Implemented in v1.20.2.
