"""Media processing implementation."""
import subprocess
import logging
from pathlib import Path
from src.config import settings
from src.models.media_file import MediaPair
from src.utils import helpers

logger = logging.getLogger(__name__)

class MediaProcessor:
    """Handles the actual media processing operations."""
    
    def __init__(self, results_dir: Path):
        """Initialize the processor."""
        self.results_dir = results_dir
    
    def process_media_pair(self, pair: MediaPair) -> None:
        """Process a single audio-media pair."""
        try:
            # Generate output path
            output_path = self.results_dir / pair.output_name
            if output_path.exists():
                output_path.unlink()
            
            # Process based on media type
            if pair.is_video:
                self._process_video(pair, output_path)
            else:
                self._process_image(pair, output_path)
            
            # Log success
            size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"Created: {output_path.name} ({size_mb:.1f} MB)")            # Clean up intermediate temp files unless user requested to preserve them
            try:
                if not settings.PRESERVE_TEMP:
                    # remove temp video if present
                    temp_video = self.temp_dir / settings.TEMP_VIDEO_NAME
                    if temp_video.exists():
                        temp_video.unlink()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error processing {pair.audio.base_name}: {str(e)}\n")
            raise
    
    def _process_video(
        self, 
        pair: MediaPair,
        output_path: Path
    ) -> None:
        """Process a video-audio pair."""
        # Get video duration directly
        video_duration = helpers.get_video_duration(
            settings.FFMPEG_PATH, 
            str(pair.media.path)
        )

        # Process video and add audio in one step
        if video_duration < pair.audio.duration:
            # Need to loop video
            loops = int(pair.audio.duration / video_duration) + 1
            logger.info(f"Looping video {loops} times to match audio duration")
            
            subprocess.run([
                settings.FFMPEG_PATH, '-y',
                '-stream_loop', str(loops-1),  # -1 means infinite loop
                '-i', str(pair.media.path),
                '-i', str(pair.audio.path),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', settings.DEFAULT_AUDIO_BITRATE,
                '-shortest',
                '-movflags', '+faststart',
                str(output_path)
            ], check=True, capture_output=True, text=True)
        else:
            # Need to trim video
            logger.info(f"Trimming video to {pair.audio.duration} seconds")
            subprocess.run([
                settings.FFMPEG_PATH, '-y',
                '-i', str(pair.media.path),
                '-i', str(pair.audio.path),
                '-t', str(pair.audio.duration),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', settings.DEFAULT_AUDIO_BITRATE,
                '-shortest',
                '-movflags', '+faststart',
                str(output_path)
            ], check=True, capture_output=True, text=True)
    
    def _process_image(
        self, 
        pair: MediaPair,
        output_path: Path
    ) -> None:
        """Process an image-audio pair."""
        logger.info("Creating video with audio from image...")
        subprocess.run([
            settings.FFMPEG_PATH, '-y',
            '-loop', '1',
            '-framerate', str(settings.DEFAULT_FRAMERATE),
            '-i', str(pair.media.path),
            '-i', str(pair.audio.path),
            '-t', str(pair.audio.duration),
            '-c:v', 'libx264',
            '-preset', settings.DEFAULT_VIDEO_PRESET,
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', settings.DEFAULT_AUDIO_BITRATE,
            '-vf', settings.FFMPEG_VIDEO_FILTERS,
            '-pix_fmt', 'yuv420p',
            '-r', str(settings.DEFAULT_FRAMERATE),
            '-threads', '4',
            '-movflags', '+faststart',
            str(output_path)
        ], check=True, capture_output=True, text=True)
    
    def _loop_video(
        self, 
        input_path: Path, 
        output_path: Path, 
        target_duration: float
    ) -> None:
        """Loop a video to match target duration."""
        video_duration = helpers.get_video_duration(
            settings.FFMPEG_PATH, 
            str(input_path)
        )
        loops = int(target_duration / video_duration) + 1
        logger.info(f"Looping video {loops} times to match audio duration")
        
        # Create concat file
        concat_file = self.temp_dir / settings.CONCAT_FILE_NAME
        with concat_file.open('w') as f:
            for _ in range(loops):
                f.write(f"file '{input_path}'\n")
        
        # Concatenate video
        subprocess.run([
            settings.FFMPEG_PATH, '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            str(output_path)
        ], check=True, capture_output=True, text=True)
        
        # Cleanup concat file
        concat_file.unlink()
    
    def _trim_video(
        self, 
        input_path: Path, 
        output_path: Path, 
        duration: float
    ) -> None:
        """Trim a video to specified duration."""
        logger.info(f"Trimming video to {duration} seconds")
        subprocess.run([
            settings.FFMPEG_PATH, '-y',
            '-i', str(input_path),
            '-t', str(duration),
            '-c', 'copy',
            str(output_path)
        ], check=True, capture_output=True, text=True)
    
    def _add_audio_to_video(
        self, 
        video_path: Path, 
        pair: MediaPair, 
        output_path: Path
    ) -> None:
        """Add audio to a video file."""
        logger.info("Step 2/2: Adding audio...")
        subprocess.run([
            settings.FFMPEG_PATH, '-y',
            '-i', str(video_path),
            '-i', str(pair.audio.path),
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', settings.DEFAULT_AUDIO_BITRATE,
            '-shortest',
            '-movflags', '+faststart',
            str(output_path)
        ], check=True, capture_output=True, text=True)