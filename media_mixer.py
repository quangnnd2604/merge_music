"""
Media Mixer - Tool to combine audio files with video/image files.
"""
import sys
import argparse
import logging
from pathlib import Path

from src.utils.package_manager import check_and_install_dependencies

# Perform dependency check as early as possible
if not check_and_install_dependencies():
    print("Error: Failed to install required dependencies. Please install them manually.", file=sys.stderr)
    sys.exit(1)

# Now that dependencies are checked, we can import the rest of the app
from src.config import settings
from src.utils import helpers

logger = logging.getLogger(__name__)

def process_cli(input_dir: str) -> int:
    """Process media files using command line interface."""
    # Local import to avoid loading heavy modules if not needed
    from src.controllers.media_controller import MediaController
    from src.controllers.media_processor import MediaProcessor

    try:
        controller = MediaController()
        # Note: The CLI does not support waveform generation yet.
        # The controller's directory processing task is now the primary method.
        controller.progress_update.connect(logger.info)
        controller.processing_finished.connect(lambda success: logger.info("CLI processing finished."))
        
        # This is a blocking call for the CLI version
        controller._directory_processing_task(input_dir, add_waveform=False)
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1

def main():
    """Main entry point."""
    helpers.setup_logging()
    
    parser = argparse.ArgumentParser(
        description='Media Mixer - Automatically mix audio with video/image files.'
    )
    parser.add_argument(
        '--input_dir',
        type=str,
        help='Path to the input directory containing media files'
    )
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Start graphical user interface'
    )
    
    args = parser.parse_args()
    
    if not helpers.check_ffmpeg(settings.FFMPEG_PATH):
        logger.error("FFmpeg is required but not found.")
        return 1
    
    if args.gui:
        # Local import for GUI mode
        from src.views.main_window import run_gui
        run_gui()
        return 0
    else:
        if not args.input_dir:
            logger.error("--input_dir is required in command line mode")
            return 1
        return process_cli(args.input_dir)

if __name__ == '__main__':
    sys.exit(main())
