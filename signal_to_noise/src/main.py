#!/usr/bin/env python3
"""
Signal to Noise - Main Entry Point

A 2D story-driven systems game where the player is the last human operator
routing messages across a fractured network.

Usage:
    python -m src.main [options]

Options:
    --low-end       Enable low-end mode for better performance
    --fullscreen    Run in fullscreen mode
    --width WIDTH   Set window width (default: 1280)
    --height HEIGHT Set window height (default: 720)
    --debug         Enable debug overlay
"""

import argparse
import sys


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Signal to Noise - A 2D story-driven systems game"
    )
    
    parser.add_argument(
        '--low-end',
        action='store_true',
        help='Enable low-end mode for better performance on weak hardware'
    )
    
    parser.add_argument(
        '--fullscreen',
        action='store_true',
        help='Run in fullscreen mode'
    )
    
    parser.add_argument(
        '--width',
        type=int,
        default=1280,
        help='Window width (default: 1280)'
    )
    
    parser.add_argument(
        '--height',
        type=int,
        default=720,
        help='Window height (default: 720)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug overlay'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Import here to avoid import errors if pygame is not installed
    try:
        from .settings import get_settings
        from .app import App
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure pygame is installed: pip install pygame")
        sys.exit(1)
    
    # Apply settings
    settings = get_settings()
    settings.SCREEN_WIDTH = args.width
    settings.SCREEN_HEIGHT = args.height
    settings.FULLSCREEN = args.fullscreen
    settings.DEBUG_OVERLAY = args.debug
    
    # Create and run application
    try:
        app = App(low_end=args.low_end)
        app.start()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
