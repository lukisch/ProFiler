# ProFiler Suite

Professionelle Dateiverwaltung mit Volltext-Suche, OCR und PDF-Bearbeitung.

## Features

- **Datei-Indizierung** mit SQLite-basiertem Index
- **Volltext-Suche** in Dokumenten (PDF, DOCX, TXT)
- **OCR** fuer gescannte Dokumente (Tesseract)
- **PDF-Viewer und -Editor** (PyMuPDF)
- **Datei-Ueberwachung** mit Watchdog (Auto-Sync)
- **Datenschutzampel** - Erkennung sensibler Dateien
- **System-Tray Integration** fuer Hintergrund-Betrieb
- **Excel-Import** fuer bestehende Dateilisten
- **Report-Generierung** (PDF)

## Screenshots

![Hauptfenster](screenshots/main.png)

## Installation

### Voraussetzungen

- Python >= 3.8
- Tesseract OCR (separat installieren oder portable Version nutzen)

### Python-Abhaengigkeiten

```bash
pip install -r requirements.txt
```

### Tesseract OCR

Fuer OCR-Funktionalitaet wird [Tesseract](https://github.com/tesseract-ocr/tesseract) benoetigt.
Der Pfad kann in `profiler_config.json` konfiguriert werden.

## Verwendung

```bash
python Profiler_Suite_V15.py
```

Oder ueber die Batch-Datei:

```bash
START.bat
```

## Konfiguration

| Datei | Zweck |
|-------|-------|
| `profiler_config.json` | Hauptkonfiguration (Pfade, OCR, Index) |
| `profiler_settings.json` | Benutzereinstellungen (UI, Theme) |
| `search_config.json` | Suchoptionen und Filter |

## Enthaltene Tools

| Tool | Beschreibung |
|------|-------------|
| `Profiler_Suite_V15.py` | Hauptanwendung |
| `ProFiler_Datenschutzampel.py` | Standalone-Datenschutzpruefung |
| `SQLiteViewer.py` | Datenbank-Viewer fuer den Index |
| `import_excel_to_profiler.py` | Excel-Import in den Profiler-Index |
| `indent_gui_checker.py` | GUI-Einrueckungs-Checker |

## Unterstuetzte Formate

| Kategorie | Formate |
|-----------|---------|
| **Dokumente** | PDF, DOCX, TXT, RTF |
| **Bilder** | PNG, JPG, TIFF (mit OCR) |
| **Tabellen** | XLSX, XLS, CSV |

## Lizenz

AGPL v3 - Siehe [LICENSE](LICENSE)

Dieses Projekt verwendet PyQt6 (GPL) und PyMuPDF (AGPL).

---

**Version:** 15
**Autor:** Lukas Geiger
**Letzte Aktualisierung:** Maerz 2026

---

## English

Professional file management with full-text search, OCR, and PDF editing capabilities.

### Features

- Full-text search with indexing
- OCR integration (Tesseract)
- PDF editing and merging
- Tag-based organization

### Installation

```bash
git clone https://github.com/lukisch/REL-PUB_ProFiler.git
cd REL-PUB_ProFiler
pip install -r requirements.txt
python "Profiler_Suite_V13.2_Enhanced.py"
```

### License

See [LICENSE](LICENSE) for details.
