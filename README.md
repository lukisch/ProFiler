# ProFiler Suite

Professional file management with full-text search, OCR, and PDF editing.

## Features

- **File Indexing** with SQLite-based index
- **Full-Text Search** across documents (PDF, DOCX, TXT)
- **OCR** for scanned documents (Tesseract)
- **PDF Viewer and Editor** (PyMuPDF)
- **File Monitoring** with Watchdog (Auto-Sync)
- **Privacy Traffic Light** — detection of sensitive files
- **System Tray Integration** for background operation
- **Excel Import** for existing file lists
- **Report Generation** (PDF)

## Screenshots

\![Main Window](screenshots/main.png)

## Installation

### Prerequisites

- Python >= 3.8
- Tesseract OCR (install separately or use the portable version)

### Python Dependencies

```bash
pip install -r requirements.txt
```

### Tesseract OCR

OCR functionality requires [Tesseract](https://github.com/tesseract-ocr/tesseract).
The path can be configured in `profiler_config.json`.

## Usage

```bash
python Profiler_Suite_V15.py
```

Or via the batch file:

```bash
START.bat
```

## Configuration

| File | Purpose |
|------|---------|
| `profiler_config.json` | Main configuration (paths, OCR, index) |
| `profiler_settings.json` | User settings (UI, theme) |
| `search_config.json` | Search options and filters |

## Included Tools

| Tool | Description |
|------|-------------|
| `Profiler_Suite_V15.py` | Main application |
| `ProFiler_Datenschutzampel.py` | Standalone privacy check |
| `SQLiteViewer.py` | Database viewer for the index |
| `import_excel_to_profiler.py` | Excel import into the Profiler index |
| `indent_gui_checker.py` | GUI indentation checker |

## Supported Formats

| Category | Formats |
|----------|---------|
| **Documents** | PDF, DOCX, TXT, RTF |
| **Images** | PNG, JPG, TIFF (with OCR) |
| **Spreadsheets** | XLSX, XLS, CSV |

## License

AGPL v3 — See [LICENSE](LICENSE)

This project uses PyQt6 (GPL) and PyMuPDF (AGPL).

---

**Version:** 15
**Author:** Lukas Geiger
**Last Updated:** March 2026

---

🇩🇪 [Deutsche Version](README.de.md)
