#!/usr/bin/env python3
"""
Script to pre-download all Google Fonts for PDF generation.

This script downloads all available Google Fonts to the fonts directory
so they're ready for immediate use in PDF generation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.font_manager import get_font_manager, GOOGLE_FONTS


def download_all_fonts():
    """Download all available Google Fonts."""
    font_manager = get_font_manager()

    print("=" * 60)
    print("Downloading Google Fonts for PDF Generation")
    print("=" * 60)
    print()

    total_fonts = len(GOOGLE_FONTS)
    successful = 0
    failed = []

    for i, font_name in enumerate(GOOGLE_FONTS.keys(), 1):
        print(f"[{i}/{total_fonts}] Processing {font_name}...")

        if font_manager.register_font(font_name):
            successful += 1
            print(f"  ✓ Successfully registered {font_name}")
        else:
            failed.append(font_name)
            print(f"  ✗ Failed to register {font_name}")

        print()

    # Summary
    print("=" * 60)
    print("Download Summary")
    print("=" * 60)
    print(f"Total fonts: {total_fonts}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(failed)}")

    if failed:
        print()
        print("Failed fonts:")
        for font in failed:
            print(f"  - {font}")

    print()
    print("Fonts directory:", font_manager.fonts_dir)
    print("=" * 60)


if __name__ == '__main__':
    try:
        download_all_fonts()
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)
