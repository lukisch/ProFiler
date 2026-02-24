# UI-Konzept: Batch-Operationen für ProFiler V14
*Erstellt: 04.01.2026*

---

## 1. Übersicht

Batch-Operationen erlauben die gleichzeitige Verarbeitung mehrerer Dateien.
Integration in bestehende ProFiler-UI ohne große Umbauten.

---

## 2. Mehrfachauswahl (Schritt 1.2)

**In allen Dateilisten aktivieren:**
- QTableWidget/QListWidget: `setSelectionMode(QAbstractItemView.ExtendedSelection)`
- Strg+Klick = einzelne hinzufügen
- Shift+Klick = Bereich auswählen
- Strg+A = alle auswählen

**Statusleiste:** "X Dateien ausgewählt" anzeigen

---

## 3. Batch-Kontextmenü (Schritt 1.3)

**Rechtsklick bei Mehrfachauswahl zeigt:**
```
┌─────────────────────────────┐
│ Batch-Operationen           │
│ ├── PDF verschlüsseln...    │
│ ├── PDF entschlüsseln...    │
│ ├── Text extrahieren (OCR)  │
│ ├── Seiten extrahieren...   │
│ └── In Ordner kopieren...   │
│─────────────────────────────│
│ Auswahl aufheben            │
│ Auswahl exportieren (CSV)   │
└─────────────────────────────┘
```

---

## 4. Batch-Dialog (Schritt 1.4)

**Modaler Dialog mit:**
```
┌─────────────────────────────────────────────┐
│ Batch: PDF Verschlüsselung                  │
├─────────────────────────────────────────────┤
│ Dateien: 15 ausgewählt                      │
│                                             │
│ Passwort: [________________] [👁]           │
│ Bestätigen: [________________]              │
│                                             │
│ ☑ Originale behalten                       │
│ ☐ Fehler überspringen                      │
│                                             │
│ ═══════════════════════════════════════════ │
│ Fortschritt: ████████░░░░░░░░ 8/15 (53%)   │
│ Aktuell: Dokument_2024_03.pdf               │
│                                             │
│ Log:                                        │
│ ┌─────────────────────────────────────────┐ │
│ │ ✓ Rechnung_01.pdf - OK                  │ │
│ │ ✓ Vertrag_A.pdf - OK                    │ │
│ │ ✗ Scan_003.pdf - Fehler: bereits gesch. │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│         [Abbrechen]        [Schließen]      │
└─────────────────────────────────────────────┘
```

**Komponenten:**
- QProgressBar für Gesamtfortschritt
- QTextEdit (readonly) für Log
- QThread für Hintergrundverarbeitung (UI bleibt responsiv)
- Signal/Slot für Status-Updates

---

## 5. Technische Umsetzung

**Neue Klasse: `BatchProcessor`**
```python
class BatchProcessor(QThread):
    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished_file = pyqtSignal(str, bool, str)  # filename, success, message
    
    def __init__(self, files: list, operation: str, params: dict):
        ...
```

**Neue Klasse: `BatchDialog`**
```python
class BatchDialog(QDialog):
    def __init__(self, files: list, operation_type: str):
        ...
```

---

## 6. Nächste Schritte

1. [ ] 1.2: ExtendedSelection in allen Listen aktivieren
2. [ ] 1.3: Kontextmenü mit Batch-Optionen
3. [ ] 1.4: BatchDialog + BatchProcessor implementieren
4. [ ] 1.5: PDF-spezifische Batch-Operationen

---
*Konzept bereit für Implementation*
