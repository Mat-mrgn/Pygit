import os
import json
from datetime import datetime
from pathlib import Path
from portabilite import *
from configfile import get_cfg
cfg = get_cfg()
import lang

COMPUTER = cfg.PC

#---------------------------------ARCHITECTURE OF PYGIT-----------------------------------------
#
#    PYGIT (folder)
#     |
#     |----->saves (folder)
#     |        |            
#     |        |----->save_0 (folder)                       
#     |        |        |----->current_save (folder)                        
#     |        |        |             |----->Jsontree.json (the tree of the date.zip folder)
#     |        |        |             |----->{date}.zip (the current save named by the date it was make at the format dd:mm:yy_hh:mm.zip)
#     |        |        |----->old_save (folder)
#     |        |                      |
#     |        |                      |---->{date}.zip an old save. In the old_save folder a maximum number of save is fixed by the user in this file right above
#     |        |                      |... and beyond until MAX_OLD_SAVE is reached
#     |       ...
#     |        |----->Save_N (folder)
#     |        |-----> manifest.json
#     |
#     |-------Py (folder)   -> Note that this is the app and could be
#     |        |           anywhere else in the OS as long as you set the BASE_DIR variable to another place
#     |        |
#     |        |-------lang(folder) -> What langage your interface will display his message
#     |        |         |
#     |        |         |---->en.json
#     |        |         |---->fr.json
#     |        |         |---->other_lang.json...
#     |        |
#     |        |
#     |        |-------web(folder) -> it's all about the GUI...
#     |        |         |
#     |        |         |---->index.html
#     |        |         |-------UI(folder) −> it's where all the stylesheet while be
#     |        |         |        |
#     |        |         |        |--->...somes stylesheet...
#     |        |         |        |
#     |        |         |
#     |        |
#     |        |---->lang.py
#     |        |---->save.py
#     |        |---->checksum.py
#     |        |---->pathree.py
#     |        |---->README.py (we are here)
#     |        |---->portabilite.py 
#     |        |---->pygnore.py 
#     |        |---->configfile.py
#     |        |---->CLI.py 
#     |        |---->manifest.py
#     |        |---->GUI_engine.py
#     |        |---->GUI.py 
#     |
#     |------> README.txt (and here)
#     |------>.pygnore 
#     |------>.config-file
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.

JOURNAL_NAME = ".readme.json"
RENDER_NAME = "README.txt"
DRYRUN_NAME = ".dryrun.txt"
_CHANGE_ORDER = (
    ("Moved", "/"),
    ("Created", "+"),
    ("Deleted", "-"),
    ("Modified", "*"),
)

_ERROR_KEYS = {
    "save": "readme_error_save",
    "zip": "readme_error_zip",
    "verify": "readme_error_verify",
    "restore": "readme_error_restore",
}

_TS_FORMAT = "%d/%m/%Y %H:%M"

def _slot(dest):
    """Resolve a slot folder. cfg.DIR is read HERE, not at import time: the old
    module-level _APP_DIR/_SAVE_DIR froze the value of the first import and kept
    pointing at the previous folder after a setdir."""
    return Path(dest) if dest is not None else Path(cfg.DIR)

def _now():
    return datetime.now().isoformat(timespec="seconds")


def _entry(key, params=None, sign=None):
    entry = {"ts": _now(), "key": key}
    if params:
        entry["params"] = params
    if sign:
        entry["sign"] = sign
    return entry

def _load(dest):
    """Read a slot's journal, migrating a legacy plain-text README on the way.

    Returns:
        list: the journal entries, [] if the slot has no history yet
    """
    folder = _slot(dest)
    journal = folder / JOURNAL_NAME

    if journal.exists():
        try:
            with open(journal, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            pass
        # Un journal illisible n'est pas écrasé en silence : il est mis de côté,
        # sinon la première écriture qui suit efface tout l'historique.
        try:
            os.replace(journal, folder / (JOURNAL_NAME + ".bad"))
        except OSError:
            pass
        return []

    legacy = folder / RENDER_NAME
    if legacy.exists() and legacy.stat().st_size > 0:
        try:
            raw = legacy.read_text(encoding="utf-8", errors="replace").rstrip("\n")
            return [{"ts": _now(), "text": raw}]
        except OSError:
            return []
    return []


def _write(dest, entries):
    """Persist the journal, then regenerate the rendering from it.

    os.replace() is atomic on POSIX and Windows alike: a crash mid-write leaves
    the previous journal intact instead of a truncated one. For a backup tool,
    a half-written history is worse than a stale one."""
    folder = _slot(dest)
    folder.mkdir(parents=True, exist_ok=True)

    tmp = folder / (JOURNAL_NAME + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
    os.replace(tmp, folder / JOURNAL_NAME)

    rerender(folder, entries)
    
def _append(dest, key, params=None, sign=None):
    entries = _load(dest)
    entries.append(_entry(key, params, sign))
    _write(dest, entries)

def _extend(dest, new_entries):
    """Batch append: one read and one write for a whole diff, instead of one
    round-trip per changed file."""
    if not new_entries:
        return
    entries = _load(dest)
    entries.extend(new_entries)
    _write(dest, entries)
    
def _change_entries(comparedict, prefix):
    """Turn a comparefolder() diff into journal entries.

    Args:
        comparedict (dict): as returned by comparefolder()
        prefix (str): "readme" (what happened) or "dryrun_would" (what would)

    The tuple layout comes straight from comparefolder: Moved is (from, to),
    Created is (None, path), Deleted is (path, None), Modified is (path, path).
    """
    out = []
    for category, sign in _CHANGE_ORDER:
        key = f"{prefix}_{category.lower()}"
        for item in comparedict.get(category, []):
            if category == "Moved":
                params = {"src": str(item[0]), "dst": str(item[1])}
            elif category == "Created":
                params = {"path": str(item[1])}
            else:
                params = {"path": str(item[0])}
            out.append(_entry(key, params, sign))
    return out

def _stamp(ts):
    try:
        return datetime.fromisoformat(ts).strftime(_TS_FORMAT)
    except (TypeError, ValueError):
        return str(ts)

def _render_entry(entry):
    """One journal entry -> one line, in the language currently loaded."""
    if "text" in entry:
        return entry["text"]
    body = lang.t(entry.get("key", ""), **entry.get("params", {}))
    sign = entry.get("sign")
    if sign:
        return f"\t({sign}) {body}"
    return f"{_stamp(entry.get('ts'))} : {body}"

def rerender(dest=None, entries=None):
    """Regenerate README.txt from the journal, in the language currently loaded.

    Call this after lang.load() for every known slot: that is what makes a
    language switch retroactive over the whole history.

    Returns:
        Path: the rendered file, or None if the slot has no journal
    """
    folder = _slot(dest)
    if entries is None:
        entries = _load(folder)
    if not entries:
        return None

    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / (RENDER_NAME + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(_render_entry(entry) + "\n")
    path = folder / RENDER_NAME
    os.replace(tmp, path)
    return path



#=============================================================================
#=================================== WRITE ===================================
#=============================================================================


def initREADME(dest=None):
    """Open the history of a slot. Replaces createREADME("init").

    Unlike createREADME, this APPENDS instead of truncating: a slot that already
    carries a history keeps it."""
    _append(dest, "readme_init")
    
def parseREADME(comparedict, dest=None):
    """Log what a save actually changed."""
    _extend(dest, _change_entries(comparedict, "readme"))
    
def nodiffREADME(dest=None):
    _append(dest, "readme_nodiff")

def errorREADME(err, operation, dest=None):
    """Log a failure. operation is one of save / zip / verify / restore."""
    if operation in _ERROR_KEYS:
        _append(dest, _ERROR_KEYS[operation], {"detail": str(err)})
    else:
        _append(dest, "readme_error_unknown",
                {"operation": str(operation), "detail": str(err)})

def PARSEintegritycheck(result, dest=None):
    _append(dest, "readme_integrity_ok" if result else "readme_integrity_fail")
    
    
def dryrunResult(comparedict, dest=None):
    """Write .dryrun.txt in the language currently loaded.
    No journal here on purpose: the file is fully rewritten at every dry run, so
    there is nothing to translate retroactively. A stale language is one dry run
    away from being fixed, and a second mechanism for a throwaway file is not
    worth its weight."""
    folder = _slot(dest)
    folder.mkdir(parents=True, exist_ok=True)

    entries = [_entry("dryrun_would_header")]
    entries.extend(_change_entries(comparedict, "dryrun_would"))

    tmp = folder / (DRYRUN_NAME + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(_render_entry(entry) + "\n")
    path = folder / DRYRUN_NAME
    os.replace(tmp, path)
    return path


# =============================================================================
#==================================== READ ====================================
# =============================================================================

def _as_file(src, filename):
    """Accept either the slot folder or the file itself."""
    path = _slot(src) if src is not None else _slot(None)
    return path / filename if path.is_dir() else path

def readREADME(src=None, notify=lang.notify):
    """Read a slot's rendered README.

    Returns:
        str: the content, or None if there is nothing to show
    """
    path = _as_file(src, RENDER_NAME)
    if not path.exists():
        # Journal présent mais rendu absent (fichier supprimé à la main, dossier
        # copié partiellement) : on le reconstruit plutôt que de crier à l'absence.
        if (path.parent / JOURNAL_NAME).exists():
            rerender(path.parent)
    if not path.exists():
        notify("readme_noexist", path=str(path))
        return None
    if path.stat().st_size == 0:
        notify("readme_empty", path=str(path))
        return None
    return path.read_text(encoding="utf-8", errors="replace")

def readDryRun(src=None, notify=lang.notify):
    """Read a slot's last dry run report.

    Returns:
        str: the content, or None if no dry run was ever written for this slot
    """
    path = _as_file(src, DRYRUN_NAME)
    if not path.exists() or path.stat().st_size == 0:
        notify("dryrun_noexist", fallback=None, path=str(path))
        return None
    return path.read_text(encoding="utf-8", errors="replace")
