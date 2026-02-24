#!/usr/bin/env python3
"""
ProFiler Datenschutzampel - System-Tray Tool
Parallel zu ProFiler Suite laufend
Überwacht Zwischenablage auf sensible Daten
Shared Config für Blacklist/Whitelist
"""

import sys
import json
import re
from pathlib import Path
from typing import List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QLineEdit, QListWidget,
    QTextEdit, QFileDialog, QMessageBox, QCheckBox,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QPixmap, QPainter, QBrush, QIcon

# ============================================================================
# KONFIGURATION
# ============================================================================

CONFIG_PATH = Path.home() / ".profiler_suite" / "datenschutzampel.json"
HISTORY_LIMIT = 15

STYLESHEET = """
QMainWindow { background-color: #f0f2f5; }
QTabWidget::pane { border: 1px solid #dcdcdc; background: white; border-radius: 4px; }
QTabBar::tab { 
    background: #e1e4e8; 
    padding: 8px 20px; 
    margin-right: 2px; 
    border-top-left-radius: 4px; 
    border-top-right-radius: 4px; 
    color: #333; 
}
QTabBar::tab:selected { 
    background: white; 
    font-weight: bold; 
    border-bottom: 2px solid #007bff; 
}
QLabel { color: #333; font-size: 14px; }
QLabel#Header { font-size: 18px; font-weight: bold; color: #2c3e50; }
QPushButton { 
    background-color: #ffffff; 
    border: 1px solid #ced4da; 
    border-radius: 4px; 
    padding: 6px 12px; 
    font-size: 13px; 
    color: #495057; 
}
QPushButton:hover { background-color: #e9ecef; border-color: #adb5bd; }
QPushButton#Danger { color: #dc3545; border-color: #dc3545; }
QPushButton#Danger:hover { background-color: #dc3545; color: white; }
QPushButton#Success { color: #28a745; border-color: #28a745; }
QPushButton#Success:hover { background-color: #28a745; color: white; }
QLineEdit, QListWidget, QTextEdit { 
    border: 1px solid #ced4da; 
    border-radius: 4px; 
    padding: 4px; 
    background-color: white; 
    selection-background-color: #007bff; 
}
"""

# ============================================================================
# MAIN APPLICATION
# ============================================================================

class DatenschutzAmpel(QMainWindow):
    """Datenschutz-Ampel für ProFiler Suite"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("🚦 ProFiler Datenschutzampel")
        self.resize(900, 650)
        self.setMinimumSize(800, 500)
        
        # State
        self.sensitive: List[str] = []
        self.whitelist: List[str] = []
        self.clip_history: List[str] = []
        self.patterns: List[re.Pattern] = []
        
        self.ampel_status = "grün"  # grün, gelb, rot
        self.case_sensitive = False
        self.whole_words = False
        self.clipboard_lock = False
        
        # UI
        self.init_ui()
        self.setup_tray()
        
        # Clipboard
        self.clipboard = QApplication.clipboard()
        
        # Config laden
        self.load_config()
        self.compile_patterns()
        
        # Clipboard Monitoring
        self.clipboard.dataChanged.connect(self.on_clipboard_change)
        
        # Styling
        self.setStyleSheet(STYLESHEET)
        self.statusBar().showMessage("Bereit - Ampel: 🟢")
    
    def init_ui(self):
        """Initialisiert UI"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        tabs = QTabWidget()
        
        # Tab 1: Listen
        tab_lists = QWidget()
        self.setup_tab_lists(tab_lists)
        tabs.addTab(tab_lists, "📋 Listen (Blacklist/Whitelist)")
        
        # Tab 2: Ampel
        tab_ampel = QWidget()
        self.setup_tab_ampel(tab_ampel)
        tabs.addTab(tab_ampel, "🚦 Ampel-Steuerung")
        
        # Tab 3: Verlauf
        tab_history = QWidget()
        self.setup_tab_history(tab_history)
        tabs.addTab(tab_history, "🕘 Verlauf")
        
        main_layout.addWidget(tabs)
    
    def setup_tab_lists(self, tab):
        """Blacklist/Whitelist Verwaltung"""
        layout = QVBoxLayout(tab)
        
        # Header
        header = QLabel("Listen-Verwaltung")
        header.setObjectName("Header")
        layout.addWidget(header)
        
        # Blacklist
        layout.addWidget(QLabel("🚫 Blacklist (Sensible Begriffe):"))
        
        self.blacklist_widget = QListWidget()
        layout.addWidget(self.blacklist_widget)
        
        bl_controls = QHBoxLayout()
        self.blacklist_input = QLineEdit()
        self.blacklist_input.setPlaceholderText("Begriff hinzufügen...")
        btn_add_bl = QPushButton("+ Hinzufügen")
        btn_add_bl.clicked.connect(self.add_to_blacklist)
        btn_remove_bl = QPushButton("- Entfernen")
        btn_remove_bl.clicked.connect(self.remove_from_blacklist)
        
        bl_controls.addWidget(self.blacklist_input)
        bl_controls.addWidget(btn_add_bl)
        bl_controls.addWidget(btn_remove_bl)
        layout.addLayout(bl_controls)
        
        # Whitelist
        layout.addWidget(QLabel("✅ Whitelist (Ausnahmen):"))
        
        self.whitelist_widget = QListWidget()
        layout.addWidget(self.whitelist_widget)
        
        wl_controls = QHBoxLayout()
        self.whitelist_input = QLineEdit()
        self.whitelist_input.setPlaceholderText("Ausnahme hinzufügen...")
        btn_add_wl = QPushButton("+ Hinzufügen")
        btn_add_wl.clicked.connect(self.add_to_whitelist)
        btn_remove_wl = QPushButton("- Entfernen")
        btn_remove_wl.clicked.connect(self.remove_from_whitelist)
        
        wl_controls.addWidget(self.whitelist_input)
        wl_controls.addWidget(btn_add_wl)
        wl_controls.addWidget(btn_remove_wl)
        layout.addLayout(wl_controls)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_clear_bl = QPushButton("🗑️ Blacklist leeren")
        btn_clear_bl.setObjectName("Danger")
        btn_clear_bl.clicked.connect(self.clear_blacklist)
        
        btn_save = QPushButton("💾 Listen speichern")
        btn_save.setObjectName("Success")
        btn_save.clicked.connect(self.save_config)
        
        btn_layout.addWidget(btn_clear_bl)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
    
    def setup_tab_ampel(self, tab):
        """Ampel-Steuerung"""
        layout = QVBoxLayout(tab)
        
        # Ampel-Anzeige
        self.ampel_label = QLabel("🟢")
        self.ampel_label.setStyleSheet("font-size: 72px;")
        self.ampel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.ampel_label)
        
        self.ampel_text = QLabel("Status: Grün - Alles sicher")
        self.ampel_text.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.ampel_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.ampel_text)
        
        layout.addWidget(QLabel(""))
        
        # Optionen
        self.cb_case_sensitive = QCheckBox("Groß-/Kleinschreibung beachten")
        self.cb_case_sensitive.stateChanged.connect(self.on_options_changed)
        layout.addWidget(self.cb_case_sensitive)
        
        self.cb_whole_words = QCheckBox("Nur ganze Wörter")
        self.cb_whole_words.stateChanged.connect(self.on_options_changed)
        layout.addWidget(self.cb_whole_words)
        
        self.cb_clipboard_lock = QCheckBox("🔒 Zwischenablage sperren bei Rot")
        self.cb_clipboard_lock.stateChanged.connect(self.on_options_changed)
        layout.addWidget(self.cb_clipboard_lock)
        
        layout.addStretch()
        
        # Manual Override
        manual_layout = QHBoxLayout()
        btn_green = QPushButton("🟢 Auf Grün setzen")
        btn_green.setObjectName("Success")
        btn_green.clicked.connect(lambda: self.set_ampel_manual("grün"))
        
        btn_red = QPushButton("🔴 Auf Rot setzen")
        btn_red.setObjectName("Danger")
        btn_red.clicked.connect(lambda: self.set_ampel_manual("rot"))
        
        manual_layout.addWidget(btn_green)
        manual_layout.addWidget(btn_red)
        layout.addLayout(manual_layout)
    
    def setup_tab_history(self, tab):
        """Zwischenablage-Verlauf"""
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("📋 Letzte Zwischenablage-Einträge:"))
        
        self.history_widget = QTextEdit()
        self.history_widget.setReadOnly(True)
        layout.addWidget(self.history_widget)
        
        btn_clear_history = QPushButton("🗑️ Verlauf löschen")
        btn_clear_history.clicked.connect(self.clear_history)
        layout.addWidget(btn_clear_history)
    
    def setup_tray(self):
        """System-Tray Icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.update_tray_icon()
        
        tray_menu = QMenu()
        action_show = tray_menu.addAction("📂 Öffnen")
        action_show.triggered.connect(self.show)
        
        tray_menu.addSeparator()
        action_quit = tray_menu.addAction("❌ Beenden")
        action_quit.triggered.connect(self.force_quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_click)
        self.tray_icon.show()
    
    def update_tray_icon(self):
        """Aktualisiert Tray-Icon basierend auf Ampel-Status"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        
        if self.ampel_status == "rot":
            color = QColor(220, 53, 69)  # Rot
        elif self.ampel_status == "gelb":
            color = QColor(255, 193, 7)  # Gelb
        else:
            color = QColor(40, 167, 69)  # Grün
        
        painter.setBrush(QBrush(color))
        painter.drawEllipse(4, 4, 56, 56)
        painter.end()
        
        # FIX: QPixmap zu QIcon konvertieren!
        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip(f"Datenschutzampel: {self.ampel_status.upper()}")
    
    def on_tray_click(self, reason):
        """Tray-Icon Klick"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def force_quit(self):
        """Wirklich beenden"""
        QApplication.quit()
    
    def closeEvent(self, event):
        """Minimiert zu Tray"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Datenschutzampel",
            "Läuft im Hintergrund weiter.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    # ========================================================================
    # LISTE-VERWALTUNG
    # ========================================================================
    
    def add_to_blacklist(self):
        word = self.blacklist_input.text().strip()
        if word and word not in self.sensitive:
            self.sensitive.append(word)
            self.update_blacklist_display()
            self.blacklist_input.clear()
            self.compile_patterns()
    
    def add_to_whitelist(self):
        word = self.whitelist_input.text().strip()
        if word and word not in self.whitelist:
            self.whitelist.append(word)
            self.update_whitelist_display()
            self.whitelist_input.clear()
    
    def remove_from_blacklist(self):
        for item in self.blacklist_widget.selectedItems():
            self.sensitive.remove(item.text())
        self.update_blacklist_display()
        self.compile_patterns()
    
    def remove_from_whitelist(self):
        for item in self.whitelist_widget.selectedItems():
            self.whitelist.remove(item.text())
        self.update_whitelist_display()
    
    def clear_blacklist(self):
        reply = QMessageBox.question(
            self,
            "Blacklist leeren",
            "Wirklich alle Einträge löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.sensitive.clear()
            self.update_blacklist_display()
            self.compile_patterns()
    
    def update_blacklist_display(self):
        self.blacklist_widget.clear()
        for word in sorted(self.sensitive):
            self.blacklist_widget.addItem(word)
    
    def update_whitelist_display(self):
        self.whitelist_widget.clear()
        for word in sorted(self.whitelist):
            self.whitelist_widget.addItem(word)
    
    def clear_history(self):
        self.clip_history.clear()
        self.history_widget.clear()
    
    # ========================================================================
    # AMPEL-LOGIK
    # ========================================================================
    
    def compile_patterns(self):
        """Kompiliert Regex-Patterns aus Blacklist"""
        self.patterns = []
        flags = 0 if self.case_sensitive else re.IGNORECASE
        
        for word in self.sensitive:
            if self.whole_words:
                pattern = rf"\b{re.escape(word)}\b"
            else:
                pattern = re.escape(word)
            try:
                self.patterns.append(re.compile(pattern, flags))
            except:
                pass
    
    def on_options_changed(self):
        """Optionen geändert"""
        self.case_sensitive = self.cb_case_sensitive.isChecked()
        self.whole_words = self.cb_whole_words.isChecked()
        self.clipboard_lock = self.cb_clipboard_lock.isChecked()
        self.compile_patterns()
    
    def on_clipboard_change(self):
        """Zwischenablage hat sich geändert"""
        try:
            text = self.clipboard.text()
            if not text:
                return
            
            # Zu Verlauf hinzufügen
            self.clip_history.insert(0, text)
            if len(self.clip_history) > HISTORY_LIMIT:
                self.clip_history.pop()
            self.update_history_display()
            
            # Prüfen
            found_sensitive = []
            
            for pattern in self.patterns:
                matches = pattern.findall(text)
                if matches:
                    found_sensitive.extend(matches)
            
            # Whitelist-Check
            found_sensitive = [
                word for word in found_sensitive
                if word.lower() not in [w.lower() for w in self.whitelist]
            ]
            
            if found_sensitive:
                self.set_ampel("rot", f"Sensible Begriffe: {', '.join(set(found_sensitive))}")
                
                if self.clipboard_lock:
                    self.clipboard.clear()
                    QMessageBox.warning(
                        self,
                        "Zwischenablage gesperrt",
                        f"⚠️ Sensible Begriffe erkannt!\n\nZwischenablage wurde geleert:\n{', '.join(set(found_sensitive))}"
                    )
            else:
                self.set_ampel("grün", "Keine sensiblen Daten erkannt")
        
        except Exception as e:
            pass
    
    def set_ampel(self, status, message=""):
        """Setzt Ampel-Status"""
        self.ampel_status = status
        
        if status == "rot":
            self.ampel_label.setText("🔴")
            self.ampel_text.setText(f"Status: ROT - {message}")
            self.statusBar().showMessage(f"⚠️ ROT: {message}")
        elif status == "gelb":
            self.ampel_label.setText("🟡")
            self.ampel_text.setText(f"Status: GELB - {message}")
            self.statusBar().showMessage(f"⚠️ GELB: {message}")
        else:
            self.ampel_label.setText("🟢")
            self.ampel_text.setText(f"Status: GRÜN - {message}")
            self.statusBar().showMessage(f"✅ GRÜN: {message}")
        
        self.update_tray_icon()
    
    def set_ampel_manual(self, status):
        """Manuelles Setzen der Ampel"""
        self.set_ampel(status, "Manuell gesetzt")
    
    def update_history_display(self):
        """Aktualisiert Verlaufs-Anzeige"""
        text = "\n\n".join([
            f"[{i+1}] {entry[:200]}{'...' if len(entry) > 200 else ''}"
            for i, entry in enumerate(self.clip_history)
        ])
        self.history_widget.setPlainText(text)
    
    # ========================================================================
    # CONFIG
    # ========================================================================
    
    def load_config(self):
        """Lädt Konfiguration"""
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.sensitive = data.get('blacklist', [])
                self.whitelist = data.get('whitelist', [])
                self.case_sensitive = data.get('case_sensitive', False)
                self.whole_words = data.get('whole_words', False)
                self.clipboard_lock = data.get('clipboard_lock', False)
                
                self.update_blacklist_display()
                self.update_whitelist_display()
                
                self.cb_case_sensitive.setChecked(self.case_sensitive)
                self.cb_whole_words.setChecked(self.whole_words)
                self.cb_clipboard_lock.setChecked(self.clipboard_lock)
            except:
                pass
    
    def save_config(self):
        """Speichert Konfiguration"""
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'blacklist': self.sensitive,
            'whitelist': self.whitelist,
            'case_sensitive': self.case_sensitive,
            'whole_words': self.whole_words,
            'clipboard_lock': self.clipboard_lock
        }
        
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        QMessageBox.information(
            self,
            "Gespeichert",
            f"✅ Konfiguration gespeichert:\n{CONFIG_PATH}"
        )


# ============================================================================
# MAIN
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Wichtig für Tray!
    
    window = DatenschutzAmpel()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()