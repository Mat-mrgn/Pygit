import json
from pathlib import Path
from portabilite import set_computer


COMPUTER=set_computer()
LANG_DIR=Path(COMPUTER.get_app_root()) /"py"/ "lang"
SUPPORTED = []
#p.stem for p in LANG_DIR.glob("*.json")
for p in LANG_DIR.glob("*json"):
    if p.stem=="pattern":
        pass
    else:
        SUPPORTED.append(p.stem)

_strings={}
_current_lang="en"

# ---------------------------------ARCHITECTURE OF PYGIT-----------------------------------------
#    PYGIT (folder)
#     |
#     |----->current_save (folder)
#     |        |
#     |        |----->Jsontree.json (the tree of the date.zip folder
#     |        |----->{date}.zip (the current save named by the date it was make at the format dd:mm:yy_hh:mm.zip)
#     |
#     |----->old_save (folder)
#     |         |
#     |         |---->{date}.zip an old save. In the old_save folder
#     |         |... and beyond until MAX_OLD_SAVE is reached
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
#     |        |---->lang.py
#     |        |---->save.py
#     |        |---->checksum.py
#     |        |---->pathree.py
#     |        |---->README.py
#     |        |---->portabilite.py
#     |        |---->pygnore.py
#     |        |---->configfile.py
#     |        |---->CLI.py (we are here)
#     |
#     |------> README.txt
#     |------>.pygnore
#     |------>.config-file
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.


def load(lang: str):
    global _strings, _current_lang
    path=LANG_DIR / f"{lang}.json"
    if not path.exists():
        #fallback sur anglais
        lang="en"
        path= LANG_DIR / "en.json"
    with open(path,encoding="utf-8") as f:
        _strings = json.load(f)
    _current_lang = lang
    

def t(key: str,fallback: str = None, **kwargs) ->str: 
    """Traduit une clé, Supporte les variables: t('save_action', src=x, dest=y"""
    text= _strings.get(key,f"[missing : {key}]")
    if text is None:
        return fallback if fallback is not None else f'[Missing: {key}]'
    return text.format(**kwargs) if kwargs else text


def current() -> str:
    return _current_lang