"""
Font Manager for PDF Generation.

Handles downloading and registering Google Fonts for use with ReportLab.
"""

import os
import requests
from pathlib import Path
from typing import Dict, Optional
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Define available Google Fonts with their download URLs
# These are direct links to TTF files from Google Fonts
GOOGLE_FONTS = {
    'Roboto': {
        'regular': 'https://github.com/google/roboto/raw/main/src/hinted/Roboto-Regular.ttf',
        'bold': 'https://github.com/google/roboto/raw/main/src/hinted/Roboto-Bold.ttf',
        'italic': 'https://github.com/google/roboto/raw/main/src/hinted/Roboto-Italic.ttf'
    },
    'Open Sans': {
        'regular': 'https://github.com/googlefonts/opensans/raw/main/fonts/ttf/OpenSans-Regular.ttf',
        'bold': 'https://github.com/googlefonts/opensans/raw/main/fonts/ttf/OpenSans-Bold.ttf',
        'italic': 'https://github.com/googlefonts/opensans/raw/main/fonts/ttf/OpenSans-Italic.ttf'
    },
    'Lato': {
        'regular': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf',
        'bold': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Bold.ttf',
        'italic': 'https://github.com/google/fonts/raw/main/ofl/lato/Lato-Italic.ttf'
    },
    'Montserrat': {
        'regular': 'https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Regular.ttf',
        'bold': 'https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf',
        'italic': 'https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Italic.ttf'
    },
    'Merriweather': {
        'regular': 'https://github.com/google/fonts/raw/main/ofl/merriweather/Merriweather-Regular.ttf',
        'bold': 'https://github.com/google/fonts/raw/main/ofl/merriweather/Merriweather-Bold.ttf',
        'italic': 'https://github.com/google/fonts/raw/main/ofl/merriweather/Merriweather-Italic.ttf'
    },
    'Playfair Display': {
        'regular': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-Regular.ttf',
        'bold': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-Bold.ttf',
        'italic': 'https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-Italic.ttf'
    },
    'Comic Neue': {
        'regular': 'https://github.com/google/fonts/raw/main/ofl/comicneue/ComicNeue-Regular.ttf',
        'bold': 'https://github.com/google/fonts/raw/main/ofl/comicneue/ComicNeue-Bold.ttf',
        'italic': 'https://github.com/google/fonts/raw/main/ofl/comicneue/ComicNeue-Italic.ttf'
    },
    'Quicksand': {
        'regular': 'https://github.com/google/fonts/raw/main/ofl/quicksand/Quicksand-Regular.ttf',
        'bold': 'https://github.com/google/fonts/raw/main/ofl/quicksand/Quicksand-Bold.ttf',
        'italic': 'https://github.com/google/fonts/raw/main/ofl/quicksand/Quicksand-Regular.ttf'  # No italic
    },
    'Nunito': {
        'regular': 'https://github.com/google/fonts/raw/main/ofl/nunito/Nunito-Regular.ttf',
        'bold': 'https://github.com/google/fonts/raw/main/ofl/nunito/Nunito-Bold.ttf',
        'italic': 'https://github.com/google/fonts/raw/main/ofl/nunito/Nunito-Italic.ttf'
    }
}

# Built-in ReportLab fonts (no download needed)
BUILTIN_FONTS = {
    'Helvetica': 'Helvetica',
    'Times-Roman': 'Times-Roman',
    'Courier': 'Courier'
}


class FontManager:
    """Manages font downloads and registration for PDF generation."""

    def __init__(self, fonts_dir: Optional[Path] = None):
        """
        Initialize the font manager.

        Args:
            fonts_dir: Directory to store downloaded fonts. If None, uses src/fonts.
        """
        if fonts_dir is None:
            # Default to src/fonts directory
            fonts_dir = Path(__file__).parent.parent / 'fonts'

        self.fonts_dir = Path(fonts_dir)
        self.fonts_dir.mkdir(parents=True, exist_ok=True)

        # Track registered fonts
        self._registered_fonts = set()

    def download_font(self, font_name: str, style: str = 'regular') -> Optional[Path]:
        """
        Download a Google Font if not already present.

        Args:
            font_name: Name of the font (e.g., 'Roboto')
            style: Font style ('regular', 'bold', 'italic')

        Returns:
            Path to the downloaded font file, or None if download fails
        """
        if font_name not in GOOGLE_FONTS:
            print(f"Font '{font_name}' not in available fonts list")
            return None

        if style not in GOOGLE_FONTS[font_name]:
            print(f"Style '{style}' not available for font '{font_name}'")
            return None

        # Create safe filename
        safe_name = font_name.replace(' ', '')
        filename = f"{safe_name}-{style.capitalize()}.ttf"
        file_path = self.fonts_dir / filename

        # Check if already downloaded
        if file_path.exists():
            return file_path

        # Download the font
        try:
            url = GOOGLE_FONTS[font_name][style]
            print(f"Downloading {font_name} ({style}) from {url}...")

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Save to file
            with open(file_path, 'wb') as f:
                f.write(response.content)

            print(f"Successfully downloaded {font_name} ({style}) to {file_path}")
            return file_path

        except Exception as e:
            print(f"Error downloading {font_name} ({style}): {e}")
            return None

    def register_font(self, font_name: str) -> bool:
        """
        Register a font with ReportLab for PDF generation.

        Args:
            font_name: Name of the font to register

        Returns:
            True if successful, False otherwise
        """
        # Check if it's a built-in font (no registration needed)
        if font_name in BUILTIN_FONTS:
            return True

        # Check if already registered
        if font_name in self._registered_fonts:
            return True

        # Download and register custom font
        if font_name not in GOOGLE_FONTS:
            print(f"Font '{font_name}' not available")
            return False

        try:
            # Download regular font
            regular_path = self.download_font(font_name, 'regular')
            if not regular_path:
                return False

            # Register with ReportLab
            safe_name = font_name.replace(' ', '')
            pdfmetrics.registerFont(TTFont(safe_name, str(regular_path)))

            # Try to register bold and italic variants if available
            bold_path = self.download_font(font_name, 'bold')
            if bold_path:
                pdfmetrics.registerFont(TTFont(f"{safe_name}-Bold", str(bold_path)))

            italic_path = self.download_font(font_name, 'italic')
            if italic_path:
                pdfmetrics.registerFont(TTFont(f"{safe_name}-Italic", str(italic_path)))

            # Mark as registered
            self._registered_fonts.add(font_name)
            print(f"Successfully registered font: {font_name}")
            return True

        except Exception as e:
            print(f"Error registering font {font_name}: {e}")
            return False

    def get_reportlab_font_name(self, font_name: str) -> str:
        """
        Get the ReportLab-compatible font name.

        Args:
            font_name: Display name of the font

        Returns:
            ReportLab font name (e.g., 'Roboto' -> 'Roboto', 'Open Sans' -> 'OpenSans')
        """
        # Built-in fonts use their exact names
        if font_name in BUILTIN_FONTS:
            return BUILTIN_FONTS[font_name]

        # Google Fonts: remove spaces
        return font_name.replace(' ', '')

    def ensure_font_available(self, font_name: str) -> str:
        """
        Ensure a font is available and return its ReportLab name.
        Downloads and registers if needed, falls back to Helvetica if unavailable.

        Args:
            font_name: Display name of the font

        Returns:
            ReportLab-compatible font name
        """
        # Try to register the font
        if self.register_font(font_name):
            return self.get_reportlab_font_name(font_name)

        # Fall back to Helvetica
        print(f"Falling back to Helvetica for font '{font_name}'")
        return 'Helvetica'


# Global font manager instance
_font_manager = None

def get_font_manager() -> FontManager:
    """Get the global font manager instance."""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager


def get_available_fonts() -> Dict[str, str]:
    """
    Get a dictionary of available fonts.

    Returns:
        Dict mapping display names to font names
    """
    fonts = {}

    # Add built-in fonts
    fonts.update({
        'Helvetica (Sans-serif)': 'Helvetica',
        'Times Roman (Serif)': 'Times-Roman',
        'Courier (Monospace)': 'Courier'
    })

    # Add Google Fonts
    fonts.update({
        f'{name} (Google Font)': name
        for name in sorted(GOOGLE_FONTS.keys())
    })

    return fonts
