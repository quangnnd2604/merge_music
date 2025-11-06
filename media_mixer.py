#!/usr/bin/env python3
"""
Media Mixer - Tool to combine audio files with video/image files.
"""
import sys
import argparse
import logging
from pathlib import Path
from src.config import settings
from src.utils import helpers
from src.controllers.media_controller import MediaController
from src.controllers.media_processor import MediaProcessor

logger = logging.getLogger(__name__)

def find_media_pairs(input_dir: str) -> tuple[MediaController, list]:
    """Find media pairs in the given directory or its immediate subdirectories."""
    # First try the input directory itself
    controller = MediaController(input_dir)
    pairs = controller.get_media_pairs()
    
    if pairs:
        return controller, pairs
        
    # If no pairs found, try scanning immediate subdirectories
    p = Path(input_dir)
    for child in sorted(p.iterdir()):
        if child.is_dir() and child.name != settings.RESULTS_FOLDER:
            try:
                sub_controller = MediaController(str(child))
                sub_pairs = sub_controller.get_media_pairs()
                if sub_pairs:
                    logger.info(f"\nFound {len(sub_pairs)} pair(s) in subfolder: {child.name}")
                    return sub_controller, sub_pairs  # Return first found pairs
            except Exception:
                continue
    
    return None, []  # No pairs found

def process_cli(input_dir: str) -> int:
    """Process media files using command line interface."""
    try:
        # Find pairs and get the appropriate controller
        controller, pairs = find_media_pairs(input_dir)
        
        if not controller or not pairs:
            logger.info("No valid pairs found to process!")
            return 0
            
        # Initialize processor and process pairs
        processor = MediaProcessor(controller.results_dir)
        total = len(pairs)
        successful = 0
        
        logger.info("\nProcessing media files...")
        for index, pair in enumerate(pairs, 1):
            try:
                processor.process_media_pair(pair)
                successful += 1
            except Exception as e:
                logger.error(f"Error processing {pair.audio.base_name}: {str(e)}")
                continue
        
        # Print summary
        logger.info(f"\nCompleted: {successful} of {total} files processed successfully")
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1

def main():
    """Main entry point."""
    # Set up logging
    helpers.setup_logging()
    
    # Parse arguments
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
    
    # Check FFmpeg first
    if not helpers.check_ffmpeg(settings.FFMPEG_PATH):
        logger.error("FFmpeg is required but not found.")
        return 1
    
    # Run in GUI mode if requested
    if args.gui:
        try:
            from src.views.main_window import run_gui
            run_gui()
            return 0
        except ImportError as e:
            logger.error("Could not start GUI. Make sure PyQt6 is installed.")
            logger.error(f"Error: {str(e)}")
            return 1
    else:
        # Command line mode requires input directory
        if not args.input_dir:
            logger.error("--input_dir is required in command line mode")
            return 1
        return process_cli(args.input_dir)

if __name__ == '__main__':
    sys.exit(main())