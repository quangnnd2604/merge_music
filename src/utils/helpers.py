"""Utility functions for media processing."""
import os
import re
import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

def setup_logging():
    """Configure logging with the specified format."""
    from src.config.settings import LOG_FORMAT, LOG_LEVEL
    # Allow LOG_LEVEL to be a string like 'INFO'
    level = LOG_LEVEL
    if isinstance(LOG_LEVEL, str):
        level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(level=level, format=LOG_FORMAT)


def _config_path() -> Path:
    """Return path to the user config file used by the GUI for persistence."""
    # Store config in the project root (three levels up from this file: utils -> src -> project)
    try:
        project_root = Path(__file__).resolve().parents[2]
        return project_root / '.media_mixer_config.json'
    except Exception:
        # Fallback to home directory if anything goes wrong
        return Path.home() / '.media_mixer_config.json'


def load_last_input_dir() -> Optional[str]:
    """Load last used input directory from a small JSON config file.

    Returns the directory string or None if not set.
    """
    cfg = _config_path()
    if not cfg.exists():
        return None
    try:
        data = json.loads(cfg.read_text(encoding='utf-8'))
        val = data.get('last_input_dir')
        if val and Path(val).exists():
            return val
    except Exception:
        return None
    return None


def save_last_input_dir(path: str) -> None:
    """Save last used input directory to a small JSON config file."""
    cfg = _config_path()
    try:
        cfg.write_text(json.dumps({'last_input_dir': path}), encoding='utf-8')
    except Exception:
        pass

def check_ffmpeg(ffmpeg_path: str) -> bool:
    """
    Check if FFmpeg is installed and working.
    
    Args:
        ffmpeg_path: Path to FFmpeg executable
        
    Returns:
        bool: True if FFmpeg is available and working
    """
    if not os.path.exists(ffmpeg_path):
        logger.error("FFmpeg not found. Please install FFmpeg first.")
        return False
    
    try:
        subprocess.run([ffmpeg_path, '-version'], capture_output=True, text=True)
        return True
    except Exception as e:
        logger.error(f"Error running FFmpeg: {str(e)}")
        return False

def get_video_duration(ffmpeg_path: str, video_path: str) -> float:
    """
    Get the duration of a video file using FFmpeg.
    
    Args:
        ffmpeg_path: Path to FFmpeg executable
        video_path: Path to the video file
        
    Returns:
        float: Duration in seconds
    """
    result = subprocess.run(
        [ffmpeg_path, '-i', video_path, '-f', 'null', '-'],
        stderr=subprocess.PIPE,
        text=True
    )
    
    duration_match = re.search(
        r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})',
        result.stderr
    )
    
    if duration_match:
        h, m, s, ms = map(int, duration_match.groups())
        return h * 3600 + m * 60 + s + ms / 100
    
    raise ValueError("Could not determine video duration")

def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, create it if it doesn't.
    
    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(exist_ok=True, parents=True)

def cleanup_directory(path: Path) -> None:
    """
    Remove a directory and all its contents.
    
    Args:
        path: Directory path to clean up
    """
    try:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    except:
        pass

def generate_output_path(results_dir: Path, base_name: str) -> Path:
    """
    Generate the output file path for a processed media file.
    
    Args:
        results_dir: Directory to store results
        base_name: Base name for the output file
        
    Returns:
        Path: Generated output path
    """
    from src.config.settings import RESULT_FILE_PREFIX
    return results_dir / f"{RESULT_FILE_PREFIX}{base_name}.mp4"