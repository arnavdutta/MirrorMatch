import os
import zlib
import threading
import time
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import csv
from datetime import datetime
import subprocess
import sys

# ---------------- Duplicate Finder Logic ----------------
def file_crc32(file_path, chunk_size=65536):
    prev = 0
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                prev = zlib.crc32(chunk, prev)
        return format(prev & 0xFFFFFFFF, '08x')
    except (OSError, PermissionError):
        return None

def files_are_identical(file1, file2, chunk_size=65536, pause_flag=None, cancel_flag=None):
    try:
        with open(file1, "rb") as f1, open(file2, "rb") as f2:
            while True:
                if cancel_flag and cancel_flag.is_set():
                    return False
                if pause_flag:
                    pause_flag.wait()

                b1 = f1.read(chunk_size)
                b2 = f2.read(chunk_size)
                if b1 != b2:
                    return False
                if not b1:
                    break
        return True
    except (OSError, PermissionError):
        return False

def find_duplicate_files(root_folder, extensions=None, progress_callback=None, cancel_flag=None, pause_flag=None):
    size_map = {}
    all_files = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if cancel_flag and cancel_flag.is_set():
                return []
            if pause_flag:
                pause_flag.wait()

            if extensions and not any(filename.lower().endswith(ext) for ext in extensions):
                continue

            file_path = os.path.abspath(os.path.join(dirpath, filename))
            try:
                size = os.path.getsize(file_path)
                size_map.setdefault(size, []).append(file_path)
                all_files.append(file_path)
            except (OSError, PermissionError):
                continue

    duplicates_verified = []
    processed = 0
    total = len(all_files)

    for size, files in size_map.items():
        if cancel_flag and cancel_flag.is_set():
            return []
        if len(files) < 2:
            continue

        crc_map = {}
        for file_path in files:
            if cancel_flag and cancel_flag.is_set():
                return []
            if pause_flag:
                pause_flag.wait()

            checksum = file_crc32(file_path)
            if checksum:
                crc_map.setdefault(checksum, []).append(file_path)
            processed += 1
            if progress_callback:
                progress_callback(processed, total)

        for checksum, file_list in crc_map.items():
            if len(file_list) > 1:
                checked = set()
                for i in range(len(file_list)):
                    if cancel_flag and cancel_flag.is_set():
                        return []
                    if pause_flag:
                        pause_flag.wait()

                    if file_list[i] in checked:
                        continue
                    duplicate_set = [file_list[i]]
                    for j in range(i + 1, len(file_list)):
                        if cancel_flag and cancel_flag.is_set():
                            return []
                        if pause_flag:
                            pause_flag.wait()

                        if file_list[j] not in checked and files_are_identical(
                            file_list[i], file_list[j], pause_flag=pause_flag, cancel_flag=cancel_flag
                        ):
                            duplicate_set.append(file_list[j])
                            checked.add(file_list[j])
                    if len(duplicate_set) > 1:
                        duplicates_verified.append((checksum, duplicate_set))
                    checked.add(file_list[i])

    grouped_results = [{"checksum": checksum, "files": paths} for checksum, paths in duplicates_verified]

    if progress_callback:
        progress_callback(total, total)
    return grouped_results


def format_time(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {minutes}m {seconds}s"
    days, hours = divmod(hours, 24)
    return f"{days}d {hours}h {minutes}m {seconds}s"


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        try:
            x, y, cx, cy = self.widget.bbox("insert")
        except Exception:
            x, y, cx, cy = 0, 0, 0, 0
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="yellow", relief="solid", borderwidth=1)
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class DuplicateFinderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MirrorMatch: Find Duplicates")
        self.root.resizable(False, False)

        menubar = tk.Menu(root)
        root.config(menu=menubar)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        self.folder_path = tk.StringVar()
        frame = tk.Frame(root)
        frame.pack(padx=10, pady=10)

        tk.Label(frame, text="Folder:").grid(row=0, column=0, sticky="w")
        browse_btn = tk.Button(frame, text="Browse", command=self.browse_folder)
        tk.Entry(frame, textvariable=self.folder_path, width=50).grid(row=0, column=1)
        browse_btn.grid(row=0, column=2, padx=5)
        ToolTip(browse_btn, "Browse and select the folder to scan for duplicate files.")

        tk.Label(frame, text="Filter Extensions:").grid(row=1, column=0, sticky="w")
        self.extension_vars = {}
        extensions = ["docx", "xlsx", "doc", "ppt", "pptx", "xls", "png", "jpg", "gif", "heif"]
        ext_frame = tk.Frame(frame)
        ext_frame.grid(row=1, column=1, columnspan=2, sticky="w")
        self.all_var = tk.BooleanVar(value=True)
        all_cb = tk.Checkbutton(ext_frame, text="All", variable=self.all_var, command=self.toggle_all_extensions)
        all_cb.pack(side=tk.LEFT)
        for ext in extensions:
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(ext_frame, text=ext, variable=var, command=self.unset_all)
            cb.pack(side=tk.LEFT)
            self.extension_vars[ext] = var
        ToolTip(ext_frame, "Select one or more extensions to filter by during scan, or choose All.")

        self.progress = ttk.Progressbar(frame, length=400, mode="determinate")
        self.progress.grid(row=2, column=0, columnspan=3, pady=5)
        self.progress_label = tk.Label(frame, text="0 / 0 files processed")
        self.progress_label.grid(row=3, column=0, columnspan=3)

        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=5)

        self.start_btn = tk.Button(btn_frame, text="Find Duplicates", command=self.start_scan)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.start_btn, "Start scanning the selected folder for duplicate files.")

        self.pause_btn = tk.Button(btn_frame, text="Pause", command=self.toggle_pause, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.pause_btn, "Pause or resume the ongoing scan.")

        self.cancel_btn = tk.Button(btn_frame, text="Cancel", command=self.cancel_scan, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.cancel_btn, "Cancel the ongoing scan (if running).")

        self.start_time = None
        self.cancel_flag = threading.Event()
        self.pause_flag = threading.Event()
        self.pause_flag.set()
        self.scanning = False
        self.paused = False
        self.state_lock = threading.Lock()

    def toggle_all_extensions(self):
        if self.all_var.get():
            for var in self.extension_vars.values():
                var.set(False)

    def unset_all(self):
        if any(var.get() for var in self.extension_vars.values()):
            self.all_var.set(False)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def start_scan(self):
        folder = self.folder_path.get()
        if not folder:
            messagebox.showwarning("MirrorMatch", "Please select a folder")
            return
        with self.state_lock:
            self.cancel_flag.clear()
            self.pause_flag.set()
            self.paused = False
            self.progress["value"] = 0
            self.progress["maximum"] = 0
            self.progress_label.config(text="0 / 0 files processed")
            self.start_time = time.time()
            self.scanning = True
            self.cancel_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.NORMAL, text="Pause")
            self.start_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.run_scan, args=(folder,), daemon=True).start()

    def cancel_scan(self):
        with self.state_lock:
            if not self.scanning:
                return
            if messagebox.askokcancel("MirrorMatch", "Are you sure you want to cancel the scan?"):
                self.cancel_flag.set()
                self.progress["value"] = 0
                self.progress["maximum"] = 0
                self.progress_label.config(text="0 / 0 files processed")
                self.pause_btn.config(state=tk.DISABLED, text="Pause")
                self.cancel_btn.config(state=tk.DISABLED)
                self.start_btn.config(state=tk.NORMAL)
                self.scanning = False
                self.paused = False
                self.pause_flag.set()

    def toggle_pause(self):
        with self.state_lock:
            if not self.scanning:
                return
            if self.paused:
                self.pause_flag.set()
                self.pause_btn.config(text="Pause")
                self.paused = False
            else:
                self.pause_flag.clear()
                self.pause_btn.config(text="Resume")
                self.paused = True

    def run_scan(self, folder):
        def progress_callback(done, total):
            def update_ui():
                self.progress["maximum"] = total
                self.progress["value"] = done
                elapsed = time.time() - self.start_time
                avg_time = elapsed / done if done else 0
                remaining = avg_time * (total - done) if avg_time else 0
                eta_text = f"{done} / {total} files processed | Elapsed: {format_time(elapsed)} | ETA: {format_time(remaining)}"
                self.progress_label.config(text=eta_text)
            self.root.after(0, update_ui)

        if self.all_var.get():
            extensions = None
        else:
            extensions = [f".{ext}" for ext, var in self.extension_vars.items() if var.get()]

        grouped_results = find_duplicate_files(folder, extensions=extensions, progress_callback=progress_callback, cancel_flag=self.cancel_flag, pause_flag=self.pause_flag)

        def finalize():
            with self.state_lock:
                if self.cancel_flag.is_set():
                    messagebox.showinfo("MirrorMatch", "User cancelled the scanning operation.")
                elif grouped_results:
                    folder_name = os.path.basename(os.path.normpath(folder))
                    timestamp = datetime.now().strftime("%d%m%yT%H%M%S")
                    csv_filename = f"duplicate_files_{folder_name}_{timestamp}.csv"
                    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                        writer.writerow(["checksum", "file_path", "duplicate_count"])
                        for group in grouped_results:
                            for file in group['files']:
                                writer.writerow([group['checksum'], file, len(group['files'])])
                            writer.writerow([])
                            writer.writerow([])
                    messagebox.showinfo("MirrorMatch", f"Scanning completed. CSV saved at:\n{os.path.abspath(csv_filename)}")
                    try:
                        if os.name == 'nt':
                            os.startfile(csv_filename)
                        elif sys.platform == 'darwin':
                            subprocess.call(('open', csv_filename))
                        elif os.name == 'posix':
                            subprocess.call(('xdg-open', csv_filename))
                    except Exception as e:
                        messagebox.showwarning("MirrorMatch", f"Could not open CSV automatically.\n{e}")
                else:
                    messagebox.showinfo("MirrorMatch", "Scanning completed. No duplicates found.")

                self.cancel_btn.config(state=tk.DISABLED)
                self.pause_btn.config(state=tk.DISABLED, text="Pause")
                self.start_btn.config(state=tk.NORMAL)
                self.scanning = False
                self.paused = False
        self.root.after(0, finalize)

    def show_about(self):
        messagebox.showinfo(
            "MirrorMatch",
            "MirrorMatch: Find Duplicates\nVersion 1.6.1\n\n"
            "Developed by Arnav Dutta.\n\n"
            "This software scans the chosen folder, identifies duplicate files "
            "by comparing checksums and full contents, and produces a CSV report."
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = DuplicateFinderGUI(root)
    root.mainloop()
