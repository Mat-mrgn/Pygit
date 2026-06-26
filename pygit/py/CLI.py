from pathlib import Path

from portabilite import *
from save import *
from pygnore import *
from README import *
from checksum import *
from pathtree import *
from configfile import configfile
import lang
from itertools import zip_longest

import asyncio

import os
from rich.progress import track
from rich.progress import Progress,SpinnerColumn,BarColumn,TextColumn
from rich.columns import Columns
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.tree import Tree
from rich.json import JSON
from rich.live import Live

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory


VERSION = lang.t("VERSION")
ABOUT = lang.t("ABOUT")
PYGNORE_RAPPEL=lang.t("PYGNORE_RAPPEL")

LOGO="""[bold cyan]
 ██████╗ ██╗   ██╗ ██████╗ ██╗████████╗
 ██╔══██╗╚██╗ ██╔╝██╔════╝ ██║╚══██╔══╝
 ██████╔╝ ╚████╔╝ ██║  ███╗██║   ██║   
 ██╔═══╝   ╚██╔╝  ██║   ██║██║   ██║   
 ██║        ██║   ╚██████╔╝██║   ██║   
 ╚═╝        ╚═╝    ╚═════╝ ╚═╝   ╚═╝[/bold cyan]"""
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
#     |-------Py (folder)   -> Note that this is the app and could be anywhere else in the OS as long as you set the BASE_DIR variable to another place
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
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.
def showerror(msg="Unknown"):
    rprint("[red]"+msg+"[/red]")


def showok(msg="Unknown"):
    rprint("[green]"+msg+"[/green]")


def parametrized(dec):
    "decoration des fonctions"
    def layer(*args, **kwargs):
        def repl(f):
            return dec(f, *args, **kwargs)

        return repl
    return layer


# SETTER des variables de base.

def startup():
    global cfg,IGNORE_MNGR
    
    steps = [ ("Loading .configfile...",lambda: configfile()),
              ("Loading lang package ...", lambda:lang.load(cfg.LANG)),
              ("Loading .pygnore... ",lambda: pygnore()),
              ]
    results=[]
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[green]{task.percentage:3.0f}%"),
    ) as progress:
        task=progress.add_task("Démarrage...", total=len(steps))

        for description, action in steps:
            progress.update(task, description=description)
            results.append(action())
            progress.advance(task)

    cfg = results[0]
    
    IGNORE_MNGR = results[2]

FUNCTIONS = {}
HISTORY_PATH=str(COMPUTER.get_app_root()/".pygit_history")

@parametrized
def command(fctn, name):
    FUNCTIONS[name] = fctn


# --------------------------BASIC COMMAND--------------------------
@command("help")
async def displayHelp():
    """L'affichage de la liste des fonctions"""
    table = Table(title=lang.t("help_title"))
    table.add_column(lang.t("help_col_cmd"), justify="left", style="cyan", no_wrap=True)
    table.add_column(lang.t("help_col_info"), justify="left")
    for f in FUNCTIONS.keys():
        d = lang.t(f"doc_{f}",fallback=FUNCTIONS[f].__doc__ or "!")
        table.add_row(f,d)
    rprint(table)


@command("clear")
async def doClear():
    """Efface le contenu du terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')
    rprint(LOGO)
    rprint(lang.t("TAGELINE"))
    rprint(Markdown(lang.t("help_title")))
    rprint(lang.t("main_hint"))


@command("quit")
async def doQuit():
    """Sortie du programme"""
    exit(0)


@command("exit")
async def doExit():
    """Sortie du programme"""
    exit(0)


@command("version")
async def doVersion():
    """La version de l'application"""
    rprint(Markdown(lang.t("VERSION")))


@command("about")
async def doAbout():
    """A propos de l'application"""
    rprint(Markdown(lang.t("ABOUT")))


# --------------------------DIR COMMAND--------------------------
@command("dir")
async def doDir():
    """Le chemin de fichier où sont placés les sauvegardes"""
    global cfg
    rprint(cfg.DIR)


@command("setdir")
async def setdir():
    """Modifie le chemin de fichier où sont placés les sauvegardes"""
    global cfg
    rprint(lang.t("setdir_current",dir=cfg.DIR))
    verif = False
    while not verif:
        new = Path(Prompt.ask(lang.t("setdir_ask")))
        verif = Path.is_absolute(new)
    cfg.setDIR(new)
    rprint(lang.t("setdir_new",dir=cfg.DIR))


@command("wdir")
async def doWorkingdir():
    """Le chemin de fichier du dossier de travail"""
    global cfg
    if cfg.WORKINGDIR is None:
        rprint(lang.t("wdir_none"))
    else:
        rprint(str(cfg.WORKINGDIR))


@command("setwdir")
async def setWorkingdir():
    """Modifie le chemin de fichier du dossier de travail"""
    global cfg
    rprint(lang.t("setwdir_current",wdir=cfg.WORKINGDIR))
    verif = False
    while not verif:
        new = Path(Prompt.ask(
            lang.t("setwdir_ask")))
        verif = Path.is_absolute(new)
    cfg.setWORKINGDIR(new)
    rprint(
        lang.t("setwdir_new",wdir=cfg.WORKINGDIR))

# --------------------------PYGNORE COMMAND--------------------------


@command("psetpath")
async def set_Pygnore_path():
    """Set le path du fichier .pygnore par défaut il est mit à la racine du projet"""
    global IGNORE_MNGR
    current_path = IGNORE_MNGR.get_path()
    new = str(Prompt.ask(
        lang.t("psetpath_ask",path=current_path)))
    if new == "exit":
        rprint(lang.t("psetpath_interrupt"))
        return (200, "User Interuption")
    else:
        new = Path(new)
        try:
            IGNORE_MNGR.set_path(new)
            rprint(lang.t("psetpath_success"))
            return (200, "Success")
        except Exception as e:
            rprint(lang.t("psetpath_error",e=e))
            return (400, "Erreur while changing path")


@command("pgetpath")
async def get_pygnore_path():
    """Donne le path actuel du fichier .pygnore"""
    global IGNORE_MNGR
    try:
        rprint(lang.t("pgetpath_success",path=IGNORE_MNGR.get_path()))
        return (200, "Success")
    except Exception as e:
        rprint(lang.t("pgetpath_error",e=e))


@command("paddexclude")
async def pygnore_add_exculde():
    """Ajoute une type à la liste des excludes"""
    rprint(PYGNORE_RAPPEL)
    global IGNORE_MNGR
    typ = ""
    while not typ in ('fi', 'fo'):
        typ = str(Prompt.ask(lang.t("paddexclude_ask_type")))
    pattern = str(Prompt.ask(lang.t("paddexclude_ask_pattern")))
    try:
        IGNORE_MNGR.add_exclude(typ, pattern)
        rprint(lang.t("paddexclude_success"))
    except Exception as e:
        rprint(lang.t("paddexclude_error",e=e))


@command("paddinclude")
async def pygnore_add_include():
    """Ajoute une type à la liste des includes"""
    global IGNORE_MNGR
    typ = ""
    rprint(PYGNORE_RAPPEL)
    while not typ in ('fi', 'fo'):
        typ = str(Prompt.ask(lang.t("paddinclude_ask_type")))
    pattern = str(Prompt.ask(lang.t("paddinclude_ask_pattern")))
    try:
        IGNORE_MNGR.add_include(typ, pattern)
        rprint(lang.t("paddinclude_success"))
    except Exception as e:
        rprint(lang.t("paddinclude_error"),e=e)


@command("pdelexclude")
async def pygnore_del_exclude():
    """Supprime une typo de la liste des excludes """
    global IGNORE_MNGR
    rprint(PYGNORE_RAPPEL)
    typ = str(Prompt.ask(lang.t("pdelexclude_ask_type")))
    for exc in IGNORE_MNGR.exc:
        if exc[0] == typ:
            rprint(exc)
    pattern = str(Prompt.ask(lang.t("pdelexclude_ask_pattern")))
    for exc in IGNORE_MNGR.exc:
        if exc[0] == typ and exc[1] == pattern:
            try:
                IGNORE_MNGR.del_exclude(exc[0], exc[1])
                rprint(lang.t("pdelexclude_success"))
                return (200, "Success")
            except Exception as e:
                rprint(lang.t("pdelexclude_error"),e=e)
                return (400, "Error")


@command("pdelinclude")
async def pygnore_del_include():
    """Supprime une type de la liste des includes"""
    global IGNORE_MNGR
    rprint(PYGNORE_RAPPEL)
    typ = str(Prompt.ask(lang.t("pdelinclude_ask_type")))
    for inc in IGNORE_MNGR.inc:
        if inc[0] == typ:
            rprint(inc)
    pattern = str(Prompt.ask(lang.t("pdelinclude_ask_pattern")))
    for inc in IGNORE_MNGR.inc:
        if inc[0] == typ and inc[1] == pattern:
            try:
                IGNORE_MNGR.del_include(inc[0], inc[1])
                rprint(lang.t("pdelinclude_success"))
                return (200, "Success")
            except Exception as e:
                rprint(lang.t("pdelinclude_error"),e=e)
                return (400, "Error")


@command("pshowall")
async def pygnore_showall():
    """Affiche les listes d'include et d'exclude"""
    global IGNORE_MNGR
    rprint(PYGNORE_RAPPEL)
    inc = IGNORE_MNGR.inc
    exc = IGNORE_MNGR.exc
    rprint(lang.t("pshowall_inc_header"))
    for i in inc:
        rprint(i)
    rprint(lang.t("pshowall_exc_header"))
    for e in exc:
        rprint(e)


@command("pshowinc")
async def pygnore_showinc():
    """Affiche la liste d'include"""
    global IGNORE_MNGR
    rprint(PYGNORE_RAPPEL)
    inc = IGNORE_MNGR.inc
    rprint(lang.t("pshowall_inc_header"))
    for i in inc:
        rprint(i)


@command("pshowexc")
async def pygnore_showexc():
    """Affiche la liste d'exclude"""
    global IGNORE_MNGR
    rprint(PYGNORE_RAPPEL)
    exc = IGNORE_MNGR.exc
    rprint(lang.t("pshowall_exc_header"))
    for e in exc:
        rprint(e)


@command("pneedtoinclude")
async def pygnore_needtoinclude():
    """Permet de tester si un fichier serait inclut ou non"""
    global IGNORE_MNGR
    rprint(PYGNORE_RAPPEL)
    is_dir = str(Confirm.ask(lang.t("pneedtoinclude_ask_isdir")))
    filename = str(Prompt.ask(lang.t("pneedtoinclude_ask_name")))
    try:
        r = IGNORE_MNGR.needtoInclude(filename, is_dir=is_dir)
        if r:
            rprint(lang.t("pneedtoinclude_yes"))
        else:
            rprint(lang.t("pneedtoinclude_no"))
    except Exception as e:
        rprint(lang.t("pneedtoinclude_error"),e=e)

# --------------------------SAVE COMMAND--------------------------

@command("save")
async def cli_save(force: bool=False):
    """Réalise une sauvegarde du {cfg.WORKINGDIR}"""
    src=cfg.getWORKINGDIR()
    dest=cfg.getDIR()
    
    if not src or dest=="None" :
        rprint(lang.t("save_missing_config"))
        return
    rprint(lang.t("save_action",src=src,dest=dest))
    if not force:
        confirm=Confirm.ask(lang.t("save_confirm"))
        if not confirm:
            rprint(lang.t("save_cancelled"))
            return
    result,status=save(dest,src)
    
    if result==200:
        rprint(lang.t("save_success"))
    else:
        rprint(lang.t("save_error",code=result,status=status))


@command("dryrun")
async def cli_dryrun(verbose: bool=False):
    """Vérifie et donne la liste des modifications entre la sauvegarde courante et le {cfg.WORKINGDIR}"""
    src=cfg.getWORKINGDIR()
    dest=cfg.getDIR()
    if not src or not dest:
        rprint(lang.t("dryrun_missing_config"))
        return
    result,statusdict=dryrun(src,dest_path=dest,verbose=verbose)
    if result==200:
        rprint(lang.t("dryrun_success"))
        if isinstance(statusdict,dict):
            total_diff=sum(len(statusdict[k]) for k in ["Moved",'Deleted','Created','Modified'])
            if total_diff==0:
                rprint(lang.t("dryrun_no_diff",src=src,dest=dest))
            else:
                rprint(lang.t("dryrun_diff_found"))
                dryrunResult(statusdict,dest=dest)
                readDryRun(str(Path(dest)/".dryrun.txt"))
    else:
        rprint(lang.t("dryrun_error",code=result,status=statusdict))


@command("restore")
async def cli_restore():
    """Restaure une sauvegarde à partir du {cfg.BASE_DIR}, ou d'anciennes sauvegardes"""
    destpath=str(Prompt.ask(lang.t("restore_ask_dest")))
    if destpath is None or destpath=="":
        destpath=cfg.getWORKINGDIR()
    else:
        destpath=cfg.get_abs(destpath)
    curr=not Confirm.ask(lang.t("restore_ask_from_current"))
    code,msg=restore(destpath,fromolder=curr)
    if code==417:
        rprint(lang.t("restore_integrity_fail"))
        categories = {
                "Created": {"color": "green", "sign": "(+)", "label": "Files Created"},
                "Modified": {"color": "yellow", "sign": "(*)", "label": "Files Modified"},
                "Moved": {"color": "blue", "sign": "(/)", "label": "Files Moved"},
                "Deleted": {"color": "red", "sign": "(-)", "label": "Files Deleted"}
            }
        if len(msg["Created"]) > 0:
                rprint(lang.t("restore_created_header"))
                for created_file in msg['Created']:
                    csign = categories["Created"]["sign"]
                    rprint(f"\t {csign} {created_file[1]}")
        else:
                rprint(lang.t("restore_created_none"))

        if len(msg["Deleted"]) > 0:
                rprint(lang.t("restore_deleted_header"))
                for deleted_file in msg['Deleted']:
                    dsign = categories["Deleted"]["sign"]
                    rprint(f"\t {dsign} {deleted_file[0]}")
        else:
                rprint(lang.t("restore_deleted_none"))

        if len(msg["Modified"]) > 0:
                rprint(lang.t("restore_modified_header"))
                for modified_file in msg['Modified']:
                    msign = categories["Modified"]["sign"]
                    rprint(f"\t {msign} {modified_file[1]}")
        else:
                rprint(lang.t("restore_modified_none"))

        if len(msg["Moved"]) > 0:
                rprint(lang.t("restore_moved_header"))
                for moved_file in msg['Moved']:
                    mmsign = categories["Moved"]["sign"]
                    rprint(f"\t {mmsign} {moved_file[1]}")
        else:
            rprint(lang.t("restore_moved_none"))
    else:
        rprint(msg)
    
    
# --------------------------CHECKSUM COMMAND--------------------------
@command("checkfiles")
async def CLI_checksumFiles():
    """Check if the content of f1 == the content of f2 using the hashcode of the file
    It will not enter and read the file but compute it's hash so it will not say where it is """
    file_1=cfg.get_abs(Prompt.ask(lang.t("checkfiles_ask1")))
    file_2=cfg.get_abs(Prompt.ask(lang.t("checkfiles_ask2")))
    if file_1 == 404 or file_2 == 404:
        return (404,lang.t("checkfiles_error"))
    res=checksumfiles(file_1,file_2)
    if res==False:
        rprint(lang.t("checkfiles_nok"))
        return(200,lang.t("checkfiles_nok"))
    else:
        rprint(lang.t("checkfiles_ok"))
        return(200,lang.t("checkfiles_ok"))
    
@command("checkfolder")
async def CLI_checkfolder():
    """Check if the content of the folder 1 == the content of the folder 2 recursively (by watching all the child)
    folder 1 is by default set to dir and folder 2 to wdir"""
    f1=Prompt.ask(lang.t("checkfolder_ask1"),default=None)
    if f1 is None:
        f1=cfg.DIR
    f2=Prompt.ask(lang.t("checkfolder_ask2"),default=None)
    if f2 is None:
        f2=cfg.WORKINGDIR
    t1=get_unified_tree(f1)
    t2=get_unified_tree(f2)
    code,diff=comparefolder(t1,t2)
    if code:
        rprint(lang.t("checkfolder_nodiff"))
        return (200,lang.t("checkfolder_nodiff"))
    else:
        table=Table(title=lang.t("checkfolder_diff_title"))
        table.add_column(lang.t("checkfolder_col_modified"),justify='left',no_wrap=True)
        table.add_column(lang.t("checkfolder_col_created"),justify='left',no_wrap=True)
        table.add_column(lang.t("checkfolder_col_deleted"),justify='left',no_wrap=True)
        table.add_column(lang.t("checkfolder_col_moved"),justify='left',no_wrap=True)
        
        modified = [f"{m[0]}" for m in diff["Modified"]]
        created  = [f"{c[1]}" for c in diff["Created"]]
        deleted  = [f"{d[0]}" for d in diff["Deleted"]]
        moved    = [f"{mv[0]} -> {mv[1]}" for mv in diff["Moved"]]
        for mod,cre,dele,mov in zip_longest(modified,created,deleted,moved,fillvalue=""):
            table.add_row(mod,cre,dele,mov)
        rprint(table)
                
        return(200,lang.t("checkfolder_diff",dico=diff))
    

# --------------------------PATHTREE COMMAND--------------------------
@command("gettree")
async def CLI_gettree():
    """Détermine si le fichier est un zip ou pas et retourne son arbre avec le nom, le timestamp, la taille, 
    son chemin et son hash pour chaque fichier/dossier présent dans le dossier en faisant attention au .pygnore"""
    v=Confirm.ask(lang.t("gettree_verbose"))
    folder=Prompt.ask(lang.t("gettree_path"),default=None)
    if folder is None:
        folder=cfg.WORKINGDIR
    folder=cfg.get_abs(folder)
    tree=get_unified_tree(folder,verbose=v)
    rprint(tree)
# --------------------------README COMMAND--------------------------
@command("readreadme")
async def CLI_readreadme():
    """Read the readme.txt files"""
    readREADME()
    
@command("readdryrun")
async def CLI_readyrun():
    """Read the dryrun.txt files"""
    readDryRun()
# --------------------------GENERAL COMMAND--------------------------

@command("setlang")
async def set_lang():
    rprint(lang.t("setlang_current",lang=cfg.LANG))
    table=Table(title=lang.t("setlang_title"))
    table.add_column(lang.t("setlang_col_alias"),justify="left",style="cyan",no_wrap=True)
    table.add_column(lang.t("setlang_col_lang"),justify="left")
    for l in lang.SUPPORTED:
        d=lang.t(f"lang_{l}")
        table.add_row(l,d)
    rprint(table)
    
    
    choosen_lang=Prompt.ask(lang.t("setlang_ask"))
    if choosen_lang in lang.SUPPORTED:
        cfg.LANG=choosen_lang
        lang.load(cfg.LANG)
        rprint(lang.t("setlang_success",lang=cfg.LANG))
    else:
        rprint(lang.t("setlang_error"))
        cfg.LANG="en"
        lang.load(cfg.LANG)
        
@command("getlang")
async def get_lang():
    rprint(lang.t("getlang_current",lang=cfg.LANG))



async def main():
    rprint(LOGO)
    rprint(lang.t("TAGELINE"))
    rprint(Markdown(lang.t("main_title")))
    rprint(lang.t("main_hint"))

    session = PromptSession(history=FileHistory(HISTORY_PATH))
    while True:
        try:
            user_imput = Prompt.ask("[bold cyan]pygit>[/bold cyan]", default="help",show_choices=False, show_default=False).strip().lower()
            if not user_imput:
                continue
            
            parts = user_imput.split()
            cmd=parts[0]
            if cmd in FUNCTIONS:
                raw_args=parts[1:]
                kwargs={}
                for arg in raw_args:
                    if arg.startswith("--"):
                        key= arg[2:].replace("-","_")
                        kwargs[key]=True
                await FUNCTIONS[cmd](**kwargs)
            else:
                showerror(lang.t("main_unknown_cmd",cmd=cmd))
        except KeyboardInterrupt:
            rprint(lang.t("main_interrupt"))
        except SystemExit:
            break


if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    startup()
    asyncio.run(main())


# ---------------------------------END OF ARCHITECTURE-----------------------------------------

# This CLI is designed to be highly personalisable and extensible. Here under a list of all the commands that are natively implemented

# --------------------------BASIC COMMAND--------------------------
# `help` : Show the list of disponible functions and their description
# `quit` : Leave the program, the command `exit` is the same
# `version` : Show the versions of the application.
# `about` : Show the information about the application.

# --------------------------DIR COMMAND--------------------------
# `dir` : show the path where the saves are stocked
# `wdir` : Show the setted workplace
# `setdir` : Modify the path of the future save folder
# `setwdir` : Modify the path of the workplace

# --------------------------PYGNORE COMMAND--------------------------
# `psetpath` : Set the path of the .pygnore folder by default, he's at the root of the project
# `pgetpath` :Give the actual .pygnore path
# `paddexclude` : Add a typo to the exclude list format : < {`fi` or `fo`} {pattern} see .pygnore default for some exclude patterns
# `paddinclude` : Add a typo to the include list format: > {`fi` or `fo`} {pattern} see .pygnore default for some include patterns
# `pdelexclude` : Delete a typo to the  exclude list 
# `pdelinclude` : Delete a typo to the include list include
# `pshowall` : Show the list of the include and the exclude
# `pshowinc` : Show the include list
# `pshowexc` : Show the exclude list
# `pneedtoinclude` : Try to know if you files would be included or not (does not look about the `fo` pattern)

# --------------------------SAVE COMMAND--------------------------
# `save` : Do a save of  {cfg.WORKINGDIR}
# `dryrun` : Try wich files would be modified depict the actual save
# `restore` : Restore and actual save

# --------------------------CHECKSUM COMMAND--------------------------
# `checkfiles` : check if the content of the file1 is the same as the content of file2 with calculating his hash
# `checkfolder` : check if the content of the folder1 is the same as the content of folder2 with looking at the child and etc.

# --------------------------PATHTREE COMMAND--------------------------
# `gettree` : use the command get_unified_tree to get the tree of a folder it could be either a zipfile or a folder

# --------------------------README COMMAND--------------------------
# `readreadme`: to reread the readme file
# `readdryrun`: to reread the precedent result of the dryrun


# --------------------------GENERAL COMMAND--------------------------
# `setlang` : Change the langage
# `getlang` : Get the current langage


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
