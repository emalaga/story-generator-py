# Fonts Directory

This directory stores Google Fonts used for PDF generation.

## How It Works

When you select a Google Font for PDF export, the system will automatically:
1. Download the font file (TTF format) from Google Fonts GitHub repository
2. Cache it in this directory
3. Register it with ReportLab for PDF generation

## Available Fonts

### Children's Story Fonts (Recommended)
- **Comic Neue** - Playful and fun, perfect for children's books
- **Quicksand** - Rounded and friendly sans-serif
- **Nunito** - Friendly and approachable sans-serif

### Modern Sans-serif Fonts
- **Roboto** - Clean, modern sans-serif
- **Open Sans** - Professional and readable
- **Lato** - Elegant and versatile
- **Montserrat** - Geometric and contemporary

### Serif Fonts
- **Merriweather** - Classic and readable serif
- **Playfair Display** - Elegant display serif

## Manual Font Download

To pre-download all fonts at once, run:

```bash
python -c "from src.utils.font_manager import get_font_manager, GOOGLE_FONTS; fm = get_font_manager(); [fm.register_font(name) for name in GOOGLE_FONTS.keys()]"
```

## Font Files

Downloaded fonts will be stored here with names like:
- `Roboto-Regular.ttf`
- `OpenSans-Bold.ttf`
- `Montserrat-Italic.ttf`

## Troubleshooting

If a font fails to download:
1. Check your internet connection
2. The system will automatically fall back to Helvetica
3. You can manually download TTF files from [Google Fonts](https://fonts.google.com/) and place them in this directory

## License

All fonts are from Google Fonts and are open source. Each font has its own license (typically OFL or Apache 2.0).
