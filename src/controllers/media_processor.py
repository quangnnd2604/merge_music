"""
Media processing implementation.

This module handles the actual media processing, including the optional
creation of audio waveforms.
"""
import subprocess
import logging
from pathlib import Path
from typing import Optional

from src.config import settings
from src.models.media_file import MediaPair
from src.utils import helpers

logger = logging.getLogger(__name__)

class MediaProcessor:
    """Handles the actual media processing operations."""
    
    def __init__(self, results_dir: Path):
        self.results_dir = results_dir
    
    def process_media_pair(self, pair: MediaPair, add_waveform: bool = False, waveform_effect: Optional[str] = None) -> None:
        """Process one audio+media pair and write an MP4 to results_dir."""
        output_path = self.results_dir / pair.output_name
        if output_path.exists():
            logger.info(f"Output file {output_path.name} exists. Overwriting.")
            output_path.unlink()

        try:
            if add_waveform:
                logger.debug("Processing with audio waveform visualization")
                self._process_with_spectrum_waveform(pair, output_path, waveform_effect)
            else:
                logger.debug("Processing with FFmpeg path")
                if pair.is_video:
                    self._process_video_ffmpeg(pair, output_path)
                else:
                    self._process_image_ffmpeg(pair, output_path)
            
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"Successfully created: {output_path.name} ({size_mb:.1f} MB)")
            else:
                raise RuntimeError("Output file was not created.")

        except Exception:
            # Let caller handle error reporting; avoid duplicate logs here.
            raise

    def _process_with_spectrum_waveform(self, pair: MediaPair, output_path: Path, waveform_effect: Optional[str] = None):
        """Processes the media pair using moviepy to add a spectrum analyzer waveform."""
        import numpy as np
        import librosa
        from PIL import Image, ImageDraw
        from moviepy.editor import (
            AudioFileClip, ImageClip, VideoFileClip, CompositeVideoClip, VideoClip
        )

        logger.debug("Analyzing audio for spectrum visualization")
        y, sr = librosa.load(str(pair.audio.path), sr=None)
        n_fft = 2048
        hop_length = 512
        stft = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
        db = librosa.amplitude_to_db(stft, ref=np.max)
        times = librosa.times_like(db, sr=sr, hop_length=hop_length, n_fft=n_fft)
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

        audio_clip = AudioFileClip(str(pair.audio.path))
        final_duration = audio_clip.duration

        # --- Main Clip Setup ---
        if pair.is_video:
            main_clip = VideoFileClip(str(pair.media.path))
            if main_clip.duration < final_duration:
                main_clip = main_clip.loop(duration=final_duration)
            elif main_clip.duration > final_duration:
                main_clip = main_clip.subclip(0, final_duration)
        else: # Is Image
            main_clip = ImageClip(str(pair.media.path), duration=final_duration)

        main_clip = main_clip.set_audio(audio_clip)
        
        # --- Waveform Visualization Logic ---
        logger.debug("Generating waveform animation")
        w, h = main_clip.size
        waveform_h = int(h * 0.15)
        n_bars = 64

        log_freqs = np.logspace(np.log10(freqs[1]), np.log10(freqs[-1]), num=n_bars + 1)

        # Helper to draw a single frame. This avoids duplicating the drawing logic.
        def _draw_spectrum_frame(t):
            img = Image.new('RGBA', (w, waveform_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            time_idx = np.searchsorted(times, t)
            if time_idx >= len(times):
                time_idx = len(times) - 1

            bar_w = w / n_bars
            for i in range(n_bars):
                freq_start, freq_end = log_freqs[i], log_freqs[i+1]
                freq_bin_start, freq_bin_end = np.searchsorted(freqs, freq_start), np.searchsorted(freqs, freq_end)
                if freq_bin_start >= freq_bin_end:
                    continue

                band_db = db[freq_bin_start:freq_bin_end, time_idx]
                max_db = np.max(band_db)
                norm_height = (max_db + 80) / 80
                norm_height = max(0, min(1, norm_height))
                bar_h = int(norm_height * waveform_h * 0.9)
                if bar_h < 1:
                    continue

                x1 = i * bar_w
                y1 = waveform_h - bar_h
                # Choose bar color based on selected effect
                if waveform_effect == "Gradient Bars":
                    # Simple left-to-right gradient from blue to magenta to orange
                    t = i / max(1, (n_bars - 1))
                    if t < 0.5:
                        # blue (0,120,255) -> magenta (200,0,200)
                        k = t / 0.5
                        r = int(0 + (200 - 0) * k)
                        g = int(120 + (0 - 120) * k)
                        b = int(255 + (200 - 255) * k)
                    else:
                        # magenta (200,0,200) -> orange (255,120,0)
                        k = (t - 0.5) / 0.5
                        r = int(200 + (255 - 200) * k)
                        g = int(0 + (120 - 0) * k)
                        b = int(200 + (0 - 200) * k)
                    color = (r, g, b, 180)
                else:
                    # Default "Classic Bars"
                    color = (0, 255, 0, 180)
                draw.rectangle([x1, y1, x1 + bar_w - 2, waveform_h], fill=color)
            return np.array(img)

        # Create the RGB clip and the Alpha mask clip separately
        def make_frame_rgb(t):
            return _draw_spectrum_frame(t)[:,:,:3] # Return only RGB channels

        def make_frame_mask(t):
            return _draw_spectrum_frame(t)[:,:,3] / 255.0 # Return normalized alpha channel

        waveform_clip = VideoClip(make_frame_rgb, duration=final_duration)
        mask_clip = VideoClip(make_frame_mask, duration=final_duration, ismask=True)

        # Apply the mask to the waveform clip
        waveform_clip.mask = mask_clip

        # --- Composition ---
        logger.info("Compositing video and waveform...")
        final_video = CompositeVideoClip([
            main_clip,
            waveform_clip.set_pos(('center', 'bottom'))
        ])

        # --- Write to File ---
        logger.info(f"Writing final video to {output_path.name}...")
        final_video.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            audio_bitrate=settings.DEFAULT_AUDIO_BITRATE,
            temp_audiofile=str(self.results_dir / "temp-audio.m4a"),
            threads=4,
            fps=settings.DEFAULT_FRAMERATE,
            preset=settings.DEFAULT_VIDEO_PRESET,
            ffmpeg_params=[
                '-pix_fmt', 'yuv420p',
                '-profile:v', 'main',
                '-level', '4.0',
                '-tag:v', 'avc1',
                '-r', str(settings.DEFAULT_FRAMERATE),
                '-vsync', 'cfr',
                '-vf', settings.FFMPEG_VIDEO_FILTERS,
                '-ac', '2', '-ar', '44100',
                '-movflags', '+faststart'
            ]
        )

    def _process_video_ffmpeg(self, pair: MediaPair, output_path: Path):
        """Create an MP4 using video input re-encoded for compatibility."""
        video_duration = helpers.get_video_duration(settings.FFMPEG_PATH, str(pair.media.path))
        common_encode = [
            '-c:v', 'libx264',
            '-preset', settings.DEFAULT_VIDEO_PRESET,
            '-profile:v', 'main',
            '-level', '4.0',
            '-tag:v', 'avc1',
            '-pix_fmt', 'yuv420p',
            '-vf', settings.FFMPEG_VIDEO_FILTERS,
            '-r', str(settings.DEFAULT_FRAMERATE),
            '-vsync', 'cfr',
            '-c:a', 'aac', '-b:a', settings.DEFAULT_AUDIO_BITRATE,
            '-ac', '2', '-ar', '44100',
            '-movflags', '+faststart',
            '-threads', '4'
        ]

        if video_duration < pair.audio.duration:
            loops = int(pair.audio.duration / video_duration) + 1
            logger.info(f"Looping video {loops} times to match audio duration")
            cmd = [
                settings.FFMPEG_PATH, '-y',
                '-stream_loop', str(loops - 1),
                '-i', str(pair.media.path),
                '-i', str(pair.audio.path),
                '-t', str(pair.audio.duration),
                *common_encode,
                '-shortest', str(output_path)
            ]
        else:
            logger.info(f"Trimming video to {pair.audio.duration} seconds")
            cmd = [
                settings.FFMPEG_PATH, '-y',
                '-i', str(pair.media.path),
                '-i', str(pair.audio.path),
                '-t', str(pair.audio.duration),
                *common_encode,
                '-shortest', str(output_path)
            ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

    def _process_image_ffmpeg(self, pair: MediaPair, output_path: Path):
        logger.info("Creating video with audio from image...")
        cmd = [
            settings.FFMPEG_PATH, '-y',
            '-loop', '1', '-framerate', str(settings.DEFAULT_FRAMERATE),
            '-i', str(pair.media.path),
            '-i', str(pair.audio.path),
            '-t', str(pair.audio.duration),
            '-c:v', 'libx264', '-preset', settings.DEFAULT_VIDEO_PRESET, '-tune', 'stillimage',
            '-profile:v', 'main', '-level', '4.0', '-tag:v', 'avc1',
            '-pix_fmt', 'yuv420p',
            '-vf', settings.FFMPEG_VIDEO_FILTERS,
            '-r', str(settings.DEFAULT_FRAMERATE), '-vsync', 'cfr',
            '-c:a', 'aac', '-b:a', settings.DEFAULT_AUDIO_BITRATE, '-ac', '2', '-ar', '44100',
            '-threads', '4', '-movflags', '+faststart',
            str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

