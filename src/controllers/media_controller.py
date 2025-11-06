"""Media processing controller.

This module orchestrates media processing tasks by acting as the bridge
between the user interface (View) and the data models/processing logic (Model).
It uses a QObject-based approach to run tasks in a separate thread and
communicate with the UI via signals.
"""
import logging
from pathlib import Path
from typing import List
from moviepy.editor import AudioFileClip

from PyQt6.QtCore import QObject, pyqtSignal, QThread

from src.config import settings
from src.models.media_file import AudioFile, VideoFile, ImageFile, MediaPair
from src.controllers.media_processor import MediaProcessor
from src.utils import helpers

logger = logging.getLogger(__name__)

class Worker(QObject):
    """
    A worker that executes a function in a separate thread.
    Emits signals for progress and completion.
    """
    progress_update = pyqtSignal(str)
    progress_value = pyqtSignal(int)
    processing_finished = pyqtSignal(bool)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """Execute the worker's function."""
        try:
            self.func(*self.args, **self.kwargs)
            self.processing_finished.emit(True)
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            self.progress_update.emit(f"\nFatal error: {str(e)}")
            self.processing_finished.emit(False)


class MediaController(QObject):
    """
    Controller for media processing operations. Inherits from QObject to use signals.
    """
    # Signals to communicate with the View
    progress_update = pyqtSignal(str)
    progress_value = pyqtSignal(int)
    processing_finished = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None

    def _run_in_thread(self, func, *args, **kwargs):
        """Helper to run a function in a background thread."""
        self.thread = QThread()
        self.worker = Worker(func, *args, **kwargs)
        self.worker.moveToThread(self.thread)

        # Connect worker signals to controller signals
        self.worker.progress_update.connect(self.progress_update)
        self.worker.progress_value.connect(self.progress_value)
        self.worker.processing_finished.connect(self._on_processing_finished)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def _on_processing_finished(self, success):
        """Clean up thread and emit finished signal."""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None
        self.processing_finished.emit(success)

    def process_directory(self, input_dir_str: str):
        """
        Scans a directory for media pairs and processes them.
        This method is designed to be run in a background thread.
        """
        self._run_in_thread(self._directory_processing_task, input_dir_str)

    def _directory_processing_task(self, input_dir_str: str):
        """The actual logic for directory processing."""
        input_dir = Path(input_dir_str)
        if not input_dir.is_dir():
            self.progress_update.emit("Error: Invalid input directory.")
            return

        # 1. Scan for pairs
        self.progress_update.emit("Scanning for media pairs...")
        pairs = self._scan_for_pairs(input_dir)

        if not pairs:
            self.progress_update.emit("No valid media pairs found in the selected directory.")
            return

        # 2. Process pairs
        results_dir = input_dir / settings.RESULTS_FOLDER
        helpers.ensure_directory(results_dir)
        processor = MediaProcessor(results_dir)
        
        self.progress_update.emit(f"Found {len(pairs)} pairs to process.")
        total = len(pairs)
        for index, pair in enumerate(pairs, 1):
            try:
                media_type = "Video" if pair.is_video else "Image"
                self.progress_update.emit(
                    f"\nProcessing {index}/{total}: {pair.audio.name} + {pair.media.name} ({media_type})"
                )
                processor.process_media_pair(pair)
                self.progress_value.emit(int((index / total) * 100))
            except Exception as e:
                self.progress_update.emit(f"Error processing {pair.audio.base_name}: {str(e)}")
        
        self.progress_update.emit("\nDirectory processing complete.")

    def _scan_for_pairs(self, input_dir: Path) -> List[MediaPair]:
        """Scans a directory and returns a list of MediaPairs."""
        audio_files = {}
        video_files = {}
        image_files = {}

        for f in input_dir.iterdir():
            if not f.is_file():
                continue
            ext = f.suffix.lower()
            base_name = f.stem
            if ext in settings.SUPPORTED_AUDIO_FORMATS:
                clip = AudioFileClip(str(f))
                audio_files[base_name] = AudioFile(path=f, base_name=base_name, duration=clip.duration)
                clip.close()
            elif ext in settings.SUPPORTED_VIDEO_FORMATS:
                video_files.setdefault(base_name, []).append(VideoFile(path=f, base_name=base_name))
            elif ext in settings.SUPPORTED_IMAGE_FORMATS:
                image_files.setdefault(base_name, []).append(ImageFile(path=f, base_name=base_name))

        pairs = []
        for base_name, audio_file in audio_files.items():
            media_file = None
            if base_name in video_files:
                media_file = sorted(video_files[base_name], key=lambda x: x.path.name)[0]
            elif base_name in image_files:
                media_file = sorted(image_files[base_name], key=lambda x: (settings.SUPPORTED_IMAGE_FORMATS.index(x.extension), x.path.name))[0]
            
            if media_file:
                pairs.append(MediaPair(audio=audio_file, media=media_file))
        return pairs

    def process_single_pair(self, mp3_path_str: str, media_path_str: str, output_dir_str: str):
        """
        Processes a single, user-selected pair of media files.
        """
        self._run_in_thread(self._single_file_processing_task, mp3_path_str, media_path_str, output_dir_str)

    def _single_file_processing_task(self, mp3_path_str: str, media_path_str: str, output_dir_str: str):
        """The actual logic for single file processing."""
        try:
            # 1. Create Models from paths
            audio_path = Path(mp3_path_str)
            media_path = Path(media_path_str)
            results_dir = Path(output_dir_str)

            helpers.ensure_directory(results_dir)

            self.progress_update.emit("Analyzing files...")
            self.progress_value.emit(5)

            audio_clip = AudioFileClip(str(audio_path))
            audio_file = AudioFile(path=audio_path, base_name=audio_path.stem, duration=audio_clip.duration)
            audio_clip.close()

            media_ext = media_path.suffix.lower()
            if media_ext in settings.SUPPORTED_VIDEO_FORMATS:
                media_file = VideoFile(path=media_path, base_name=media_path.stem)
            elif media_ext in settings.SUPPORTED_IMAGE_FORMATS:
                media_file = ImageFile(path=media_path, base_name=media_path.stem)
            else:
                raise ValueError("Unsupported media file type.")

            media_pair = MediaPair(audio=audio_file, media=media_file)
            
            # 2. Process the pair
            processor = MediaProcessor(results_dir)
            media_type = "Video" if media_pair.is_video else "Image"
            self.progress_update.emit(
                f"Processing: {media_pair.audio.name} + {media_pair.media.name} ({media_type})"
            )
            self.progress_value.emit(10)

            processor.process_media_pair(media_pair)
            
            self.progress_value.emit(100)
            self.progress_update.emit("Single file processing complete.")

        except Exception as e:
            # Re-raise to be caught by the main worker exception handler
            raise e
