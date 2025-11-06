"""Application settings and constants."""
import os
from pathlib import Path

# Supported file formats
SUPPORTED_VIDEO_FORMATS = ['.mp4']
SUPPORTED_AUDIO_FORMATS = ['.mp3']
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.webp', '.png']

# Folder names
RESULTS_FOLDER = '__results'  # Main results folder in input directory

# File name patterns
RESULT_FILE_PREFIX = ''
TEMP_VIDEO_NAME = 'temp_video.mp4'
TEMP_SILENT_VIDEO_NAME = 'temp_silent.mp4'
CONCAT_FILE_NAME = 'concat.txt'

# FFmpeg settings
FFMPEG_PATH = r"C:\Windows\System32\ffmpeg.exe"
DEFAULT_FRAMERATE = 30
DEFAULT_AUDIO_BITRATE = '192k'
DEFAULT_VIDEO_PRESET = 'ultrafast'
VIDEO_DIMENSIONS = '1920:1080'

# FFmpeg commands
FFMPEG_VIDEO_FILTERS = f'scale={VIDEO_DIMENSIONS}:force_original_aspect_ratio=decrease,pad={VIDEO_DIMENSIONS}:(ow-iw)/2:(oh-ih)/2'

# Logging format
LOG_FORMAT = '%(message)s'
LOG_LEVEL = 'INFO'

# Preserve temporary files (set to True to keep __results/temp for debugging)
PRESERVE_TEMP = False