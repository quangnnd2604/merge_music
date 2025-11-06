# Media Mixer

Version: 1.0.0

An application that automatically merges MP3 audio files with corresponding MP4 videos or image files (JPG, JPEG, WEBP) from an input directory, creating new MP4 videos with the merged audio.

## Features

- Graphical user interface with a clean, tabbed layout
- **Batch Processing**: Automatically scan an input directory for media files and process all valid pairs.
- **Single File Processing**: Manually select an MP3, a video/image, and an output directory for a single merge operation.
- Matches MP3 files with corresponding videos or images by name.
- Supports MP4 videos and JPG/JPEG/WEBP images.
- Handles video duration adjustment (looping or trimming) to match audio length.
- Creates video from static images.
- Clear progress and error reporting in a log view.
- Preserves media quality through efficient FFmpeg commands.

## Requirements

- Python 3.x
- FFmpeg (must be installed and accessible in the system's PATH)

Required Python packages (will be installed automatically on first run):
- moviepy
- PyQt6

## Installation

1.  Ensure Python 3.x is installed on your system.
2.  Install FFmpeg (see below).
3.  Run the application. Required Python packages will be installed automatically.

### Installing FFmpeg

- **Windows**:
  1.  Download a static build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (e.g., `ffmpeg-release-full.7z`).
  2.  Extract the archive to a permanent location (e.g., `C:\ffmpeg`).
  3.  Add the `bin` folder (e.g., `C:\ffmpeg\bin`) to the system's PATH environment variable.
- **macOS** (using Homebrew):
  ```bash
  brew install ffmpeg
  ```
- **Linux** (Debian/Ubuntu):
  ```bash
  sudo apt-get update && sudo apt-get install ffmpeg
  ```

## Usage (GUI)

Run the application using the `--gui` flag:

```bash
python media_mixer.py --gui
```

The application features a tabbed interface for different processing modes.

### Tab 1: Process Directory

This tab is for batch processing an entire folder.

1.  Click **Browse** and select the main directory containing your media files.
2.  The application will scan the directory for valid pairs (MP3s and matching video/image files by name).
3.  Click **Start Processing Directory** to begin.
4.  The merged files will be saved in a `__results` subfolder inside your selected directory.

**Example Input Directory Structure:**

```
input_folder/
├── song1.mp3
├── song1.mp4       # song1.mp3 will be merged with song1.mp4
├── song2.mp3
├── song2.webp      # song2.mp3 will be merged with song2.webp
└── song3.mp3       # song3.mp3 will be ignored (no matching media)
```

### Tab 2: Process Single File

This tab is for manually merging one audio file with one media file.

1.  **Select MP3 File**: Click **Browse** and choose the MP3 audio file.
2.  **Select Media Source**: Click **Browse** and choose the video (MP4) or image (JPG, WEBP) file.
3.  **Select Output Directory**: Click **Browse** and choose the folder where the final video will be saved.
4.  Click **Start Processing Single File** to begin.

## Usage (Command Line)

For automated scripting, you can run the tool from the command line by providing the input directory path.

```bash
python media_mixer.py --input_dir /path/to/your/input_folder
```

## Error Handling

Common issues and solutions:

- **FFmpeg not found**: Ensure FFmpeg is installed and its location is added to the system's PATH.
- **File not supported**: Check that your files are in the supported formats (MP3, MP4, JPG, JPEG, WEBP).
- **Permission issues**: Ensure the application has read/write permissions for the input and output directories.

## License

This project is open source and available under the MIT License.