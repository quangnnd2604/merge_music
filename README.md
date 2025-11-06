# Media Mixer

Version: 1.1.0

An app that automatically merges MP3 audio with matching MP4 videos or images (JPG, JPEG, WEBP, PNG) from an input folder to produce new MP4 videos. Supports both GUI and command-line modes.

## Features

- Clean GUI with two tabs: process directory and process single pair
- Scans a folder and auto-pairs by matching base names (e.g., `song.mp3` + `song.mp4` or `song.jpg`)
- Manual single-pair mode: pick MP3 + pick video/image + choose output folder
- Duration alignment: loops or trims video to match audio length
- Creates video from a still image
- Optional audio waveform overlay with effects:
  - Classic Bars (solid green)
  - Gradient Bars (blue → magenta → orange)
- Windows Media Player compatibility: H.264/AVC, yuv420p, Main@4.0, AAC 44.1kHz stereo, faststart
- Minimal, useful progress logging

## Requirements

- Python 3.x
- FFmpeg (installed and referenced by configuration)

Python packages (auto-installed on first run):
- moviepy
- PyQt6
- librosa
- Pillow

## Installation

1) Install Python 3.x
2) Install FFmpeg
3) Run the app; missing Python packages will be installed automatically

### Install FFmpeg

- Windows:
  1. Download a static build from https://www.gyan.dev/ffmpeg/builds/
  2. Extract to a stable location (e.g., `C:\\ffmpeg`)
  3. Add `C:\\ffmpeg\\bin` to PATH or set the path in `src/config/settings.py`
- macOS (Homebrew): `brew install ffmpeg`
- Linux (Debian/Ubuntu): `sudo apt-get update && sudo apt-get install ffmpeg`

## Configuration

- FFmpeg path: set `FFMPEG_PATH` in `src/config/settings.py:20`
- Supported formats: see `SUPPORTED_*` in `src/config/settings.py`
- Output folder: `__results` inside the input directory

## Usage (GUI)

Launch GUI:

```bash
python media_mixer.py --gui
```

### Tab 1: Process Directory

1) Click Browse and select the folder with your media
2) Optionally enable “Add audio waveform” and pick an effect
3) Click Start to process all pairs
4) Outputs are saved in the `__results` folder inside your input directory

Example structure:

```
input_folder/
  song1.mp3
  song1.mp4       # song1.mp3 will merge with song1.mp4
  song2.mp3
  song2.webp      # song2.mp3 will merge with song2.webp
  song3.mp3       # no matching media → skipped
```

### Tab 2: Process Single File

1) Pick an MP3 file
2) Pick a media file (MP4 or image JPG/WEBP/PNG)
3) Choose an output folder
4) Optionally enable waveform and choose an effect
5) Click Start to export

## Usage (Command Line)

Process a folder:

```bash
python media_mixer.py --input_dir "C:\\path\\to\\folder"
```

Note: CLI mode currently does not enable waveform.

## Output & Compatibility

- Video: H.264/AVC (`libx264`), `yuv420p`, Main@4.0, `-movflags +faststart`
- Audio: AAC 192 kbps, stereo (2 channels), 44.1 kHz
- Frame rate: fixed (30 FPS), CFR
- Frame size: scaled/padded to `1920x1080` for broad compatibility

## PowerShell Tips (Windows)

- When calling `ffmpeg.exe` with a quoted path, use the call operator `&`:

```powershell
& "C:\\Windows\\System32\\ffmpeg.exe" -hide_banner -i "C:\\path\\to\\file.mp4"
```

## Troubleshooting

- FFmpeg not found: install it and update `FFMPEG_PATH` in `src/config/settings.py`
- Media Player shows “unsupported encoding setting 0x80004005”:
  - Inspect the file with ffmpeg: `& "C:\\Windows\\System32\\ffmpeg.exe" -hide_banner -i "<file.mp4>"`
  - Ensure `Video: h264 (Main), yuv420p` and `Audio: aac, 44100 Hz, stereo`
  - The app uses these compatible settings by default
- Pair not found: make sure base names match (`After_the_Storm.mp3` + `After_the_Storm.jpg`)
- Unsupported format: see `SUPPORTED_*` in `src/config/settings.py`

## Architecture (MVC)

- Model: `src/models/media_file.py` — defines `AudioFile`, `VideoFile`, `ImageFile`, `MediaPair`
- View: `src/views/main_window.py` — GUI (PyQt6)
- Controller:
  - `src/controllers/media_controller.py` — scans folders, orchestrates processing, updates progress
  - `src/controllers/media_processor.py` — performs FFmpeg processing, renders waveform (MoviePy)
- Utilities: `src/utils/*` — helpers, package install, settings

## License

Released under the MIT License.
