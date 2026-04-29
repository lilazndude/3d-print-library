# 3D Print Library — Project Summary

## Core App
- Flask backend + single-page frontend with Bootstrap 5 dark theme
- Three.js for in-browser 3D preview (STL and 3MF)
- Flat `models/<name>/` directory structure with `meta.json` per mod

## Import & Library Management
- ZIP import with automatic file extraction
- Direct STL/3MF import
- Printables URL fetcher (zip CDN + GraphQL API fallback)
- Auto-import watch folder (`~/Downloads/3d-import`) with FDM/SLA subfolders
- Source zip storage per mod

## Detail View
- List view grouped by status with collapsible sections
- Section headers: arrow left, status label, white count, separator line
- Per-card labeled rows for Printer Type and File Format badges
- File thumbnail strip (wrapping grid, not horizontal scroll)
- Size variant auto-grouping with custom picker and floating hover preview
- PDF documentation slide-out panel (resizable, snappable)
- Render button per card with animated progress bar (wraps below content correctly)
- 8px card spacing within sections

## Printer Type & Format Filtering
- Replaced single category with multi-select printer types per mod
- Auto-detected file format filter built from actual files in library
- Dynamic/editable printer types via gear modal (drag to reorder, color picker)
- Format filter auto-populates from what's actually in your library
- STL moved out of printer types — it's a file format, not a print technology

## Thumbnail System
- Server-side rendering with trimesh + matplotlib (Agg backend)
- Per-file thumbs in `thumbs/` directory
- Background render job with polling progress bar
- `Cache-Control: max-age=3600` to prevent re-fetching
- `loading="lazy"` on strip images
- `needs_thumbs` detects missing `thumbnail.png` even when file thumbs exist
- `lxml` added to requirements for 3MF parsing

## Slicer Integration
- OrcaSlicer, Cura, Bambu Studio, Creality Print auto-detection
- Per-file open-in-slicer with dropdown selector
- Slicer status icons in top bar with "Slicers" label

## Status & Customization
- Fully customizable mod statuses with color and drag-to-reorder
- File-level part statuses (Needed / Optional)
- Auto-save with 600ms debounce on all fields
- Origin flag (Downloaded vs My Design) driving the Mine filter

## Modal Polish
- Printer type toggle buttons (multi-select, auto-saves)
- File formats display (read-only, auto-detected)
- Visible labels on all form fields
- Copy folder path button grouped with close button
- Save & Close button

## Windows Launcher & Tray
- `install.bat` / `install.sh` for first-time setup
- `run.bat` kills stale port 5000 processes on startup, uses `-B` to bypass stale bytecode cache on network shares
- System tray icon (pystray + Pillow) with Open and Stop Server
- `make-shortcuts.bat` creates a single smart desktop shortcut
- `no-store` cache header on the HTML route to prevent browser caching stale pages

## Bug Fixes
- `__pycache__` stale bytecode on SMB network share causing old code to run
- Multiple Python processes accumulating on port 5000
- UNC path handling throughout batch files
- Missing `lxml` breaking 3MF thumbnail rendering
- `flex-wrap` on detail rows so render progress bar wraps cleanly
- JS event delegation for dynamically rendered filter buttons
- Removed file name text row from cards (thumbnails already show filenames)

## Git
- `.gitignore` excluding models, venvs, user config, archives
- Repo initialized at correct root level
- Pushed to https://github.com/lilazndude/3d-print-library


added support for ambiguous files.  something like gambody would be imported and indexed if duplicate (additional files from that source)
clicking on the 'new' filter at the top will filter to that card.  suggestions should be there, so the user can label that project (does not change the folder name)