import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox

def check_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    errors = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        indent_level = len(line) - len(line.lstrip())

        if re.match(r"^(def|if|elif|else|for|while|try|except|class)\b", stripped) and not stripped.endswith(":"):
            errors.append(f"{file_path} | Zeile {i+1}: Struktur ohne ':'")

        if stripped.startswith("return") and indent_level == 0:
            errors.append(f"{file_path} | Zeile {i+1}: 'return' außerhalb von Block?")

        if "\t" in line and " " in line[:line.find("\t")]:
            errors.append(f"{file_path} | Zeile {i+1}: Mischung aus Tab & Leerzeichen")

    return errors

def scan_folder(folder_path):
    all_errors = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                all_errors.extend(check_file(full_path))
    return all_errors

def choose_folder():
    folder = filedialog.askdirectory()
    if not folder:
        return

    result = scan_folder(folder)
    log_path = os.path.join(folder, "indent_log.txt")

    with open(log_path, "w", encoding="utf-8") as f:
        if result:
            for line in result:
                f.write(line + "\n")
        else:
            f.write("✅ Keine Einrückungsfehler gefunden.")

    messagebox.showinfo("Fertig!", f"Prüfung abgeschlossen.\nLog gespeichert unter:\n{log_path}")

# 🖼️ GUI erstellen
root = tk.Tk()
root.title("Einrückungsprüfer")
root.geometry("400x150")

label = tk.Label(root, text="Wähle einen Ordner mit .py-Dateien zur Prüfung:", font=("Arial", 11))
label.pack(pady=15)

btn = tk.Button(root, text="Ordner auswählen & prüfen", command=choose_folder, font=("Arial", 12))
btn.pack(pady=10)

root.mainloop()
