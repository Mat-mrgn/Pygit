import os
from datetime import datetime
# definition des fonctions tel que parseREADME ou autre utilitaire à la sauvegarde..
from pathlib import Path
from portabilite import *
from configfile import configfile
cfg=configfile()
import lang

# ---------------------------------ARCHITECTURE OF PYGIT-----------------------------------------
#
#    PYGIT (folder)
#     |
#     |----->current_save (folder)
#     |        |
#     |        |----->Jsontree.json (the tree of the date.zip folder)
#     |        |----->{date}.zip (the current save named by the date it was make at the format dd:mm:yy_hh:mm.zip)
#     |
#     |----->old_save (folder)
#     |         |
#     |         |---->{date}.zip an old save. In the old_save folder a maximum number of save is fixed by the user in this file right above
#     |         |... and beyond until MAX_OLD_SAVE is reached
#     |
#     (Please note that since this part is optional since we work with absolute path and we can put the Py folder (the app) wherever we want)
#     |-------Py (folder)
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
#     |        |---->README.py (we are here)
#     |        |---->portabilite.py
#     |        |---->pygnore.py
#     |        |---->configfile.py
#     |        |---->CLI.py
#     |
#     |------> README.txt (and here... maybe)
#     |------>.pygnore
#     |------>.config-file
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.
COMPUTER = cfg.PC

_APP_DIR=cfg.BASE_DIR # interne
_SAVE_DIR=cfg.DIR # la ou vont les sauvergardes

def readREADME(src=_APP_DIR):
    path = Path(src / "README.txt")
    if not path.exists():
        print(lang.t("readme_noexist"),path=path)
        return 0
    if os.path.getsize(path) == 0:
        print(lang.t("readme_empty"),path=path)
        return 0
    print(lang.t("readme_read"),path=path)
    with open(path, "r") as R:
        for ligne in R:
            print(ligne.strip())


def createREADME(txt, dest=None):
    # utiliser pour créer le readme
    if dest is None:
        dest=Path(cfg.DIR)
    tm = datetime.now().strftime("%d/%m/%Y,%H:%M")
    path = Path(dest / "README.txt")
    f = open(path, "w")
    f.write(f"{tm} : {txt}")
    f.close()


def parseREADME(comparedict, dest=None):
    if dest is None:
        dest=Path(cfg.DIR)
    # print(type(path))
    tm = datetime.now().strftime("%d/%m/%Y,%H:%M")
    path = Path(dest / "README.txt")
    f = open(path, "a")
    f.write(f"{tm} : ")
    for moved in comparedict["Moved"]:
        f.write(f"\t(/) file {moved[0]} was moved to {moved[1]}\n")
    for created in comparedict["Created"]:
        f.write(f"\t(+) file {created[1]} was added from save\n")
    for deleted in comparedict["Deleted"]:
        f.write(f"\t(-) file {deleted[0]} was deleted from save\n")
    for modified in comparedict["Modified"]:
        f.write(f"\t(*) file {modified[0]} was modified from save\n")
    f.close()


def nodiffREADME(dest=None):
    if dest is None:
        dest=Path(cfg.DIR)
    path = Path(dest / "README.txt")
    f = open(path, "a")
    f.write(f"No differencies was found\n")
    f.close()


def errorREADME(err,operation, dest=None):
    
    path = Path(dest / "README.txt")
    f = open(path, "a")
    f.write(f"An error has occured while trying to {operation} {err}\n")
    f.close()

    
def PARSEintegritycheck(result,dest=None):
    if dest is None:
        dest=Path(cfg.DIR)
    path = Path(dest / "README.txt")
    f = open(path, "a")
    if result:
        f.write(f"The integrity check succeeded, no problem detected\n")
    else:
        f.write(f"The integrity check failed, there must be corrupt officer around here...\n")
    f.close()

def dryrunResult(comparedict,dest=None):
    if dest is None:
        dest=Path(cfg.DIR)
    tm = datetime.now().strftime("%d/%m/%Y,%H:%M")
    path = Path(dest / ".dryrun.txt")
    f = open(path, "w")
    f.write(f"{tm} : ")
    for moved in comparedict["Moved"]:
        f.write(f"\t(/) file {moved[0]} would be moved to {moved[1]}\n")
    for created in comparedict["Created"]:
        f.write(f"\t(+) file {created[1]} would be added from save\n")
    for deleted in comparedict["Deleted"]:
        f.write(f"\t(-) file {deleted[0]} would be deleted from save\n")
    for modified in comparedict["Modified"]:
        f.write(f"\t(*) file {modified[0]} would be modified from save\n")
    f.close()
    
def readDryRun(src=str(_SAVE_DIR+"/.dryrun.txt")):
    path=Path(src)
    if path.exists():
        f = open(path,"r")
        print(f.readlines())
        f.close()
    else:
        return 404