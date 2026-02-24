import os
import sqlite3
import pandas as pd
import hashlib
import shutil
from datetime import datetime

# ================= KONFIGURATION =================
INPUT_FILE = "import_daten.xlsx" 
DB_PATH = "profiler_Wissensdatenbank.db" 
OUTPUT_FOLDER = "Importierte_Materialien"

# Erweiterte Liste basierend auf deinen Daten
MATERIAL_KEYWORDS = [
    'regal', 'schrank', 'raum', 'zimmer', 'kasten', 'fach', 'schublade', 
    'ablage', 'ordner', 'mappe', 'box', 'archiv', 'theke', 'wand', 'tisch',
    'variabel', 'selbst erstellt', 'kostenlos', 'lizenzpflichtig', 'ca.'
]
# =================================================

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def sanitize_filename(name):
    if pd.isna(name): return "Unbenannt"
    # Ersetzt ungültige Zeichen und kürzt den Dateinamen
    safe = "".join(c for c in str(name) if c.isalnum() or c in (' ', '.', '_', '-')).strip()
    return safe[:100] # Maximale Länge begrenzen

def safe_str(val):
    if pd.isna(val) or val is None: return ""
    val = str(val).strip()
    if val.lower() == "nan": return ""
    return val

class ProfilerAutismoImporter:
    def __init__(self, db_path, output_folder):
        self.db_path = db_path
        self.output_folder = os.path.abspath(output_folder)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        ensure_folder(output_folder)

    # --- BEREINIGUNG ---
    def cleanup_previous_import(self):
        print("🧹 Bereinige vorherige Importe...")
        search_path = self.output_folder + os.sep + "%"
        try:
            self.cursor.execute("SELECT id, file_id FROM versions WHERE path LIKE ?", (search_path,))
            rows = self.cursor.fetchall()
            if rows:
                version_ids = [r[0] for r in rows]
                file_ids = [r[1] for r in rows]
                self.cursor.executemany("DELETE FROM collection_items WHERE version_id = ?", [(i,) for i in version_ids])
                self.cursor.executemany("DELETE FROM versions WHERE id = ?", [(i,) for i in version_ids])
                self.cursor.executemany("DELETE FROM tags WHERE file_id = ?", [(i,) for i in file_ids])
                self.cursor.executemany("DELETE FROM files WHERE id = ?", [(i,) for i in file_ids])
                self.conn.commit()
                print(f"   -> {len(version_ids)} DB-Einträge gelöscht.")
        except Exception as e:
            print(f"❌ Fehler bei DB-Bereinigung: {e}")

        if os.path.exists(self.output_folder):
            try:
                shutil.rmtree(self.output_folder)
                ensure_folder(self.output_folder)
                print(f"   -> Ordner '{self.output_folder}' geleert.")
            except Exception as e:
                print(f"❌ Fehler beim Löschen der Dateien: {e}")

    # --- DB HELFER ---
    def get_or_create_collection(self, name):
        name = safe_str(name)
        if not name: return None
        # Nutze den 'Typ' als Sammlungsname (z.B. "Material/Spiel")
        self.cursor.execute("SELECT id FROM collections WHERE name = ?", (name,))
        res = self.cursor.fetchone()
        if res: return res[0]
        ts = datetime.utcnow().isoformat()
        self.cursor.execute("INSERT INTO collections (name, description, created_at) VALUES (?, ?, ?)", 
                            (name, "Importiert aus Excel", ts))
        self.conn.commit()
        return self.cursor.lastrowid

    def add_tags(self, file_id, tags_list):
        for tag in tags_list:
            tag = tag.strip()
            if tag:
                self.cursor.execute("INSERT INTO tags (file_id, tag) VALUES (?, ?)", (file_id, tag))

    def register_in_db(self, file_path, category_id, tags_list, display_name):
        if not os.path.exists(file_path): return
        file_path = os.path.abspath(file_path)
        stat = os.stat(file_path)
        mtime = datetime.utcfromtimestamp(stat.st_mtime).isoformat()
        content_hash = sha256_file(file_path)
        
        self.cursor.execute("SELECT id FROM files WHERE content_hash = ?", (content_hash,))
        res = self.cursor.fetchone()
        if res: file_id = res[0]
        else:
            self.cursor.execute("INSERT INTO files (content_hash, size, mime, first_seen, pdf_encrypted, pdf_has_text) VALUES (?, ?, ?, ?, 0, 1)", 
                                (content_hash, stat.st_size, "text/plain", mtime))
            file_id = self.cursor.lastrowid

        try:
            self.cursor.execute("INSERT INTO versions (file_id, name, path, mtime, ctime, version_index, source_side, is_deleted, display_name) VALUES (?, ?, ?, ?, ?, 1, 'source', 0, ?)", 
                                (file_id, os.path.basename(file_path), file_path, mtime, mtime, display_name))
        except sqlite3.OperationalError:
            self.cursor.execute("INSERT INTO versions (file_id, name, path, mtime, ctime, version_index, source_side, is_deleted) VALUES (?, ?, ?, ?, ?, 1, 'source', 0)", 
                                (file_id, os.path.basename(file_path), file_path, mtime, mtime))
        version_id = self.cursor.lastrowid

        if category_id:
            ts = datetime.utcnow().isoformat()
            self.cursor.execute("INSERT OR IGNORE INTO collection_items (collection_id, version_id, added_at) VALUES (?, ?, ?)", (category_id, version_id, ts))
        
        self.add_tags(file_id, tags_list)
        self.conn.commit()
        print(f"  -> {display_name}")

    # --- DATEI ERSTELLER ---
    def create_internet_resource(self, data):
        filename = f"{sanitize_filename(data['Name'])}.url"
        path = os.path.join(self.output_folder, filename)
        content = f"""[InternetShortcut]
URL={data['Ort']}
IconIndex=0

[Metadata]
Bezeichnung={data['Name']}
Beschreibung={data['Beschreibung']}
Anmerkung={data['Preis']}
Kategorie={data['Typ']}
Tags={', '.join(data['Tags'])}
Erstellt={datetime.now().strftime('%Y-%m-%d')}
Importiert=True
"""
        with open(path, 'w', encoding='utf-8') as f: f.write(content)
        return path

    def create_material_reference(self, data):
        filename = f"Material_{sanitize_filename(data['Name'])}.material.txt"
        path = os.path.join(self.output_folder, filename)
        content = f"""Materialverweis: {data['Name']}
Erstellt: {datetime.now().strftime('%Y-%m-%d')}
================================================================================

Bezeichnung:     {data['Name']}
Standort/Info:   {data['Ort']}
Typ:             {data['Typ']}

Tags:            {', '.join(data['Tags'])}

Beschreibung:
{data['Beschreibung']}

Preis/Anmerkung:
{data['Preis']}
"""
        with open(path, 'w', encoding='utf-8') as f: f.write(content)
        return path

    def create_literature_reference(self, data):
        filename = f"Literatur_{sanitize_filename(data['Name'])}.txt"
        path = os.path.join(self.output_folder, filename)
        # In deinem Datensatz steht im Feld "Ort" oft die Quelle/Autor (z.B. "Frith 2013")
        content = f"""Literatur: {data['Name']}
Erstellt: {datetime.now().strftime('%Y-%m-%d')}
================================================================================

Titel:      {data['Name']}
Quelle/Ref: {data['Ort']}
Typ:        {data['Typ']}

Tags:       {', '.join(data['Tags'])}

Beschreibung/Inhalt:
{data['Beschreibung']}

Anmerkung:
{data['Preis']}
"""
        with open(path, 'w', encoding='utf-8') as f: f.write(content)
        return path

    def create_generic_info(self, data):
        filename = f"Info_{sanitize_filename(data['Name'])}.txt"
        path = os.path.join(self.output_folder, filename)
        content = f"""Information: {data['Name']}
================================================================================

Typ:    {data['Typ']}
Status: {data['Ort']}
Tags:   {', '.join(data['Tags'])}

Beschreibung:
{data['Beschreibung']}

Anmerkung:
{data['Preis']}
"""
        with open(path, 'w', encoding='utf-8') as f: f.write(content)
        return path

    # --- MAIN ---
    def run_import(self, excel_path):
        print(f"🚀 Starte Spezial-Import aus {excel_path}...")
        
        try:
            xls = pd.ExcelFile(excel_path, engine='openpyxl')
            target_df = None
            found_sheet = ""
            
            # Header-Suche über alle Sheets
            for sheet in xls.sheet_names:
                df_raw = pd.read_excel(xls, sheet_name=sheet, header=None)
                for i, r in df_raw.head(20).iterrows():
                    row_str = " ".join([str(v) for v in r.values])
                    # Suche nach den markanten Spalten
                    if "Name" in row_str and "Beschreibung" in row_str:
                        print(f"✅ Header gefunden in Blatt '{sheet}', Zeile {i+1}")
                        target_df = pd.read_excel(xls, sheet_name=sheet, header=i)
                        found_sheet = sheet
                        break
                if target_df is not None: break
            
            if target_df is None:
                print("❌ Konnte Spalten 'Name' und 'Beschreibung' nicht finden.")
                return

            target_df.columns = target_df.columns.str.strip()
            
            # Finde die variable Ort-Spalte (sie heißt "Ort: Hyperlink...")
            ort_col = next((c for c in target_df.columns if "Ort" in c or "Hyperlink" in c), None)
            if not ort_col:
                print("❌ Spalte für 'Ort/Hyperlink' nicht gefunden.")
                return

            success = 0
            for index, row in target_df.iterrows():
                try:
                    name = safe_str(row.get('Name'))
                    if not name: continue

                    typ = safe_str(row.get('Typ'))
                    typ_lower = typ.lower()
                    
                    data = {
                        'Name': name,
                        'Typ': typ,
                        'Beschreibung': safe_str(row.get('Beschreibung')),
                        'Preis': safe_str(row.get('Preis/Anmerkung')),
                        'Ort': safe_str(row.get(ort_col)),
                        'Tags': []
                    }
                    
                    # Tags bauen
                    foerder = safe_str(row.get('Förderkategorien'))
                    icf = safe_str(row.get('ICF-Bereiche'))
                    if foerder: data['Tags'].extend([t.strip() for t in foerder.replace(';',',').split(',')])
                    if icf: data['Tags'].extend([t.strip() for t in icf.replace(';',',').split(',')])

                    path = None
                    ort_lower = data['Ort'].lower()

                    # --- LOGIK FÜR DEINEN DATENSATZ ---
                    
                    # 1. URL Erkennung (z.B. YouTube Links)
                    if ort_lower.startswith('http') or ort_lower.startswith('www'):
                        path = self.create_internet_resource(data)
                        
                    # 2. Literatur Erkennung (anhand der Spalte "Typ")
                    elif "literatur" in typ_lower or "buch" in typ_lower:
                        path = self.create_literature_reference(data)
                        
                    # 3. Material Erkennung (anhand Keywords im Ort)
                    elif any(k in ort_lower for k in MATERIAL_KEYWORDS) or "material" in typ_lower:
                        path = self.create_material_reference(data)
                        
                    # 4. Fallback (Apps ohne Link, Konzepte, etc.)
                    else:
                        path = self.create_generic_info(data)

                    if path:
                        cat_id = self.get_or_create_collection(typ)
                        self.register_in_db(path, cat_id, data['Tags'], name)
                        success += 1

                except Exception as e:
                    print(f"⚠️ Fehler Zeile {index}: {e}")

            self.conn.close()
            print(f"\n🎉 Fertig! {success} Einträge erfolgreich importiert.")

        except Exception as e:
            print(f"❌ Kritischer Fehler: {e}")

if __name__ == "__main__":
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Datei nicht gefunden: {INPUT_FILE}")
    else:
        imp = ProfilerAutismoImporter(DB_PATH, OUTPUT_FOLDER)
        frage = input("⚠️ Möchtest du den vorherigen Import LÖSCHEN und neu starten? (j/n): ").strip().lower()
        if frage == 'j': 
            imp.cleanup_previous_import()
        
        imp.run_import(INPUT_FILE)