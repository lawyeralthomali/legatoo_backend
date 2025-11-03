# Arabic Fonts Directory

This directory contains Arabic-supporting TrueType fonts (TTF files) for PDF generation.

## Included Fonts

✅ **Noto Sans Arabic fonts are included:**
- `NotoSansArabic-Regular.ttf` - Main font (default, used for all PDF text)
- `NotoSansArabic-Bold.ttf` - Bold variant (available for future use)
- `NotoSansArabic-VariableFont_wdth,wght.ttf` - Variable font (available for future use)

## How It Works

The PDF generator automatically:
1. **First** checks this `fonts/` directory for bundled fonts
2. **Then** falls back to system fonts if no bundled font is found:
   - DejaVu Sans (if available on system)
   - Arial Unicode MS (if available on Windows)
   - System Arabic fonts (if available)

## Font Selection Priority

The PDF generator will automatically detect and use fonts in this order:
1. `NotoSansArabic-Regular.ttf` ✅ **Currently included**
2. `NotoSansArabic.ttf`
3. `DejaVuSans.ttf`
4. `arial-unicode-ms.ttf`
5. `ARIALUNI.TTF`

## Default Behavior

- **All PDF text uses Arabic font by default** (`NotoSansArabic-Regular.ttf`)
- **All text is right-aligned** (RTL for Arabic support)
- Works correctly for both Arabic and English text

## Note

If no Arabic font is found, the PDF generator will log a warning and use Helvetica as fallback, which may cause Arabic text to display as rectangles. However, with the included Noto Sans Arabic fonts, this should never happen.

