# ProFiler Suite

Professionelle Dateiverwaltung mit Volltext-Suche, OCR und PDF-Bearbeitung.

## Features

- Datei-Indizierung und Volltext-Suche
- OCR für gescannte Dokumente
- PDF-Viewer und -Editor
- Datei-Überwachung (Watchdog)
- System-Tray Integration
- SQLite-basierter Index

## Installation

### Python Dependencies

Installiere alle benötigten Python-Pakete:

```bash
pip install -r requirements.txt
```

Siehe [requirements.txt](requirements.txt) für die vollständige Liste.

### Mitgelieferte Tools

- **Tesseract-OCR**: Portable Version in `tesseract_portable/`
- **Tessdata**: Sprachpakete in `tessdata/`

## Verwendung

```bash
python Profiler_Suite_V15.py
```

Oder über `START.bat`.

## Konfiguration

| Datei | Zweck |
|-------|-------|
| `profiler_config.json` | Hauptkonfiguration |
| `profiler_settings.json` | Benutzereinstellungen |
| `search_config.json` | Suchoptionen |

## Unterstützte Formate

- **Dokumente**: PDF, DOCX, TXT
- **Bilder**: PNG, JPG (mit OCR)
- **Archive**: Vorschau von Inhalten

## Lizenz

AGPL v3 - Siehe [LICENSE](LICENSE)

Dieses Projekt verwendet PyQt6 (GPL) und PyMuPDF (AGPL).
