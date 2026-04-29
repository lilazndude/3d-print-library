# 3D Print Library

A self-hosted web app for organizing your 3D print model collection. Run it locally on Windows or on a home server (CasaOS/Docker). Browse, tag, preview, and open models directly in your slicer from one place.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey) ![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **Detail & grid views** — browse your library as a list grouped by status or as a card grid
- **3D preview** — in-browser viewer for STL and 3MF files via Three.js
- **Thumbnail generation** — server-side rendered thumbnails per file using trimesh + matplotlib
- **Printer type & file format filters** — multi-select printer type tags (FDM, SLA, etc.) and auto-detected format filters (STL, 3MF)
- **Slicer integration** — open any file directly in OrcaSlicer, Cura, Bambu Studio, or Creality Print
- **Custom status flags** — fully customizable Kanban-style statuses (Want to Try, Testing, Keeper, etc.) with colors
- **Part-level tracking** — mark individual files as Needed or Optional with notes
- **Size variant grouping** — files like `box-1x1.stl`, `box-2x2.stl` are automatically grouped with a variant picker
- **PDF documentation** — slide-out panel for viewing instruction PDFs alongside the model
- **Auto-import watch folder** — drop ZIPs or model files into `~/Downloads/3d-import` and they import automatically
- **Printables integration** — fetch models directly from a Printables URL
- **System tray** — Windows tray icon to open the site or stop the server

---

## Installation

### Windows

```bat
install.bat
```

Then launch with:

```bat
run.bat
```

A browser window opens automatically. A tray icon appears in the system tray — right-click to open the site or stop the server.

To create a desktop shortcut:

```bat
make-shortcuts.bat
```

### Linux / CasaOS

```bash
chmod +x install.sh run.sh
./install.sh
./run.sh
```

For CasaOS Docker deployment, see `_app/deploy-casaos.sh`.

---

## Requirements

- Python 3.10+
- Dependencies installed automatically by `install.bat` / `install.sh`:
  - Flask, trimesh, NumPy, matplotlib, SciPy, NetworkX, lxml
  - pystray + Pillow (Windows only, for system tray)

---

## Project Structure

```
repo/
├── models/              # Your model library (gitignored)
├── _app/
│   ├── app.py           # Flask backend
│   ├── templates/
│   │   └── index.html   # Full frontend (single page)
│   └── requirements.txt
├── install.bat / install.sh
├── run.bat / run.sh
└── make-shortcuts.bat
```

Each model lives in `models/<name>/` with:
- Printable files (`.stl`, `.3mf`, `.orca`)
- `meta.json` — status, notes, printer types, file notes
- `thumbs/` — generated thumbnails per file
- `source/` — original ZIP archive

---

## Slicer Detection

Slicers are auto-detected from standard install locations. To override, set environment variables before running:

| Slicer | Variable |
|--------|----------|
| OrcaSlicer | `ORCA_PATH` |
| Cura | `CURA_PATH` |
| Bambu Studio | `BAMBU_PATH` |
| Creality Print | `CREALITY_PATH` |

---

## Auto-Import Watch Folder

Drop files into `~/Downloads/3d-import/` and they will be imported automatically:

- `.zip` — extracted, printable files pulled out
- `.stl` / `.3mf` — imported directly
- `FDM/` subfolder — tagged as FDM
- `SLA/` subfolder — tagged as SLA
