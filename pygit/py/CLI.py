from pathlib import Path

from portabilite import *
from save import *
from pygnore import *
from README import *
from checksum import *
from pathtree import *
from configfile import get_cfg
from manifest import manifest
import lang
from itertools import zip_longest

import asyncio

import os
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich import print as rprint
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory


VERSION = lang.t("VERSION")
ABOUT = lang.t("ABOUT")
PYGNORE_RAPPEL = lang.t("PYGNORE_RAPPEL")

LOGO = """[bold cyan]
 ██████╗ ██╗   ██╗ ██████╗ ██╗████████╗
 ██╔══██╗╚██╗ ██╔╝██╔════╝ ██║╚══██╔══╝
 ██████╔╝ ╚████╔╝ ██║  ███╗██║   ██║   
 ██╔═══╝   ╚██╔╝  ██║   ██║██║   ██║   
 ██║        ██║   ╚██████╔╝██║   ██║   
 ╚═╝        ╚═╝    ╚═════╝ ╚═╝   ╚═╝[/bold cyan]"""

# ---------------------------------ARCHITECTURE OF PYGIT-----------------------------------------
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
#     |        |---->README.py
#     |        |---->portabilite.py
#     |        |---->pygnore.py
#     |        |---->configfile.py
#     |        |---->CLI.py (we are here)
#     |        |---->manifest.py
#     |        |---->GUI_engine.py
#     |        |---->GUI.py
#     |
#     |------> README.txt
#     |------>.pygnore
#     |------>.config-file
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
    global cfg, IGNORE_MNGR

    steps = [("Loading .configfile...", lambda: get_cfg()),
             ("Loading lang package ...", lambda: lang.load(cfg.LANG)),
             ("Loading .pygnore... ", lambda: get_ignore()),
             ]
    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=30),
        TextColumn("[green]{task.percentage:3.0f}%"),
    ) as progress:
        task = progress.add_task("Démarrage...", total=len(steps))

        for description, action in steps:
            progress.update(task, description=description)
            results.append(action())
            progress.advance(task)

    cfg = results[0]

    IGNORE_MNGR = results[2]


FUNCTIONS = {}
HISTORY_PATH = str(COMPUTER.get_app_root()/".pygit_history")


@parametrized
def command(fctn, name):
    FUNCTIONS[name] = fctn


# --------------------------BASIC COMMAND--------------------------
@command("help")
async def displayHelp():
    """Display the list of the function"""
    table = Table(title=lang.t("help_title"))
    table.add_column(lang.t("help_col_cmd"), justify="left",
                     style="cyan", no_wrap=True)
    table.add_column(lang.t("help_col_info"), justify="left")
    for f in FUNCTIONS.keys():
        d = lang.t(f"doc_{f}", fallback=FUNCTIONS[f].__doc__ or "!")
        table.add_row(f, d)
    rprint(table)


@command("clear")
async def doClear():
    """Clear the terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')
    rprint(LOGO)
    rprint(lang.t("TAGLINE"))
    rprint(Markdown(lang.t("help_title")))
    rprint(lang.t("main_hint"))


@command("quit")
async def doQuit():
    """Exit the program"""
    cfg.write()
    exit(0)


@command("exit")
async def doExit():
    """Exit the program"""
    cfg.write()
    exit(0)


@command("version")
async def doVersion():
    """App version"""
    rprint(Markdown(lang.t("VERSION")))


@command("about")
async def doAbout():
    """About the app"""
    rprint(Markdown(lang.t("ABOUT")))


# --------------------------DIR COMMAND--------------------------
@command("dir")
async def doDir():
    """The path where the saves are located"""
    global cfg
    rprint(cfg.DIR)


@command("setdir")
async def setdir():
    """Set the path were the saves will be located"""
    global cfg
    rprint(lang.t("setdir_current", dir=cfg.DIR))
    verif = False
    while not verif:
        new = Path(Prompt.ask(lang.t("setdir_ask")))
        verif = Path.is_absolute(new)
    if not cfg.setDIR(new):
        rprint(lang.t("setdir_error", dir=new,
               fallback="[red]{dir} does not exist, the save folder is unchanged.[/red]"))
        return
    rprint(lang.t("setdir_new", dir=cfg.DIR))


@command("wdir")
async def doWorkingdir():
    """The path of the working dir"""
    global cfg
    if cfg.WORKINGDIR is None:
        rprint(lang.t("wdir_none"))
    else:
        rprint(str(cfg.WORKINGDIR))


@command("setwdir")
async def setWorkingdir():
    """Set the working dir file path"""
    global cfg
    rprint(lang.t("setwdir_current", wdir=cfg.WORKINGDIR))
    verif = False
    while not verif:
        new = Path(Prompt.ask(
            lang.t("setwdir_ask")))
        verif = Path.is_absolute(new)
    if not cfg.setWORKINGDIR(new):
        rprint(lang.t("setwdire_error", wdir=new,
               fallback="[red]{wdir} does not exist, the working dir is unchanged.[/red]"))
        return
    rprint(lang.t("setwdir_new", wdir=cfg.WORKINGDIR))

# --------------------------PYGNORE COMMAND--------------------------


@command("psetpath")
async def set_Pygnore_path():
    """Set the path of .pygnore by default he's set to the root of the app"""
    global IGNORE_MNGR
    current_path = IGNORE_MNGR.get_path()
    new = str(Prompt.ask(
        lang.t("psetpath_ask", path=current_path)))
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
            rprint(lang.t("psetpath_error", e=e))
            return (400, "Erreur while changing path")


@command("pgetpath")
async def get_pygnore_path():
    """Give the path of the .pygnore"""
    global IGNORE_MNGR
    try:
        rprint(lang.t("pgetpath_success", path=IGNORE_MNGR.get_path()))
        return (200, "Success")
    except Exception as e:
        rprint(lang.t("pgetpath_error", e=e))


@command("paddexclude")
async def pygnore_add_exculde():
    """Add a typo to the excludes list"""
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
        rprint(lang.t("paddexclude_error", e=e))


@command("paddinclude")
async def pygnore_add_include():
    """Add a typo to the include list"""
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
        rprint(lang.t("paddinclude_error", e=e))


@command("pdelexclude")
async def pygnore_del_exclude():
    """Delete a typo of the exclude list """
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
                rprint(lang.t("pdelexclude_error", e=e))
                return (400, "Error")


@command("pdelinclude")
async def pygnore_del_include():
    """Delete a typo of the include list"""
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
                rprint(lang.t("pdelinclude_error", e=e))
                return (400, "Error")


@command("pshowall")
async def pygnore_showall():
    """Display the include and exclude list"""
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
    """Display the include list"""
    global IGNORE_MNGR
    rprint(PYGNORE_RAPPEL)
    inc = IGNORE_MNGR.inc
    rprint(lang.t("pshowall_inc_header"))
    for i in inc:
        rprint(i)


@command("pshowexc")
async def pygnore_showexc():
    """Display the exclude list"""
    global IGNORE_MNGR
    rprint(PYGNORE_RAPPEL)
    exc = IGNORE_MNGR.exc
    rprint(lang.t("pshowall_exc_header"))
    for e in exc:
        rprint(e)


@command("pneedtoinclude")
async def pygnore_needtoinclude():
    """Test if a file will be included or no """
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
        rprint(lang.t("pneedtoinclude_error", e=e))

# --------------------------SAVE COMMAND--------------------------


@command("save")
async def cli_save(force: bool = False):
    """Save the {cfg.WORKINGDIR}"""
    src = cfg.getWORKINGDIR()
    dest = cfg.getDIR()

    if not src or dest == "None":
        rprint(lang.t("save_missing_config"))
        return
    abs_src = cfg.get_abs(src)
    if abs_src == 404:
        rprint(lang.t("save_missing_config"))
        return
    mnf = manifest(cfg)
    resolved_dest = mnf.resolve_save_slot(abs_src)
    rprint(lang.t("save_action", src=src, dest=resolved_dest))
    if not force:
        confirm = Confirm.ask(lang.t("save_confirm"))
        if not confirm:
            rprint(lang.t("save_cancelled"))
            return
    result, status = save(resolved_dest, src)

    if result == 200:
        rprint(lang.t("save_success"))
    else:
        rprint(lang.t("save_error", code=result, status=status))


@command("dryrun")
async def cli_dryrun(verbose: bool = False):
    """Check and give the list of the change of the save and the {cfg.WORKINGDIR}"""
    src = cfg.getWORKINGDIR()
    dest = cfg.getDIR()
    if not src or not dest:
        rprint(lang.t("dryrun_missing_config"))
        return
    abs_src = cfg.get_abs(src)
    if abs_src == 404:
        rprint(lang.t("dryrun_missing_config"))
        return
    mnf = manifest(cfg)
    save_dir = mnf.resolve_existing_slot(abs_src)
    if save_dir is None:
        rprint(lang.t("manifest_dryrun_no_save",
               fallback="[yellow]No known save found for this working directory yet. Nothing to compare.[/yellow]"))
        return
    result, statusdict = dryrun(src, dest_path=save_dir, verbose=verbose)
    if result == 200:
        rprint(lang.t("dryrun_success"))
        if isinstance(statusdict, dict):
            total_diff = sum(len(statusdict[k]) for k in [
                             "Moved", 'Deleted', 'Created', 'Modified'])
            if total_diff == 0:
                rprint(lang.t("dryrun_no_diff", src=src, dest=save_dir))
            else:
                rprint(lang.t("dryrun_diff_found"))
                dryrunResult(statusdict, dest=save_dir)
                txt = readDryRun(save_dir)
                if txt:
                    rprint(txt)
    else:
        rprint(lang.t("dryrun_error", code=result, status=statusdict))


@command("restore")
async def cli_restore():
    """Restore a save based of the {cfg.BASE_DIR}, or older save"""
    mnf = manifest(cfg)
    save_dir = mnf.resolve_restore_target()
    if save_dir is None:
        return
    destpath = str(Prompt.ask(lang.t("restore_ask_dest")))
    if destpath is None or destpath == "":
        destpath = cfg.getWORKINGDIR()
    else:
        destpath = cfg.get_abs(destpath)
    curr = not Confirm.ask(lang.t("restore_ask_from_current"))
    code, msg = restore(destpath, save_dir=save_dir, fromolder=curr)
    if code == 417:
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


# --------------------------MANIFEST COMMAND--------------------------

def _print_sources_table(sources):
    """Shared table display for listsaves/unlinksave, {path: slot} -> a Slot/Path table."""
    table = Table(title=lang.t("listsaves_title",
                  fallback="Known save sources"))
    table.add_column(lang.t("listsaves_col_slot", fallback="Slot"),
                     justify="left", style="cyan", no_wrap=True)
    table.add_column(lang.t("listsaves_col_path",
                     fallback="Path"), justify="left")
    for path, slot in sources.items():
        table.add_row(slot, path)
    rprint(table)


@command("setsimthreshold")
async def cli_setsimthreshold():
    """Change the similarity threshold used to detect a moved save source"""
    rprint(lang.t("setsimthreshold_current", threshold=cfg.get_SIMThreshold(),
                  fallback=f"Current similarity threshold: {cfg.get_SIMThreshold()}%"))
    raw = Prompt.ask(lang.t("setsimthreshold_ask",
                     fallback="Enter the new threshold (0-100)"))
    try:
        new_value = int(raw)
        if not 0 <= new_value <= 100:
            raise ValueError
    except ValueError:
        rprint(lang.t("setsimthreshold_error",
                      fallback="[red]Invalid value, please enter an integer between 0 and 100.[/red]"))
        return
    cfg.setSIMThreshold(new_value)
    rprint(lang.t("setsimthreshold_success", threshold=new_value,
                  fallback=f"[green]Similarity threshold updated to: {new_value}%[/green]"))


@command("getsimthreshold")
async def cli_getsimthreshold():
    """Show the current similarity threshold used to detect a moved save source"""
    rprint(lang.t("getsimthreshold_current", threshold=cfg.get_SIMThreshold(),
                  fallback=f"Current similarity threshold: {cfg.get_SIMThreshold()}%"))


@command("listsaves")
async def cli_listsaves():
    """List every known save source and the save slot it is linked to"""
    mnf = manifest(cfg)
    sources = mnf.list_sources()
    if not sources:
        rprint(lang.t("listsaves_none",
               fallback="[yellow]No known save source yet.[/yellow]"))
        return
    _print_sources_table(sources)


@command("unlinksave")
async def cli_unlinksave():
    """Unlink a known path from its save slot (e.g. to undo a wrong similarity match).
    This never deletes any backup file, only the tracking link in the manifest."""
    mnf = manifest(cfg)
    sources = mnf.list_sources()
    if not sources:
        rprint(lang.t("listsaves_none",
               fallback="[yellow]No known save source yet.[/yellow]"))
        return
    _print_sources_table(sources)
    choice = str(Prompt.ask(lang.t("unlinksave_ask",
                 fallback="Enter the exact path to unlink, or 'exit'")))
    if choice.lower() == "exit":
        return
    if choice not in sources:
        rprint(lang.t("unlinksave_invalid",
               fallback="[red]Unknown path.[/red]"))
        return
    confirm = Confirm.ask(lang.t("unlinksave_confirm", path=choice, slot=sources[choice],
                                 fallback=f"Unlink {choice} from {sources[choice]}? This won't delete any backup file."))
    if not confirm:
        rprint(lang.t("unlinksave_cancelled",
               fallback="[yellow]Cancelled.[/yellow]"))
        return
    slot = mnf.unregister(choice)
    rprint(lang.t("unlinksave_success", path=choice, slot=slot,
                  fallback=f"[green]{choice} has been unlinked from {slot}.[/green]"))


# --------------------------CHECKSUM COMMAND--------------------------
@command("checkfiles")
async def CLI_checksumFiles():
    """Check if the content of f1 == the content of f2 using the hashcode of the file
    It will not enter and read the file but compute it's hash so it will not say where it is """
    file_1 = cfg.get_abs(Prompt.ask(lang.t("checkfiles_ask1")))
    file_2 = cfg.get_abs(Prompt.ask(lang.t("checkfiles_ask2")))
    if file_1 == 404 or file_2 == 404:
        return (404, lang.t("checkfiles_error"))
    res = checksumfiles(file_1, file_2)
    if res == False:
        rprint(lang.t("checkfiles_nok"))
        return (200, lang.t("checkfiles_nok"))
    else:
        rprint(lang.t("checkfiles_ok"))
        return (200, lang.t("checkfiles_ok"))


@command("checkfolder")
async def CLI_checkfolder():
    """Check if the content of the folder 1 == the content of the folder 2 recursively (by watching all the child)
    folder 1 is by default set to dir and folder 2 to wdir"""
    f1 = Prompt.ask(lang.t("checkfolder_ask1"), default=None)
    if f1 is None:
        f1 = cfg.DIR
    f2 = Prompt.ask(lang.t("checkfolder_ask2"), default=None)
    if f2 is None:
        f2 = cfg.WORKINGDIR
    t1 = get_unified_tree(f1)
    t2 = get_unified_tree(f2)
    code, diff = comparefolder(t1, t2)
    if code:
        rprint(lang.t("checkfolder_nodiff"))
        return (200, lang.t("checkfolder_nodiff"))
    else:
        table = Table(title=lang.t("checkfolder_diff_title"))
        table.add_column(lang.t("checkfolder_col_modified"),
                         justify='left', no_wrap=True)
        table.add_column(lang.t("checkfolder_col_created"),
                         justify='left', no_wrap=True)
        table.add_column(lang.t("checkfolder_col_deleted"),
                         justify='left', no_wrap=True)
        table.add_column(lang.t("checkfolder_col_moved"),
                         justify='left', no_wrap=True)

        modified = [f"{m[0]}" for m in diff["Modified"]]
        created = [f"{c[1]}" for c in diff["Created"]]
        deleted = [f"{d[0]}" for d in diff["Deleted"]]
        moved = [f"{mv[0]} -> {mv[1]}" for mv in diff["Moved"]]
        for mod, cre, dele, mov in zip_longest(modified, created, deleted, moved, fillvalue=""):
            table.add_row(mod, cre, dele, mov)
        rprint(table)

        return (200, lang.t("checkfolder_diff", dico=diff))


# --------------------------PATHTREE COMMAND--------------------------
@command("gettree")
async def CLI_gettree():
    """Determineif the file is a zip or not and return his timestamp, his taille, 
    the path and the hash of each fichier/dossier present in the folder with taking note of the .pygnore"""
    v = Confirm.ask(lang.t("gettree_verbose"))
    folder = Prompt.ask(lang.t("gettree_path"), default=None)
    if folder is None:
        folder = cfg.WORKINGDIR
    folder = cfg.get_abs(folder)
    tree = get_unified_tree(folder, verbose=v)
    rprint(tree)
# --------------------------README COMMAND--------------------------


@command("readreadme")
async def CLI_readreadme():
    """Read the readme.txt files"""
    txt = readREADME()
    if txt:
        rprint(txt)


@command("readdryrun")
async def CLI_readyrun():
    """Read the dryrun.txt files"""
    txt = readDryRun()
    if txt:
        rprint(txt)
# --------------------------GENERAL COMMAND--------------------------
def apply_lang(code):
    """Load a language, then re-render every known slot's README.txt in it.

    Both branches of setlang end here, the fallback included: an unsupported code
    drops back to English, and that drop has to reach the README files too, or the
    history stays in a language nobody asked for.
    """
    lang.load(code)
    mnf = manifest(cfg)
    done = 0
    for slot in set(mnf.list_sources().values()):
        if rerender(Path(cfg.DIR) / "saves" / slot) is not None:
            done += 1
    return done

@command("setlang")
async def set_lang():
    rprint(lang.t("setlang_current", lang=cfg.LANG))
    table = Table(title=lang.t("setlang_title"))
    table.add_column(lang.t("setlang_col_alias"),
                     justify="left", style="cyan", no_wrap=True)
    table.add_column(lang.t("setlang_col_lang"), justify="left")
    for l in lang.SUPPORTED:
        d = lang.t(f"lang_{l}")
        table.add_row(l, d)
    rprint(table)

    choosen_lang = Prompt.ask(lang.t("setlang_ask"))
    if choosen_lang in lang.SUPPORTED:
        cfg.setLANG(choosen_lang)
        apply_lang(cfg.LANG)
        rprint(lang.t("setlang_success", lang=cfg.LANG))
    else:
        rprint(lang.t("setlang_error"))
        cfg.setLANG("en")
        apply_lang(cfg.LANG)

@command("getlang")
async def get_lang():
    rprint(lang.t("getlang_current", lang=cfg.LANG))
    
@command("applylang")
async def cli_applylang():
    """Re-render every known README.txt in the current language"""
    done = apply_lang(cfg.getLANG())
    if done:
        rprint(lang.t("applylang_success", lang=cfg.getLANG(), count=done))
    else:
        rprint(lang.t("applylang_none"))

# --------------------------CONFIG COMMAND--------------------------
@command("setmaxold")
async def set_maxold():
    rprint(lang.t("getmos",fallback="The current MAX_OLD_SAVE parameter is fixed at :{mos}",mos=cfg.getMOS()))
    raw = Prompt.ask(lang.t("setMOS"), default=str(cfg.getMOS()))
    if not cfg.setMOS(raw):
        rprint(lang.t("setmos_error",fallback="[red]Invalid value, please enter an integer greater than 0.[/red]"))
        return
    rprint(lang.t("setmos",fallback="The MAX_OLD_SAVE parameter has been fixed at :{mos}",mos=cfg.getMOS()))

@command("getmaxold")
async def get_maxold():
    rprint(lang.t("getmos",fallback="The current MAX_OLD_SAVE parameter is fixed at :{mos}",mos=cfg.getMOS()))

@command("checkopspeed")
async def checkopspeed():
    cfg.setOPTspeed(cfg.PC.set_optimal_speed())
    rprint(lang.t("checkopspeed",fallback="Your optimal speed has been recalculated to :{speed}",speed=cfg.get_OPT_speed()))

@command("getopspeed")
async def getopspeed():
    rprint(lang.t("getopspeed",fallback="Your Optimal Speed is :{speed}",speed=cfg.get_OPT_speed()))

@command("checkcomputer")
async def checkcomputer():
    cfg.PC = set_computer()
    rprint(lang.t("setcomputer",fallback="Your OS has been recalculated to :{comp}",comp=cfg.PC.get_os()))

@command("getcomputer")
async def getcomputer():
    rprint(lang.t("getcomputer",fallback="Your OS is :{comp}",comp=cfg.PC.get_os()))



async def main():
    rprint(LOGO)
    rprint(lang.t("TAGLINE"))
    rprint(Markdown(lang.t("main_title")))
    rprint(lang.t("main_hint"))

    session = PromptSession(history=FileHistory(HISTORY_PATH))
    while True:
        try:
            user_imput = Prompt.ask("[bold cyan]pygit>[/bold cyan]", default="help",
                                    show_choices=False, show_default=False).strip().lower()
            if not user_imput:
                continue

            parts = user_imput.split()
            cmd = parts[0]
            if cmd in FUNCTIONS:
                raw_args = parts[1:]
                kwargs = {}
                for arg in raw_args:
                    if arg.startswith("--"):
                        key = arg[2:].replace("-", "_")
                        kwargs[key] = True
                await FUNCTIONS[cmd](**kwargs)
            else:
                showerror(lang.t("main_unknown_cmd", cmd=cmd))
        except KeyboardInterrupt:
            cfg.write()
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

# --------------------------MANIFEST COMMAND--------------------------
# `setsimthreshold` : Change the similarity threshold used to detect a moved save source
# `getsimthreshold` : Show the current similarity threshold
# `listsaves` : List every known save source and the save_N slot it is linked to
# `unlinksave` : Unlink a known path from its save slot (undo a wrong match), never deletes backup files

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

# --------------------------CONFIG COMMAND--------------------------
# `setmaxold` : Modify the MAX_OLD_SAVE parameters, it influes on the maximum number of saves that can be stored in the old_save folder
# `getmaxold` : Get the current MAX_OLD_SAVE parameters
# `checkoppeed` : Recalculate the current Optimal speed to calculate the hash
# `getopspeed` :  Get the current OPTIMALSPEED parameter
# `checkcomputer` : Recalculate which OS your working on (we currently have Linux, MacOS, and Windows compatibility)
# `getcomputer` :   Get what the application found for your OS (not sure if this is relevant...)

# ---------------------------------ARCHITECTURE OF PYGIT-----------------------------------------
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
#     |        |---->README.py
#     |        |---->portabilite.py
#     |        |---->pygnore.py
#     |        |---->configfile.py
#     |        |---->CLI.py (we are here)
#     |        |---->manifest.py
#     |        |---->GUI_engine.py
#     |        |---->GUI.py
#     |
#     |------> README.txt
#     |------>.pygnore
#     |------>.config-file
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.
