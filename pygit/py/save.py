# Imports
import os
from pathlib import Path
from datetime import datetime
from rich.progress import track
import zipfile

# Utility call
from README import *
from checksum import *
from pathtree import *
from portabilite import *
import lang

from configfile import get_cfg

# ---------------------------------ARCHITECTURE OF PYGIT-----------------------------------------
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
#     (Please note that since this part is optional since we work with absolute path and we can put the Py folder (the app) wherever we want)
#     |-------Py (folder)
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
#     |        |---->save.py   (we are here)
#     |        |---->checksum.py
#     |        |---->pathree.py
#     |        |---->README.py
#     |        |---->portabilite.py
#     |        |---->pygnore.py
#     |        |---->configfile.py
#     |        |---->CLI.py
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


# MAX_OLD_SAVE is the maximum number of save we accept to be stocked in the old_save_file

def save(dest, src="folder", H_name=False,verbose=False,progress=None,ask=lang.prompt,notify=lang.notify):
    cfg=get_cfg()
    abs_dest = cfg.get_abs(dest)  # where the save is located
    abs_src = cfg.get_abs(src)  # where the working directory is located
    if abs_dest== 404:
        return (404,"The defined path does not exist")
    if abs_src== 404:
        return (404,"The defined path does not exist")
    src_tree = get_unified_tree(abs_src,verbose=verbose,progress=progress,ask=ask,notify=notify)
    pygit_cs = Path(abs_dest / 'current_save')
    pygit_os = Path(abs_dest / 'old_save')
    # here we will get the today date for the future save file
    DATE = datetime.now().strftime("%d-%m-%Y.zip")
    if H_name:
        DATE = datetime.now().strftime("%d-%m-%Y_%H-%M.zip")
    # so now we have ARCHIVE that contain the future name of the save file
    ARCHIVE = Path(pygit_cs / DATE)
    # if we got pygit dir then it mean whe got the "whole" package (if user is not stupid) "worst case scenario will be seen later on "update" "

    # case one we already got a save
    if pygit_cs.exists():
        searched_path=None
        zip_list = [file for file in COMPUTER.ls_dir(
            pygit_cs) if file.endswith(".zip")]
        if len(zip_list) >= 1:
            searched_path = zip_list[0]
        child_list = COMPUTER.ls_dir(pygit_cs)
        if searched_path:
            archive_path = pygit_cs/searched_path
            if os.path.getmtime(archive_path) > os.path.getmtime(abs_src):
                notify("save_warning") 
                if str(ask("save_warning_cont")).lower() == "n":
                    return (200, "User Interruption")
        if not searched_path:
            pygit_cs.mkdir(parents=True,exist_ok=True)
            pygit_os.mkdir(exist_ok=True)
            # should compress the file to the destination (may take some time)
            r = COMPUTER.zip(abs_src, ARCHIVE,progress=progress)
            if r:
                initREADME(dest=abs_dest)
            else:
                errorREADME(abs_src,"save",dest=abs_dest)
                return (500, "Error while trying to compress")
            cs_tree = get_unified_tree(ARCHIVE,verbose=verbose,progress=progress,ask=ask,notify=notify)
            if "error" in cs_tree:
                errorREADME(cs_tree["error"], "verify", dest=abs_dest)
                return (500, f"Error while reading the archive for verification: {cs_tree['error']}")
            result, comparaisondict = comparefolder(cs_tree, src_tree)
            PARSEintegritycheck(result,dest=abs_dest)
            if result:
                return (200, "Success")
            else:
                parseREADME(comparaisondict,dest=abs_dest)
                return (417, "Error the current save is corrupted, Please retry it")
            
        if "jsontree.json" in child_list:
            jsonfile = Path(pygit_cs/'jsontree.json')
            savedtree = json_to_tree(jsonfile,ask=ask,notify=notify)
        else:   
            savedtree = get_unified_tree(archive_path,verbose=verbose,progress=progress,label="analyse",ask=ask,notify=notify)
        result, comparaisondict = comparefolder(savedtree, src_tree)
        if not result:  # if there is in fact some differencies we will parse it down on the README text file
            parseREADME(comparaisondict,dest=abs_dest)
        # ===================Now that we have compared our save and our working directory we will clean the app (pygit_os and etc...)
        # this part below only search if the current MAX_OLD_SAVE is passed and will delete the oldest in order to put the save
        pygit_os.mkdir(exist_ok=True)
        node_os = get_node(pygit_os)
        if len(node_os["children"]) >= cfg.MAX_OLD_SAVE:
            childs=list(node_os["children"])
            oldest = childs[0]
            if COMPUTER.is_CLI():
                loop= track(childs,description=lang.t("save_des"))
            else:
                loop= childs
            for child in loop:
                if oldest["timestamp"] > child["timestamp"]:
                    oldest = child
            COMPUTER.rm_dir(oldest["path"])
        COMPUTER.mv_dir(archive_path, pygit_os)
        r = COMPUTER.zip(abs_src, ARCHIVE,progress=progress)
        if not r:
            errorREADME(abs_src,"zip",dest=abs_dest)
            return (500,"Error while trying to zip the file")
        tree_to_json(src_tree, pygit_cs)

    # case two: it is the first save we will make
    else:
        # Create the folder current-save and old_save
        pygit_cs.mkdir(parents=True,exist_ok=True)
        pygit_os.mkdir(exist_ok=True)
        # should compress the file to the destination (may take some time)
        r = COMPUTER.zip(abs_src, ARCHIVE,progress=progress)
        if r:
            initREADME(dest=abs_dest)
        else:
            errorREADME(abs_src,"save",dest=abs_dest)
            return (500, "Error while trying to compress")
    # <- we will do another comparaison in order to make sure the file isn't corrupted during the compression
    cs_tree = get_unified_tree(ARCHIVE,verbose=verbose,progress=progress,ask=ask,notify=notify)
    if "error" in cs_tree:
                    errorREADME(cs_tree["error"], "verify", dest=abs_dest)
                    return (500, f"Error while reading the archive for verification: {cs_tree['error']}")
    result, comparaisondict = comparefolder(cs_tree, src_tree)
    PARSEintegritycheck(result,dest=abs_dest)
    if result:
        return (200, "Success")
    else:
        parseREADME(comparaisondict,dest=abs_dest)
        return (417, "Error the current save is corrupted, Please retry it")


def dryrun(src, dest_path=None, verbose=False,chain_save=True,progress=None,ask=lang.prompt,notify=lang.notify):
    cfg=get_cfg()
    abs_src = cfg.get_abs(src)
    abs_save = cfg.get_abs(dest_path) if dest_path else Path(cfg.DIR)
    savetree=None
    pygit_cs = Path(abs_save / "current_save")
    if not pygit_cs.exists():
        return (404, f"No existing save found in {abs_save}. Nothing to compare.")
    child_list = COMPUTER.ls_dir(pygit_cs)
    if "jsontree.json" in child_list:
        savetree = json_to_tree(Path(pygit_cs/"jsontree.json"),ask=ask,notify=notify)
    else:
        for file in child_list:
            if file.endswith(".zip"):
                savetree = get_unified_tree(Path(pygit_cs/file),verbose=verbose,progress=progress,ask=ask,notify=notify)
                break
    if not savetree:
        return (404, "Impossible to find an index or a valid archive")
    srctree = get_unified_tree(abs_src,verbose=verbose,progress=progress,ask=ask,notify=notify)
    result, comparedir = comparefolder(savetree, srctree)
    if result:
        if verbose:
            notify("dryrun_no_diff",src=src,dest=dest_path)
        return (200, comparedir)
    else:
        if verbose:
            notify("dryrun_diff_found")
            categories = {
                "Created": {"color": "green", "sign": "(+)", "label": "Files Created"}, 
                "Modified": {"color": "yellow", "sign": "(*)", "label": "Files Modified"}, 
                "Moved": {"color": "blue", "sign": "(/)", "label": "Files Moved"}, 
                "Deleted": {"color": "red", "sign": "(-)", "label": "Files Deleted"} 
            }
            if len(comparedir["Created"]) > 0:
                notify("dryrun_created_header")
                for created_file in comparedir['Created']:
                    csign = categories["Created"]["sign"]
                    notify("dryrun_line",sign=csign,path=str(created_file[1]))
            else:
                notify("dryrun_created_none")

            if len(comparedir["Deleted"]) > 0:
                notify("dryrun_deleted_header")
                for deleted_file in comparedir['Deleted']:
                    dsign = categories["Deleted"]["sign"]
                    notify("dryrun_line",sign=dsign,path=str(deleted_file[0]))
            else:
                notify("dryrun_deleted_none")

            if len(comparedir["Modified"]) > 0:
                notify("dryrun_modified_header")
                for modified_file in comparedir['Modified']:
                    msign = categories["Modified"]["sign"]
                    notify("dryrun_line",sign=msign,path=str(modified_file[1]))
            else:
                notify("dryrun_modified_none")

            if len(comparedir["Moved"]) > 0:
                notify("dryrun_moved_header")
                for moved_file in comparedir['Moved']:
                    mmsign = categories["Moved"]["sign"]
                    notify("dryrun_line",sign=mmsign,path=str(moved_file[1]))
            else:
                notify("dryrun_moved_none")
            notify("dryrun_end")
        if not chain_save:
            return(200,comparedir)
        willtosave = ""
        while (willtosave.lower() != "y" and willtosave.lower() != "n"):
            try:
                willtosave = str(ask("dryrun_willtosave"))
            except EOFError:
                return (200,comparedir)
        if willtosave.lower() == "y":
            return save(dest=abs_save, src=abs_src,progress=progress,ask=ask,notify=notify)
        return (200, comparedir)

def _pick_archive(name,folder,filelist):
    name = str(name)
    if name in filelist and name.endswith(".zip"):
        return Path(folder)/name
    if f"{name}.zip" in filelist:
        return Path(folder)/f"{name}.zip"
    return None

def restore(dest, save_dir=None, fromolder=False,archive=None,progress=None,ask=lang.prompt,notify=lang.notify):
    cfg=get_cfg()
    ABS_DEST=cfg.get_abs(dest)
    # save_dir is the saves/save_N folder resolved by manifest.resolve_restore_target().
    # Kept optional (falling back to cfg.DIR instead of the former cfg.BASE_DIR) so this
    # still works if called without going through the manifest.
    base = Path(save_dir) if save_dir is not None else Path(cfg.DIR)
    if fromolder:
        path = base/"old_save"
        filelist = COMPUTER.ls_dir(path)
        savefile=_pick_archive(archive,path,filelist) if archive is not None else None
        if archive is not None and savefile is None:
            return ("404","The requested archive does not exist")
        while savefile is None:
            choice = str(ask("restore_choice",filelist=filelist))
            if choice.lower()=="exit":
                return (200,"User Interrupted Restore")
            savefile = _pick_archive(choice,path,filelist)
        jsontree=get_unified_tree(savefile,progress=progress,ask=ask,notify=notify)
    else:
        path = base/"current_save"
        savefile = [file for file in COMPUTER.ls_dir(
            path) if file.endswith(".zip")]
        if len(savefile) == 0:
            return (404, "There is no current save")
        savefile = Path(path / savefile[0])
        if Path(path/"jsontree.json").exists():
            jsontree= json_to_tree(Path(path/"jsontree.json"),ask=ask,notify=notify)
        else:
            jsontree = get_unified_tree(savefile,progress=progress,ask=ask,notify=notify)
    #now we got the file we want to restore and his jsontree under the same variable name "ABSOLUTE VARIABLE"
    unzipcom = COMPUTER.unzip(savefile,ABS_DEST)
    #the file is unziped now we will check for his integrity to securize it 
    if unzipcom:
        with zipfile.ZipFile(savefile) as z:
            root_name = z.namelist()[0].split('/')[0]
        integritytree=get_unified_tree(Path(ABS_DEST/root_name),progress=progress,ask=ask,notify=notify)
        r,diffdic = comparefolder(integritytree,jsontree)
        PARSEintegritycheck(r,dest=ABS_DEST)
        if r:
            return(200,"The restauration is successfull, Integrity check valid.")
        else:
            return(417,diffdic)
    else:
        errorREADME(savefile,"restore",dest=ABS_DEST)
        return (500,"An error as occured while trying to unzip the file")

"Où finit la paresse, où commence la contemplation? - Jean Dutourd"