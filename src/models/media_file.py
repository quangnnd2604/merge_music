"""Media file model classes."""
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class MediaFile:
    """Base class for media files."""
    path: Path
    base_name: str
    
    @property
    def extension(self) -> str:
        """Get file extension."""
        return self.path.suffix.lower()
    
    @property
    def name(self) -> str:
        """Get file name."""
        return self.path.name

@dataclass
class AudioFile(MediaFile):
    """Audio file representation."""
    duration: float = 0.0

@dataclass
class VideoFile(MediaFile):
    """Video file representation."""
    duration: float = 0.0

@dataclass
class ImageFile(MediaFile):
    """Image file representation."""
    pass

@dataclass
class MediaPair:
    """Represents a pair of audio and media files to process."""
    audio: AudioFile
    media: MediaFile
    
    @property
    def is_video(self) -> bool:
        """Check if the media file is a video."""
        from src.config.settings import SUPPORTED_VIDEO_FORMATS
        return self.media.extension in SUPPORTED_VIDEO_FORMATS
    
    @property
    def output_name(self) -> str:
        """Generate output file name."""
        from src.config.settings import RESULT_FILE_PREFIX
        return f"{RESULT_FILE_PREFIX}{self.audio.base_name}.mp4"