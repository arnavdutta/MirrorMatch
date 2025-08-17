# 🔍 MirrorMatch - Duplicate File Finder

MirrorMatch is a **cross-platform desktop utility** (Python + Tkinter) to scan folders and find duplicate files.  
It combines **file size filtering, fast CRC32 checksums, and byte-level comparison** to ensure accuracy.  

Results are exported into a clean **CSV report**, and you can easily review or open them in Excel/LibreOffice.

---

## ✨ Features

✅ **Accurate duplicate detection**  
&nbsp;&nbsp;Uses a 3-step process:
1. Group files by size (fast pre-check).  
2. Within equal-sized groups, compute CRC32 checksum.  
3. For checksum matches, verify with byte-for-byte comparison.  

✅ **Intuitive interface**  
- Browse folder easily.  
- Progress bar with real-time ETA.  
- Tooltips to guide users.  

✅ **Control the scan**  
- **Pause / Resume** whenever you want.  
- **Cancel** the scan and reset progress instantly.  

✅ **CSV export**  
- CSV report with duplicate groups.  
- Opens automatically after scan (on Windows, macOS, and Linux).  

✅ **Cross-platform**  
Works on **Windows, macOS, and Linux** with Python 3.x.

---

## 🚀 Installation & Usage

1. Clone the repository:

2. Install dependencies:

*(Only uses standard library, no extra packages needed by default!)*
3. Run the application:


---

## 📊 Output Example

CSV output file:  
`duplicate_files_<foldername>_<timestamp>.csv`

| checksum  | file_path                          | duplicate_count |
|-----------|------------------------------------|-----------------|
| a3f4c2e1  | /path/to/duplicate1.txt            | 3 |
| a3f4c2e1  | /path/to/duplicate2.txt            | 3 |
| a3f4c2e1  | /path/to/duplicate3.txt            | 3 |
| b5e8d1f9  | /path/to/another_duplicate.docx    | 2 |

---

## ⚙️ Options & Controls

- **Browse**: Pick a folder to scan.  
- **Find Duplicates**: Starts scanning in a background thread (UI stays responsive).  
- **Pause / Resume**: Temporarily stop and continue scanning without losing progress.  
- **Cancel**: Abort scan and reset progress bar instantly.  
- **About**: Shows app version and credits.  

---

## 🛠️ Tech Stack

- **Language**: Python 3  
- **GUI**: Tkinter (cross-platform native GUI)  
- **Logic**: `os`, `zlib`, `threading`, `csv`, `subprocess`  

---

## 👨‍💻 Author

**Arnav Dutta**  

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



