# Auto-Sync Watchdog Konzept
## ProFiler V14 - Feature 2.x
*Stand: 04.01.2026*

---

## 2.1 Watchdog-Integration (PRÜFUNG)

### Bibliothek
```bash
pip install watchdog
```

### Benötigte Imports
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
```

### Watchdog-Features
- **Observer**: Überwacht Dateisysteme auf Änderungen
- **FileSystemEventHandler**: Basisklasse für Event-Handler
- **Events**: on_created, on_modified, on_deleted, on_moved

### Geplante Architektur

```
ProFiler_Suite_V14.py
├── class AutoSyncHandler(FileSystemEventHandler)  # 2.2
│   ├── __init__(target_folder, callback)
│   ├── on_created(event)
│   ├── on_modified(event)
│   └── filter_extensions(event)
│
├── class AutoSyncManager  # 2.3
│   ├── __init__(ui_callback)
│   ├── start_watch(source, target, extensions)
│   ├── stop_watch()
│   └── get_status()
│
└── UI-Integration  # 2.4
    ├── Auto-Sync Tab (QWidget)
    ├── Watch-Ordner Konfiguration
    └── Status-Anzeige (aktiv/inaktiv)
```

### Nächster Schritt
2.2: FileSystemEventHandler Basisklasse implementieren:
```python
class AutoSyncHandler(FileSystemEventHandler):
    def __init__(self, target_folder, extensions=None, callback=None):
        self.target = target_folder
        self.extensions = extensions or ['.pdf', '.docx', '.xlsx']
        self.callback = callback
    
    def on_created(self, event):
        if not event.is_directory and self._should_sync(event.src_path):
            self._sync_file(event.src_path)
    
    def _should_sync(self, path):
        return any(path.lower().endswith(ext) for ext in self.extensions)
    
    def _sync_file(self, src_path):
        # Kopierlogik + Callback für UI
        pass
```

---
*Ergebnis: watchdog ist geeignet und kann integriert werden*
