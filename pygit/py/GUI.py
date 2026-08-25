import sys
from pathlib import Path

import webview

from portabilite import set_computer
from configfile import get_cfg
import lang
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
#     |-------Py (folder)
#     |        |
#     |        |-------lang(folder) -> What langage your interface will display his message
#     |        |         |
#     |        |         |---->en.json
#     |        |         |---->fr.json
#     |        |         |---->other_lang.json...
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
#     |        |---->README.py 
#     |        |---->portabilite.py 
#     |        |---->pygnore.py
#     |        |---->configfile.py
#     |        |---->CLI.py
#     |        |---->manifest.py
#     |        |---->GUI_engine.py
#     |        |---->GUI.py (we are here)
#     |
#     |------> README.txt
#     |------>.pygnore
#     |------>.config-file
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.

COMPUTER = set_computer()

# The frontend lives NEXT TO the .py files (PYGIT/py/web), not next to the saves,
# so parents=False. A relative "web/index.html" used to break as soon as the app was
# started from another cwd, and broke again under PyInstaller (sys.frozen).
WEB_DIR = Path(COMPUTER.get_app_root(parents=False)) / "web"
ENTRYPOINT = WEB_DIR / "index.html"


def bootstrap():
    """Prepare the process BEFORE any window exists.

    Order matters: set_mode() has to run first, because is_CLI() is what guards every
    rich.track()/Progress block in pathtree.py and save.py. Without it, a GUI started
    from a terminal still has an attached tty, is_CLI() stays True, and the core would
    quietly draw progress bars into a terminal nobody is watching.

    Returns:
        configfile: the shared configuration object
    """
    COMPUTER.set_mode("gui")
    cfg = get_cfg()
    lang.load(cfg.getLANG())
    return cfg


def main():
    cfg = bootstrap()

    if not ENTRYPOINT.exists():
        # Fail loudly in the terminal: there is no window yet to display anything in,
        # so a silent exit would just look like a crash.
        print(f"[PyGit] Frontend not found: {ENTRYPOINT}", file=sys.stderr)
        return 1

    webview.create_window(
        lang.t("gui_app_name", fallback="PyGit"),
        str(ENTRYPOINT),
        width=1100,
        height=720,
        min_size=(880, 560),
        shadow=True,
    )
    webview.start()
    cfg.write()
    return 0


if __name__ == "__main__":
    sys.exit(main())
    
