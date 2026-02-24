import os
import re
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "Mini SQL Viewer (SQLite)"
DEFAULT_LIMIT = 1000


class SqlViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x600")

        # State
        self.conn: sqlite3.Connection | None = None
        self.db_path: str | None = None

        # UI
        self._build_menu()
        self._build_toolbar()
        self._build_table_area()
        self._set_status("Keine Datenbank geÃ¶ffnet")

    # ----- UI-Build -----
    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Datenbank Ã¶ffnenâ€¦", command=self.open_db, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.destroy, accelerator="Ctrl+Q")
        menubar.add_cascade(label="Datei", menu=file_menu)
        self.config(menu=menubar)

        # Shortcuts
        self.bind_all("<Control-o>", lambda e: self.open_db())
        self.bind_all("<Control-q>", lambda e: self.destroy())

    def _build_toolbar(self):
        bar = ttk.Frame(self, padding=(8, 6))
        bar.pack(side=tk.TOP, fill=tk.X)

        # DB-Pfad
        self.db_label = ttk.Label(bar, text="DB: â€“", width=50, anchor="w")
        self.db_label.pack(side=tk.LEFT, padx=(0, 10))

        # Tabellen-Auswahl
        ttk.Label(bar, text="Tabelle:").pack(side=tk.LEFT)
        self.table_var = tk.StringVar()
        self.table_combo = ttk.Combobox(bar, textvariable=self.table_var, state="readonly", width=30)
        self.table_combo.pack(side=tk.LEFT, padx=6)
        self.table_combo.bind("<<ComboboxSelected>>", lambda e: self.load_selected_table())

        # Limit
        ttk.Label(bar, text="Limit:").pack(side=tk.LEFT, padx=(10, 0))
        self.limit_var = tk.IntVar(value=DEFAULT_LIMIT)
        self.limit_entry = ttk.Spinbox(bar, from_=1, to=1_000_000, increment=100, textvariable=self.limit_var, width=10)
        self.limit_entry.pack(side=tk.LEFT, padx=6)

        # Refresh
        self.refresh_btn = ttk.Button(bar, text="Refresh", command=self.load_selected_table)
        self.refresh_btn.pack(side=tk.LEFT, padx=(8, 0))

        # Status
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(bar, textvariable=self.status_var, anchor="e")
        self.status_label.pack(side=tk.RIGHT, expand=True, fill=tk.X)

    def _build_table_area(self):
        container = ttk.Frame(self)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Treeview
        self.tree = ttk.Treeview(container, show="headings")
        self.tree["columns"] = ()

        # Scrollbars
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

    # ----- Actions -----
    def open_db(self):
        path = filedialog.askopenfilename(
            title="SQLite-Datenbank Ã¶ffnen",
            filetypes=[("SQLite DB", "*.db *.sqlite *.sqlite3"), ("Alle Dateien", "*.*")]
        )
        if not path:
            return

        # Close existing
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

        try:
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            self.conn = conn
            self.db_path = path
            self.db_label.config(text=f"DB: {os.path.basename(path)}")
            self._set_status("Verbunden")
            self._load_tables()
        except Exception as e:
            messagebox.showerror("Fehler beim Ã–ffnen", str(e))
            self._set_status("Fehler")
    
    def open_database(self, path):
        """Öffnet Datenbank direkt per Pfad (für CLI-Args)"""
        if not path or not os.path.exists(path):
            return
        
        # Close existing
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None
        
        try:
            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            self.conn = conn
            self.db_path = path
            self.db_label.config(text=f"DB: {os.path.basename(path)}")
            self._set_status("Verbunden")
            self._load_tables()
        except Exception as e:
            messagebox.showerror("Fehler beim Öffnen", str(e))
            self._set_status("Fehler")

    def _load_tables(self):
        if not self.conn:
            return
        try:
            cur = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            tables = [r[0] for r in cur.fetchall()]
            self.table_combo["values"] = tables
            if tables:
                self.table_combo.current(0)
                self.load_selected_table()
            else:
                self.table_combo.set("")
                self._clear_tree()
                self._set_status("Keine Tabellen gefunden")
        except Exception as e:
            messagebox.showerror("Fehler", f"Tabellen konnten nicht geladen werden:\n{e}")

    def load_selected_table(self):
        table = self.table_var.get()
        if not table or not self.conn:
            return
        limit = max(1, int(self.limit_var.get() or DEFAULT_LIMIT))
        try:
            # Spalten bestimmen
            cur = self.conn.execute(f"PRAGMA table_info({self._ident(table)})")
            cols = [row[1] for row in cur.fetchall()]
            if not cols:
                self._clear_tree()
                self._set_status("Tabelle hat keine Spalten")
                return

            # Daten holen
            query = f"SELECT * FROM {self._ident(table)} LIMIT ?"
            cur = self.conn.execute(query, (limit,))
            rows = cur.fetchall()

            self._populate_tree(cols, rows)
            self._set_status(f"Tabelle: {table} â€” Zeilen: {len(rows)} von max. {limit}")
        except Exception as e:
            messagebox.showerror("Fehler beim Laden", str(e))

    # ----- Tree helpers -----
    def _clear_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = ()

    def _populate_tree(self, columns, rows):
        # Clear
        self._clear_tree()

        # Configure columns
        self.tree["columns"] = columns
        for c in columns:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, anchor="w")

        # Insert rows
        to_str = lambda v: "" if v is None else str(v)
        for row in rows:
            if isinstance(row, sqlite3.Row):
                values = [to_str(row[c]) for c in columns]
            else:
                values = [to_str(v) for v in row]
            self.tree.insert("", tk.END, values=values)

    # ----- Utils -----
    # Liste gÃ¤ngiger SQLite-Keywords (GroÃŸbuchstaben)
    _SQLITE_KEYWORDS = {
        "ABORT", "ACTION", "ADD", "AFTER", "ALL", "ALTER", "ANALYZE", "AND",
        "AS", "ASC", "ATTACH", "AUTOINCREMENT", "BEFORE", "BEGIN", "BETWEEN",
        "BY", "CASCADE", "CASE", "CAST", "CHECK", "COLLATE", "COLUMN",
        "COMMIT", "CONFLICT", "CONSTRAINT", "CREATE", "CROSS", "CURRENT_DATE",
        "CURRENT_TIME", "CURRENT_TIMESTAMP", "DATABASE", "DEFAULT", "DEFERRABLE",
        "DEFERRED", "DELETE", "DESC", "DETACH", "DISTINCT", "DROP", "EACH",
        "ELSE", "END", "ESCAPE", "EXCEPT", "EXCLUSIVE", "EXISTS", "EXPLAIN",
        "FAIL", "FOR", "FOREIGN", "FROM", "FULL", "GLOB", "GROUP", "HAVING",
        "IF", "IGNORE", "IMMEDIATE", "IN", "INDEX", "INDEXED", "INITIALLY",
        "INNER", "INSERT", "INSTEAD", "INTERSECT", "INTO", "IS", "ISNULL",
        "JOIN", "KEY", "LEFT", "LIKE", "LIMIT", "MATCH", "NATURAL", "NO",
        "NOT", "NOTNULL", "NULL", "OF", "OFFSET", "ON", "OR", "ORDER", "OUTER",
        "PLAN", "PRAGMA", "PRIMARY", "QUERY", "RAISE", "RECURSIVE", "REFERENCES",
        "REGEXP", "REINDEX", "RELEASE", "RENAME", "REPLACE", "RESTRICT",
        "RIGHT", "ROLLBACK", "ROW", "SAVEPOINT", "SELECT", "SET", "TABLE",
        "TEMP", "TEMPORARY", "THEN", "TO", "TRANSACTION", "TRIGGER", "UNION",
        "UNIQUE", "UPDATE", "USING", "VACUUM", "VALUES", "VIEW", "VIRTUAL",
        "WHEN", "WHERE", "WITH", "WITHOUT"
    }

    def _ident(self, name: str) -> str:
        """
        Gibt einen sicheren SQLite-Identifier zurück.
        - Quoted, wenn Sonderzeichen enthalten sind
        - Quoted, wenn Name ein SQL-Keyword ist
        - Escaped doppelte Anführungszeichen
        """
        if not name:
            raise ValueError("Identifier darf nicht leer sein.")

        # Prüfen, ob Name nur aus Buchstaben, Zahlen und Unterstrichen besteht
        is_simple = re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name) is not None

        # Prüfen, ob Name ein reserviertes Keyword ist
        is_keyword = name.upper() in self._SQLITE_KEYWORDS

        if not is_simple or is_keyword:
            safe_name = name.replace('"', '""')
            return f'"{safe_name}"'

        return name
    
    def _set_status(self, text: str):
        self.status_var.set(text)

        
if __name__ == "__main__":
    import sys
    app = SqlViewer()
    
    # CLI-Argument: Datenbank-Pfad (NEU V13.1!)
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        if os.path.exists(db_path):
            app.open_database(db_path)
    
    app.mainloop()