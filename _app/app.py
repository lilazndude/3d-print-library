from flask import Flask, render_template, jsonify, request, send_file, abort
import json
import subprocess
import zipfile
import shutil
import threading
import sys
from pathlib import Path

# ── Thumbnail job state ────────────────────────────────────────────────────
_thumb_job     = {'running': False, 'done': 0, 'total': 0, 'current': '', 'errors': []}
_mod_thumb_job = {'running': False, 'done': 0, 'total': 0, 'name': '', 'errors': []}

def _render_thumbnail(mesh_path, out_path):
    import trimesh, numpy as np, matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    loaded = trimesh.load(str(mesh_path))
    if isinstance(loaded, trimesh.Scene):
        geoms = list(loaded.geometry.values())
        if not geoms: return False
        mesh = trimesh.util.concatenate(geoms)
    else:
        mesh = loaded

    if not hasattr(mesh, 'faces') or len(mesh.faces) == 0:
        return False
    if len(mesh.faces) > 30000:
        try: mesh = mesh.simplify_quadric_decimation(30000)
        except: pass

    verts = np.array(mesh.vertices)
    faces = np.array(mesh.faces)

    fig = plt.figure(figsize=(3, 3), dpi=100, facecolor='#080a10')
    ax  = fig.add_subplot(111, projection='3d', facecolor='#080a10')
    polys = Poly3DCollection(verts[faces], alpha=0.9, linewidths=0)
    polys.set_facecolor('#4f7fff')
    ax.add_collection3d(polys)

    center = (verts.max(0) + verts.min(0)) / 2
    half   = max((verts.max(0) - verts.min(0)).max() / 2 * 1.1, 0.001)
    ax.set_xlim(center[0]-half, center[0]+half)
    ax.set_ylim(center[1]-half, center[1]+half)
    ax.set_zlim(center[2]-half, center[2]+half)
    ax.set_axis_off()
    ax.view_init(elev=25, azim=45)
    plt.tight_layout(pad=0)
    plt.savefig(str(out_path), facecolor='#080a10', dpi=100)
    plt.close(fig)
    return True

def _run_thumb_job(force):
    global _thumb_job
    mods = mod_dirs()
    _thumb_job.update({'running': True, 'done': 0, 'total': len(mods), 'current': '', 'errors': []})
    for mod_dir in mods:
        _thumb_job['current'] = mod_dir.name
        files = [f for f in mod_dir.iterdir() if f.is_file() and f.suffix.lower() in {'.stl', '.3mf'}]

        thumb = mod_dir / 'thumbnail.png'
        if files and (not thumb.exists() or force):
            try:
                _render_thumbnail(files[0], thumb)
            except Exception as e:
                _thumb_job['errors'].append(mod_dir.name)

        thumbs_dir = mod_dir / 'thumbs'
        thumbs_dir.mkdir(exist_ok=True)
        for f in files:
            ft = thumbs_dir / (f.name + '.png')
            if not ft.exists() or force:
                try:
                    _render_thumbnail(f, ft)
                except Exception as e:
                    _thumb_job['errors'].append(f'{mod_dir.name}/{f.name}')

        _thumb_job['done'] += 1
    _thumb_job.update({'running': False, 'current': ''})

app = Flask(__name__)

import os
ROOT = Path(os.environ.get('LIBRARY_ROOT', str(Path(__file__).resolve().parent.parent)))
MODELS = 'models'

DEFAULT_STATUSES = [
    {'id': 'want-to-try', 'label': 'Want to Try',  'color': '#3b82f6'},
    {'id': 'testing',     'label': 'Testing',        'color': '#f59e0b'},
    {'id': 'keeper',      'label': 'Keeper',          'color': '#22c55e'},
    {'id': 'failed',      'label': 'Failed',          'color': '#ef4444'},
]

DEFAULT_FILE_STATUSES = [
    {'id': 'needed',   'label': 'Needed',   'color': '#22c55e'},
    {'id': 'optional', 'label': 'Optional', 'color': '#f59e0b'},
]

DEFAULT_CATEGORIES = [
    {'id': 'FDM', 'label': 'FDM', 'color': '#7dd3fc'},
    {'id': 'SLA', 'label': 'SLA', 'color': '#c4b5fd'},
]

def get_categories():
    p = ROOT / 'categories.json'
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return DEFAULT_CATEGORIES

def get_statuses():
    p = ROOT / 'statuses.json'
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return DEFAULT_STATUSES

def get_file_statuses():
    p = ROOT / 'file_statuses.json'
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return DEFAULT_FILE_STATUSES
PRINTABLE = {'.stl', '.3mf', '.orca'}
PDF = {'.pdf'}
EXTRACTABLE = {'.stl', '.3mf', '.obj', '.f3z', '.fcstd', '.step', '.f3d', '.pdf'}

ORCA_CANDIDATES = [
    r"C:\Program Files\OrcaSlicer\orca-slicer.exe",
    r"C:\Program Files (x86)\OrcaSlicer\orca-slicer.exe",
    str(Path.home() / r"AppData\Local\OrcaSlicer\orca-slicer.exe"),
]

def orca_path():
    import os
    custom = os.environ.get('ORCA_PATH')
    if custom and Path(custom).exists():
        return custom
    for p in ORCA_CANDIDATES:
        if Path(p).exists():
            return p
    return None

def cura_path():
    import os, glob as _glob
    custom = os.environ.get('CURA_PATH')
    if custom and Path(custom).exists():
        return custom
    patterns = [
        r"C:\Program Files\UltiMaker Cura *\UltiMaker-Cura.exe",
        r"C:\Program Files\Ultimaker Cura *\Ultimaker-Cura.exe",
        r"C:\Program Files (x86)\Ultimaker Cura *\Ultimaker-Cura.exe",
    ]
    for pattern in patterns:
        matches = sorted(_glob.glob(pattern))
        if matches:
            return matches[-1]
    return None

BAMBU_CANDIDATES = [
    r"C:\Program Files\Bambu Studio\bambu-studio.exe",
    r"C:\Program Files (x86)\Bambu Studio\bambu-studio.exe",
    str(Path.home() / r"AppData\Local\Programs\Bambu Studio\bambu-studio.exe"),
]

def bambu_path():
    import os
    custom = os.environ.get('BAMBU_PATH')
    if custom and Path(custom).exists():
        return custom
    for p in BAMBU_CANDIDATES:
        if Path(p).exists():
            return p
    return None

def creality_path():
    import os, glob as _glob
    custom = os.environ.get('CREALITY_PATH')
    if custom and Path(custom).exists():
        return custom
    patterns = [
        r"C:\Program Files\Creality Print\Creality Print.exe",
        r"C:\Program Files\Creality Print *\Creality Print.exe",
        r"C:\Program Files (x86)\Creality Print\Creality Print.exe",
        r"C:\Program Files (x86)\Creality Print *\Creality Print.exe",
        str(Path.home() / r"AppData\Local\Creality Print\Creality Print.exe"),
    ]
    for pattern in patterns:
        matches = sorted(_glob.glob(pattern))
        if matches:
            return matches[-1]
    return None

def mod_dirs():
    d = ROOT / MODELS
    if not d.exists():
        return []
    return sorted([m for m in d.iterdir() if m.is_dir() and not m.name.startswith('.')])

def read_meta(mod_dir):
    p = mod_dir / 'meta.json'
    return json.loads(p.read_text()) if p.exists() else {}

def write_meta(mod_dir, meta):
    (mod_dir / 'meta.json').write_text(json.dumps(meta, indent=2))

BRAND_PREFIXES = {'gambody', 'thingiverse', 'printables', 'myminifactory', 'cults3d', 'cults', 'thangs', 'sources', 'source'}
NOISE_WORDS    = {'part', 'parts', 'body', 'head', 'base', 'top', 'bottom', 'left', 'right', 'front', 'back',
                  'v1', 'v2', 'v3', 'v4', 'print', 'printed', 'support', 'supports', 'no', 'with', 'and',
                  'the', 'for', 'by', 'of', 'a', 'an', 'tall', 'short', 'small', 'large', 'medium',
                  'version', 'remix', 'fixed', 'updated', 'final', 'new', 'old', 'file', 'files',
                  'stl', '3mf', 'obj', 'model', 'models', 'print', 'assembly', 'asm'}

def _is_noise_token(w):
    import re
    if len(w) < 3:                    return True  # too short
    if re.search(r'\d{2,}', w):       return True  # contains 2+ digits (IDs, version numbers)
    if w in NOISE_WORDS:              return True
    if w in BRAND_PREFIXES:           return True
    return False

def _derive_name_suggestions(mod_dir):
    import re
    from collections import Counter
    files = [f for f in mod_dir.iterdir() if f.is_file() and f.suffix.lower() in PRINTABLE | PDF]
    if not files:
        return []
    stems = [f.stem for f in files]

    def tokenize(stem):
        words = [w.lower() for w in re.split(r'[-_\s]+', stem) if w]
        return [w for w in words if not _is_noise_token(w)]

    word_lists = [tokenize(s) for s in stems]
    suggestions = []

    # 1. Longest common ordered prefix across all files (best signal)
    if len(stems) > 1:
        ref = tokenize(stems[0])
        common = []
        for token in ref:
            idx = len(common)
            if all(len(tokenize(s)) > idx and tokenize(s)[idx] == token for s in stems[1:]):
                common.append(token)
            else:
                break
        if common:
            suggestions.append(' '.join(w.title() for w in common))

    # 2. Words appearing in most files, combined as a phrase
    all_words = [w for wl in word_lists for w in wl]
    counts = Counter(all_words)
    threshold = max(1, len(files) * 0.4)
    frequent = [w for w, c in counts.most_common(8) if c >= threshold]
    if frequent:
        phrase = ' '.join(w.title() for w in frequent[:4])
        if phrase not in suggestions:
            suggestions.append(phrase)
        # Individual high-frequency words as extra chips
        for w in frequent[:5]:
            chip = w.title()
            if chip not in suggestions and chip.lower() not in (s.lower() for s in suggestions):
                suggestions.append(chip)

    return suggestions[:5]

def mod_info(mod_dir):
    meta = read_meta(mod_dir)
    files = sorted([f.name for f in mod_dir.iterdir() if f.is_file() and f.suffix.lower() in PRINTABLE])
    pdf_files = sorted([f.name for f in mod_dir.iterdir() if f.is_file() and f.suffix.lower() in PDF])
    source_dir = mod_dir / 'source'
    source_files = sorted([f.name for f in source_dir.iterdir() if f.is_file()]) if source_dir.exists() else []
    thumbs_dir = mod_dir / 'thumbs'
    rendered = {f.name for f in thumbs_dir.iterdir() if f.is_file()} if thumbs_dir.exists() else set()
    needs_thumbs = bool(files) and (
        not (mod_dir / 'thumbnail.png').exists() or
        any((fn + '.png') not in rendered for fn in files)
    )
    # printer_types: multi-value, falls back to legacy single category field
    printer_types = meta.get('printer_types')
    if not printer_types:
        legacy = meta.get('category', 'FDM')
        printer_types = [legacy] if legacy else ['FDM']
    # file_formats: auto-detected from actual files present
    file_formats = sorted({Path(f).suffix.lstrip('.').upper() for f in files if Path(f).suffix})
    return {
        'printer_types': printer_types,
        'file_formats': file_formats,
        'name': mod_dir.name,
        'files': files,
        'pdf_files': pdf_files,
        'source_files': source_files,
        'needs_thumbs': needs_thumbs,
        'status': meta.get('status', 'want-to-try'),
        'notes': meta.get('notes', ''),
        'source_url': meta.get('source_url', ''),
        'file_notes': meta.get('file_notes', {}),
        'origin': meta.get('origin', 'downloaded'),
        'possible_duplicate': meta.get('possible_duplicate', ''),
        'display_name': meta.get('display_name', ''),
        'needs_display_name': meta.get('needs_display_name', False) and not meta.get('display_name'),
        'newly_imported': meta.get('newly_imported', False),
    }

@app.route('/api/version')
def api_version():
    tmpl = Path(app.template_folder) / 'index.html'
    content = tmpl.read_text(encoding='utf-8')
    return jsonify({
        'template_path': str(tmpl),
        'has_printer_filter': 'printer-filter' in content,
        'has_format_filter': 'format-filter' in content,
        'has_printer_types': 'printer_types' in content,
    })

@app.route('/api/debug')
def api_debug():
    models_dir = ROOT / MODELS
    try:
        mods = mod_dirs()
        mod_names = [m.name for m in mods[:5]]
        mod_count = len(mods)
    except Exception as e:
        mod_names = []
        mod_count = f'error: {e}'
    return jsonify({
        'library_root_env': os.environ.get('LIBRARY_ROOT', 'not set'),
        'root': str(ROOT),
        'models_dir': str(models_dir),
        'models_dir_exists': models_dir.exists(),
        'mod_count': mod_count,
        'first_five': mod_names,
    })

@app.route('/')
def index():
    from flask import make_response
    r = make_response(render_template('index.html'))
    r.headers['Cache-Control'] = 'no-store'
    return r


@app.route('/api/mods/<name>/folder-path')
def api_mod_folder_path(name):
    p = ROOT / MODELS / name
    if not p.is_dir():
        abort(404)
    return jsonify({'path': str(p)})

@app.route('/api/mods/<name>/thumbnail')
def api_thumbnail_get(name):
    p = ROOT / MODELS / name / 'thumbnail.png'
    if not p.exists():
        abort(404)
    return send_file(p, mimetype='image/png', max_age=3600)

@app.route('/api/mods/<name>/thumbs/<path:filename>')
def api_file_thumb(name, filename):
    p = ROOT / MODELS / name / 'thumbs' / (filename + '.png')
    if not p.exists():
        abort(404)
    return send_file(p, mimetype='image/png', max_age=3600)

@app.route('/api/mods/<name>/export')
def api_export_mod(name):
    import io, zipfile as _zf
    d = ROOT / MODELS / name
    if not d.is_dir():
        abort(404)
    meta = read_meta(d)
    file_notes = meta.get('file_notes', {})

    all_print = [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in PRINTABLE]
    needed    = [f for f in all_print if file_notes.get(f.name, {}).get('needed') == 'needed']
    pdfs      = [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in PDF]

    export_files = (needed if needed else all_print) + pdfs

    buf = io.BytesIO()
    with _zf.ZipFile(buf, 'w', _zf.ZIP_DEFLATED) as z:
        for f in export_files:
            z.write(f, f.name)
        notes = meta.get('notes', '').strip()
        if notes:
            z.writestr('NOTES.txt', notes)
    buf.seek(0)

    display_name = meta.get('display_name') or name
    safe_name = display_name.replace('/', '-').replace('\\', '-')
    return send_file(buf, mimetype='application/zip',
                     as_attachment=True,
                     download_name=f'{safe_name}.zip')

@app.route('/api/mods/<name>/name-suggestions')
def api_name_suggestions(name):
    d = ROOT / MODELS / name
    if not d.is_dir():
        abort(404)
    return jsonify(_derive_name_suggestions(d))

@app.route('/api/mods/<name>', methods=['DELETE'])
def api_delete_mod(name):
    d = ROOT / MODELS / name
    if not d.is_dir():
        abort(404)
    shutil.rmtree(str(d))
    return jsonify({'ok': True})

@app.route('/api/mods/<name>/thumbnail', methods=['POST'])
def api_thumbnail_post(name):
    import base64
    d = ROOT / MODELS / name
    if not d.is_dir():
        abort(404)
    data = request.json.get('data', '')
    (d / 'thumbnail.png').write_bytes(base64.b64decode(data))
    return jsonify({'ok': True})

@app.route('/api/mods')
def api_mods():
    return jsonify([mod_info(d) for d in mod_dirs()])

@app.route('/api/categories')
def api_categories():
    stored = get_categories()
    stored_ids = {c['id'] for c in stored}
    used = {}
    for d in mod_dirs():
        meta = read_meta(d)
        cat = meta.get('category', 'FDM')
        if cat and cat not in stored_ids:
            used[cat] = True
    result = list(stored)
    for cat_id in sorted(used.keys()):
        result.append({'id': cat_id, 'label': cat_id, 'color': '#888'})
    return jsonify(result)

@app.route('/api/categories', methods=['POST'])
def api_categories_save():
    cats = request.json
    if not isinstance(cats, list):
        abort(400)
    (ROOT / 'categories.json').write_text(json.dumps(cats, indent=2))
    return jsonify({'ok': True})

@app.route('/api/statuses')
def api_statuses_get():
    return jsonify(get_statuses())

@app.route('/api/statuses', methods=['POST'])
def api_statuses_save():
    statuses = request.json
    if not isinstance(statuses, list):
        abort(400)
    (ROOT / 'statuses.json').write_text(json.dumps(statuses, indent=2))
    return jsonify({'ok': True})

@app.route('/api/file-statuses')
def api_file_statuses_get():
    return jsonify(get_file_statuses())

@app.route('/api/file-statuses', methods=['POST'])
def api_file_statuses_save():
    statuses = request.json
    if not isinstance(statuses, list):
        abort(400)
    (ROOT / 'file_statuses.json').write_text(json.dumps(statuses, indent=2))
    return jsonify({'ok': True})

@app.route('/api/mods/<name>/meta', methods=['POST'])
def api_update_meta(name):
    d = ROOT / MODELS / name
    if not d.is_dir():
        abort(404)
    meta = read_meta(d)
    meta.update(request.json)
    write_meta(d, meta)
    return jsonify({'ok': True})

@app.route('/api/mods/<name>/file/<path:filename>')
def api_file(name, filename):
    p = ROOT / MODELS / name / filename
    if not p.exists():
        abort(404)
    return send_file(p)

@app.route('/api/mods/<name>/open/<path:filename>', methods=['POST'])
def api_open(name, filename):
    p = ROOT / MODELS / name / filename
    if not p.exists():
        abort(404)
    slicer = request.args.get('slicer', 'orca')
    if slicer == 'cura':
        exe = cura_path()
        if not exe:
            return jsonify({'error': 'Cura not found. Set CURA_PATH environment variable.'}), 404
    elif slicer == 'bambu':
        exe = bambu_path()
        if not exe:
            return jsonify({'error': 'Bambu Studio not found. Set BAMBU_PATH environment variable.'}), 404
    elif slicer == 'creality':
        exe = creality_path()
        if not exe:
            return jsonify({'error': 'Creality Print not found. Set CREALITY_PATH environment variable.'}), 404
    else:
        exe = orca_path()
        if not exe:
            return jsonify({'error': 'OrcaSlicer not found. Set ORCA_PATH environment variable.'}), 404
    subprocess.Popen([exe, str(p)])
    return jsonify({'ok': True})

@app.route('/api/orca')
def api_orca():
    exe = orca_path()
    return jsonify({'path': exe, 'found': exe is not None})

@app.route('/api/cura')
def api_cura():
    exe = cura_path()
    return jsonify({'path': exe, 'found': exe is not None})

@app.route('/api/bambu')
def api_bambu():
    exe = bambu_path()
    return jsonify({'path': exe, 'found': exe is not None})

@app.route('/api/creality')
def api_creality():
    exe = creality_path()
    return jsonify({'path': exe, 'found': exe is not None})

@app.route('/api/import', methods=['POST'])
def api_import():
    f = request.files.get('file')
    if not f:
        abort(400)
    category = request.form.get('category', 'FDM')
    ext = Path(f.filename).suffix.lower()
    raw_name = request.form.get('name', '').strip()
    base = Path(f.filename).stem
    name = raw_name or base.replace(' ', '-').lower()
    mod_dir = ROOT / MODELS / name
    mod_dir.mkdir(parents=True, exist_ok=True)

    if ext == '.zip':
        source_dir = mod_dir / 'source'
        source_dir.mkdir(exist_ok=True)
        zip_path = source_dir / f.filename
        f.save(str(zip_path))
        with zipfile.ZipFile(zip_path) as z:
            for member in z.namelist():
                suffix = Path(member).suffix.lower()
                fname = Path(member).name
                if suffix in EXTRACTABLE and fname and not fname.startswith('.') and not fname.startswith('__'):
                    dest = mod_dir / fname
                    if not dest.exists():
                        dest.write_bytes(z.read(member))
    elif ext in PRINTABLE:
        dest = mod_dir / f.filename
        if not dest.exists():
            f.save(str(dest))
    else:
        abort(400)

    meta = read_meta(mod_dir)
    meta['category'] = category
    write_meta(mod_dir, meta)
    return jsonify({'ok': True, 'category': category, 'name': name})

def _run_mod_thumb_job(name, mod_dir):
    global _mod_thumb_job
    files = [f for f in mod_dir.iterdir() if f.is_file() and f.suffix.lower() in {'.stl', '.3mf'}]
    thumbs_dir = mod_dir / 'thumbs'
    thumbs_dir.mkdir(exist_ok=True)
    _mod_thumb_job.update({'running': True, 'done': 0, 'total': len(files), 'name': name, 'errors': []})
    for f in files:
        try:
            _render_thumbnail(f, thumbs_dir / (f.name + '.png'))
        except Exception as e:
            _mod_thumb_job['errors'].append(f.name)
        _mod_thumb_job['done'] += 1
    if files:
        try:
            _render_thumbnail(files[0], mod_dir / 'thumbnail.png')
        except Exception:
            pass
    _mod_thumb_job['running'] = False

@app.route('/api/mods/<name>/generate-thumbnails', methods=['POST'])
def api_generate_mod_thumbs(name):
    global _mod_thumb_job
    if _mod_thumb_job['running']:
        return jsonify({'running': True})
    mod_dir = ROOT / MODELS / name
    if not mod_dir.is_dir():
        abort(404)
    threading.Thread(target=_run_mod_thumb_job, args=(name, mod_dir), daemon=True).start()
    return jsonify({'started': True})

@app.route('/api/mods/<name>/generate-thumbnails/status')
def api_generate_mod_thumbs_status(name):
    return jsonify(_mod_thumb_job)

@app.route('/api/generate-thumbnails', methods=['POST'])
def api_start_thumb_job():
    global _thumb_job
    if _thumb_job['running']:
        return jsonify({'running': True})
    force = (request.json or {}).get('force', False)
    threading.Thread(target=_run_thumb_job, args=(force,), daemon=True).start()
    return jsonify({'started': True})

@app.route('/api/generate-thumbnails/status')
def api_thumb_job_status():
    return jsonify(_thumb_job)

@app.route('/api/fetch-printables', methods=['POST'])
def api_fetch_printables():
    import re as _re, json as _json, urllib.request as _ur
    data     = request.json or {}
    url      = data.get('url', '').strip()
    category = data.get('category', 'FDM')

    m = _re.search(r'printables\.com/model/(\d+)(?:-([a-z0-9-]+))?', url, _re.I)
    if not m:
        return jsonify({'error': 'Not a valid Printables model URL'}), 400

    model_id = m.group(1)
    url_slug = m.group(2) or model_id

    # ── Stage 1: try the pre-packaged zip on Printables CDN ──────────────────
    zip_candidates = [
        f'https://media.printables.com/media/prints/{model_id}/{url_slug}-model_files.zip',
        f'https://media.printables.com/media/prints/{model_id}/model_files.zip',
    ]
    zip_url = None
    for candidate in zip_candidates:
        try:
            req = _ur.Request(candidate, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
            with _ur.urlopen(req, timeout=8) as r:
                if r.status == 200:
                    zip_url = candidate
                    break
        except Exception:
            pass

    name = _re.sub(r'[^a-z0-9-]', '-', url_slug.lower()).strip('-') or model_id

    if zip_url:
        # Reuse the same extraction logic as fetch-zip
        mod_dir    = ROOT / MODELS / name
        source_dir = mod_dir / 'source'
        mod_dir.mkdir(parents=True, exist_ok=True)
        source_dir.mkdir(exist_ok=True)
        filename = zip_url.split('/')[-1]
        zip_path = source_dir / filename
        req = _ur.Request(zip_url, headers={'User-Agent': 'Mozilla/5.0'})
        with _ur.urlopen(req, timeout=60) as r:
            zip_path.write_bytes(r.read())
        with zipfile.ZipFile(zip_path) as z:
            for member in z.namelist():
                suffix = Path(member).suffix.lower()
                fname  = Path(member).name
                if suffix in EXTRACTABLE and fname and not fname.startswith('.') and not fname.startswith('__'):
                    dest = mod_dir / fname
                    if not dest.exists():
                        dest.write_bytes(z.read(member))
        meta = read_meta(mod_dir)
        meta['category']  = category
        meta['source_url'] = url
        write_meta(mod_dir, meta)
        return jsonify({'ok': True, 'name': name, 'category': category, 'method': 'zip'})

    # ── Stage 2: GraphQL API — download individual files ─────────────────────
    gql = _json.dumps({
        'operationName': 'PrintDetail',
        'variables': {'id': model_id},
        'query': 'query PrintDetail($id: ID!) { print(id: $id) { id name slug stls { id name filePath fileSize } } }'
    }).encode()
    try:
        req = _ur.Request(
            'https://api.printables.com/graphql/',
            data=gql,
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        )
        with _ur.urlopen(req, timeout=15) as r:
            api_data = _json.loads(r.read())
    except Exception as e:
        return jsonify({'error': f'Could not reach Printables API: {e}'}), 502

    print_data = (api_data.get('data') or {}).get('print')
    if not print_data:
        return jsonify({'error': 'Model not found or Printables API unavailable'}), 404

    stls = print_data.get('stls') or []
    if not stls:
        return jsonify({'error': 'No printable files found for this model'}), 404

    mod_dir    = ROOT / MODELS / name
    source_dir = mod_dir / 'source'
    mod_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(exist_ok=True)

    errors = []
    downloaded = 0
    for stl in stls:
        file_url = (stl.get('filePath') or '').strip()
        fname    = Path(stl.get('name') or '').name
        if not file_url or not fname:
            continue
        try:
            req = _ur.Request(file_url, headers={'User-Agent': 'Mozilla/5.0'})
            with _ur.urlopen(req, timeout=60) as r:
                dest = mod_dir / fname
                if not dest.exists():
                    dest.write_bytes(r.read())
            downloaded += 1
        except Exception as e:
            errors.append(fname)

    meta = read_meta(mod_dir)
    meta['category']   = category
    meta['source_url'] = url
    write_meta(mod_dir, meta)
    return jsonify({'ok': True, 'name': name, 'category': category,
                    'method': 'api', 'downloaded': downloaded, 'errors': errors})

@app.route('/api/fetch-zip', methods=['POST'])
def api_fetch_zip():
    import re, urllib.request
    data = request.json
    url      = data.get('url', '').strip()
    category = data.get('category', 'FDM')
    name     = data.get('name', '').strip()
    source_url = data.get('source_url', '').strip()
    if not url:
        abort(400)

    filename = url.split('/')[-1].split('?')[0]
    if not filename.lower().endswith('.zip'):
        filename += '.zip'

    if not name:
        n = Path(filename).stem
        n = re.sub(r'\s*\(\d+\)$',      '', n)
        n = re.sub(r'[-_]model_files$',  '', n, flags=re.IGNORECASE)
        n = re.sub(r'[\s_+]+',          '-', n)
        n = re.sub(r'[^a-zA-Z0-9\-]',   '', n)
        n = re.sub(r'-+',               '-', n)
        name = n.strip('-').lower()

    mod_dir    = ROOT / MODELS / name
    source_dir = mod_dir / 'source'
    mod_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(exist_ok=True)

    zip_path = source_dir / filename
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        zip_path.write_bytes(resp.read())

    with zipfile.ZipFile(zip_path) as z:
        for member in z.namelist():
            suffix = Path(member).suffix.lower()
            fname  = Path(member).name
            if suffix in EXTRACTABLE and fname and not fname.startswith('.') and not fname.startswith('__'):
                dest = mod_dir / fname
                if not dest.exists():
                    dest.write_bytes(z.read(member))

    meta = read_meta(mod_dir)
    meta['category'] = category
    if source_url:
        meta['source_url'] = source_url
    write_meta(mod_dir, meta)
    return jsonify({'ok': True, 'category': category, 'name': name})

# ── Watch folder ──────────────────────────────────────────────────────────
_watch_state = {'imported': 0, 'failed': 0, 'last': ''}

def _find_duplicate(slug):
    """Return the name of an existing mod that is a substring match of slug, or None."""
    for d in mod_dirs():
        name = d.name
        if name == slug:
            continue
        if slug in name or name in slug:
            return name
    return None

def _unique_slug(base):
    """Return base slug if unused or empty, otherwise base-2, base-3, etc."""
    candidate = base
    counter = 2
    while True:
        d = ROOT / MODELS / candidate
        if not d.exists():
            break
        has_files = any(f for f in d.iterdir() if f.is_file() and f.suffix.lower() in PRINTABLE)
        if not has_files:
            break  # folder exists but is empty — reuse it
        candidate = f'{base}-{counter}'
        counter += 1
    return candidate

def _watch_slug(stem):
    import re
    n = re.sub(r'\s*\(\d+\)$',     '', stem)
    n = re.sub(r'[-_]model_files$', '', n, flags=re.IGNORECASE)
    n = re.sub(r'[\s_+]+',         '-', n)
    n = re.sub(r'[^a-zA-Z0-9\-]',  '', n)
    n = re.sub(r'-+',              '-', n)
    return n.strip('-').lower() or 'import'

def _watch_import_zip(f, processed_dir, category='FDM'):
    global _watch_state
    name    = _unique_slug(_watch_slug(f.stem))
    mod_dir = ROOT / MODELS / name
    mod_dir.mkdir(parents=True, exist_ok=True)
    src_dir = mod_dir / 'source'
    src_dir.mkdir(exist_ok=True)
    dest_zip = src_dir / f.name
    shutil.copy2(f, dest_zip)
    try:
        with zipfile.ZipFile(dest_zip) as z:
            for member in z.namelist():
                suffix = Path(member).suffix.lower()
                fname  = Path(member).name
                if suffix in EXTRACTABLE and fname and not fname.startswith('.') and not fname.startswith('__'):
                    dest = mod_dir / fname
                    if not dest.exists():
                        dest.write_bytes(z.read(member))
        meta = read_meta(mod_dir)
        meta['category'] = category
        meta['newly_imported'] = True
        dup = _find_duplicate(name)
        if dup:
            meta['possible_duplicate'] = dup
        if any(name.startswith(b) for b in BRAND_PREFIXES):
            meta.setdefault('needs_display_name', True)
        write_meta(mod_dir, meta)
        shutil.move(str(f), str(processed_dir / f.name))
        _watch_state['imported'] += 1
        _watch_state['last'] = name
    except Exception as e:
        _watch_state['failed'] += 1

def _watch_import_model(f, processed_dir, category='FDM'):
    global _watch_state
    name    = _unique_slug(_watch_slug(f.stem))
    mod_dir = ROOT / MODELS / name
    mod_dir.mkdir(parents=True, exist_ok=True)
    dest = mod_dir / f.name
    if not dest.exists():
        shutil.copy2(f, dest)
    meta = read_meta(mod_dir)
    meta['category'] = category
    meta['newly_imported'] = True
    dup = _find_duplicate(name)
    if dup:
        meta['possible_duplicate'] = dup
    if any(name.startswith(b) for b in BRAND_PREFIXES):
        meta.setdefault('needs_display_name', True)
    write_meta(mod_dir, meta)
    shutil.move(str(f), str(processed_dir / f.name))
    _watch_state['imported'] += 1
    _watch_state['last'] = name

def _run_watch_folder():
    import time, re
    watch_root = Path(os.environ.get('WATCH_FOLDER',
                      str(Path.home() / 'Downloads' / '3d-import')))
    # Support category subfolders: 3d-import/FDM/ and 3d-import/SLA/
    scan_dirs = {
        watch_root:            'FDM',
        watch_root / 'FDM':    'FDM',
        watch_root / 'SLA':    'SLA',
    }
    while True:
        try:
            watch_root.mkdir(parents=True, exist_ok=True)
            for scan_dir, category in scan_dirs.items():
                if not scan_dir.exists():
                    continue
                processed = scan_dir / '_processed'
                processed.mkdir(exist_ok=True)
                for f in sorted(scan_dir.iterdir()):
                    if not f.is_file() or f.name.startswith('.') or f.name.startswith('_'):
                        continue
                    # Wait until file size is stable (not still copying)
                    try:
                        s1 = f.stat().st_size
                        time.sleep(0.5)
                        if f.stat().st_size != s1:
                            continue
                    except Exception:
                        continue
                    ext = f.suffix.lower()
                    if ext == '.zip':
                        _watch_import_zip(f, processed, category)
                    elif ext in PRINTABLE:
                        _watch_import_model(f, processed, category)
        except Exception:
            pass
        time.sleep(5)

@app.route('/api/watch-folder')
def api_watch_folder():
    watch_root = Path(os.environ.get('WATCH_FOLDER',
                      str(Path.home() / 'Downloads' / '3d-import')))
    return jsonify({
        'path':     str(watch_root),
        'exists':   watch_root.exists(),
        'imported': _watch_state['imported'],
        'failed':   _watch_state['failed'],
        'last':     _watch_state['last'],
    })

threading.Thread(target=_run_watch_folder, daemon=True).start()

def _run_flask():
    app.run(host='0.0.0.0', port=5000, use_reloader=False)

if __name__ == '__main__':
    import webbrowser
    in_docker = os.environ.get('LIBRARY_ROOT') is not None

    if in_docker:
        _run_flask()
    elif sys.platform == 'win32':
        try:
            import pystray
            from PIL import Image as _PILImage, ImageDraw as _PILDraw

            # Flask in daemon thread; pystray must own the main thread on Windows
            threading.Thread(target=_run_flask, daemon=True).start()
            threading.Timer(1.2, lambda: webbrowser.open('http://localhost:5000')).start()

            _sz = 64
            _img = _PILImage.new('RGBA', (_sz, _sz), (0, 0, 0, 0))
            _PILDraw.Draw(_img).ellipse([2, 2, _sz - 2, _sz - 2], fill='#4f7fff')

            def _stop(icon, item):
                icon.stop()
                os._exit(0)

            _menu = pystray.Menu(
                pystray.MenuItem('Open 3D Print Library', lambda icon, item: webbrowser.open('http://localhost:5000'), default=True),
                pystray.MenuItem('Stop Server', _stop),
            )
            pystray.Icon('3D Print Library', _img, '3D Print Library', _menu).run()

        except ImportError:
            threading.Timer(1, lambda: webbrowser.open('http://localhost:5000')).start()
            _run_flask()
    else:
        threading.Timer(1, lambda: webbrowser.open('http://localhost:5000')).start()
        _run_flask()
