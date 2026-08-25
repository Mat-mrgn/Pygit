from pathlib import Path
import json
import zipfile
import os
from datetime import datetime
from pygnore import *
from portabilite import set_computer
from portabilite import compute_hash
from portabilite import compute_zip_hash
import lang

COMPUTER=set_computer()
IGNORE_MNGR=get_ignore()


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
#     |        |---->pathree.py (we are here)
#     |        |---->README.py
#     |        |---->portabilite.py
#     |        |---->pygnore.py
#     |        |---->configfile.py
#     |        |---->CLI.py
#     |
#     |------> README.txt
#     |------>.pygnore
#     |------>.config-file (and here...maybe)
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.





def flat_tree(node, root_path):
    flat = {}
    path_str=node['path']
    #diff if the file is zip or not 
    if '://' in path_str:
        innerzipfile= path_str.split('://',1)[1]
        parts=innerzipfile.split("/",1)
        rel_path = parts[1] if len(parts) >1 else parts[0]
    else:
        rel_path = os.path.relpath(node['path'], root_path)
        if rel_path==".":
            rel_path = node["name"]
    if node['type'] == 'file':
        if not ('checksum' in node):
            #dif if file is from a zip or not
            if '://' not in path_str: 
                node['checksum'] = compute_hash(node['path'],COMPUTER.get_optimal_speed())
            else:
                node['checksum'] = 'Error'
        flat[rel_path] = node

    if 'children' in node:
        for child in node['children']:
            flat.update(flat_tree(child, root_path))
    return flat

#==================================================
def get_dir_size(path):
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        if IGNORE_MNGR.needtoInclude(entry.name, is_dir=True):
                            total += get_dir_size(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        if IGNORE_MNGR.needtoInclude(entry.name, is_dir=False):
                            total += entry.stat().st_size
                except (PermissionError, FileNotFoundError):
                    continue
    except PermissionError:
        pass
    return total

def get_child_list(path,ask=lang.prompt,notify=lang.notify):
    p = Path(path)
    if not p.is_dir():
        return "not_folder"
    children = []
    try:
        for item in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            children.append({
                "name":item.name,
                "path":str(item),
                "is_dir":item.is_dir(),
            })
    except PermissionError:
        notify("child_list_no")
        return "denied"
    return children

# TREE management


def tree_to_json(tree,path):
    with open(f"{path}/jsontree.json", "w") as jsonobj:
        json.dump(tree, jsonobj, indent=4)


def json_to_tree(path,ask=lang.prompt,notify=lang.notify):
    p = Path(path)
    if not p.exists():
        notify("jtot_error",path=path)
        return 0
    with open(p, "r") as jsonfile:
        return json.load(jsonfile)
        
def fix_zip_name(info):
    name = info.filename
    if info.flag_bits & 0x800:
        return name
    try:
        return name.encode('cp437').decode('utf-8')
    except(UnicodeDecodeError, UnicodeEncodeError):
        return name


def get_zip_tree(zip_path,verbose=False,is_root=True,progress=None,label="verify",ask=lang.prompt,notify=lang.notify):
    """Generate a similar structure than of get_tree but for a .zip file"""

    # we add a managing system of the include /exclude taking if they are from get_unified_tree so two dictionnary under the type :  {"type":"","names":[]}
    if verbose:
        notify("ziptree_verbose",path=zip_path)
    zip_path=Path(zip_path)
    name=zip_path.name
    owned =False
    if not IGNORE_MNGR.needtoInclude(name,is_dir=True):
        return None
    
    tree={
        "name":name,
        "type":"directory",
        "path":str(zip_path),
        "timestamp":os.path.getmtime(zip_path),
        "smax":os.path.getsize(zip_path),
        "children":[]
    }
    try:
        with zipfile.ZipFile(zip_path,'r') as z:
            dir_nodes={"":tree}
           
            infos=sorted(z.infolist(),key=lambda x: x.filename.lower())
            total_bytes = sum(i.file_size for i in infos if not i.is_dir())
            if is_root:
                owned=progress is None
                if owned:
                    progress = make_progress(lang.t("zip_reading",zip=name),computer=COMPUTER)
                    progress.__enter__()
                task = progress.add_task(label, total=max(total_bytes, 1))
            for info in infos:
                full_path=fix_zip_name(info)
                is_dir= info.is_dir() or full_path.endswith("/")
                
                parts = full_path.rstrip('/').split('/')
                dir_parts = parts if is_dir else parts[:-1]
                
                current_rel_path=""
                skip=False
                
                for part in dir_parts:
                    parent_rel_path = current_rel_path
                    current_rel_path = f"{current_rel_path}/{part}".strip('/')
                    
                    if current_rel_path not in dir_nodes:
                        if dir_nodes[parent_rel_path] is None:
                            dir_nodes[current_rel_path] = None
                            skip = True
                            break
                        if IGNORE_MNGR.needtoInclude(part,is_dir=True):
                            new_node = {
                                "name": part,
                                "type": "directory",
                                "path": f"{zip_path}://{current_rel_path}",
                                "timestamp": datetime(*info.date_time).timestamp(),
                                "smax": 0,
                                "children": []
                            }
                            # We add the file to his "child" list
                            dir_nodes[parent_rel_path]["children"].append(new_node)
                            # We add him in reference for later use
                            dir_nodes[current_rel_path] = new_node
                        else:
                            dir_nodes[current_rel_path] = None
                            skip = True
                            break
                    else:
                        #If the entry of the folder already exist but we fall on the official 
                        # entry of the folder in the zip, we modify it's timestamp
                        if dir_nodes[current_rel_path] is None:
                            skip = True
                            break
                        if is_dir and current_rel_path == full_path.rstrip('/'):
                            dir_nodes[current_rel_path]["timestamp"] = datetime(*info.date_time).timestamp()
                
                # If one of the parents folder is excluded, we go to the next file
                if skip or dir_nodes.get(current_rel_path) is None:
                    continue
                
                if not is_dir:
                    file_name = parts[-1]
                    if IGNORE_MNGR.needtoInclude(file_name, is_dir=False):
                        p = f"{zip_path}://{full_path}"
                        dt = datetime(*info.date_time)

                        try:
                            with z.open(info) as f:
                                checksum = compute_zip_hash(f)
                        except Exception:
                            checksum = "Error"

                        dir_nodes[current_rel_path]["children"].append({
                            "name": file_name,
                            "type": "file",
                            "timestamp": dt.timestamp(),
                            "smax": info.file_size,
                            "checksum": checksum,
                            "path": p,
                        })
                        if progress is not None:
                            progress.advance(task, advance=info.file_size)
            for node in dir_nodes.values():
                if node and "children" in node:
                    node["children"].sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
                    
    except Exception as e:
        tree["error"] = f"Error during the ZIP reading : {str(e)}"
    if owned and progress is not None:
        progress.__exit__(None,None,None)
    return tree
            

def get_tree(path, verbose=False, is_root=True, progress=None, task=None,hashing=True,label="analyse",ask=lang.prompt,notify=lang.notify):
    if is_root:
        owned = progress is None
        if owned:
            progress= make_progress(lang.t("analyse",path=os.path.basename(path)),computer=COMPUTER)
            progress.__enter__()
        try:
            total = get_dir_size(path) if os.path.isdir(path) else os.path.getsize(path)
            task = progress.add_task(label, total=max(total, 1))
            return _get_tree(path, verbose, progress, task,hashing,label,ask,notify)
        finally:
            if owned:
                progress.__exit__(None,None,None)
    return _get_tree(path,verbose,progress,task,hashing,ask,notify)

def _get_tree(path,verbose,progress,task,hashing=True,ask=lang.prompt,notify=lang.notify): 
    path = os.path.abspath(path)
    name = os.path.basename(path)
    if verbose:
        notify("tree_verbose", path=path)
    if os.path.isdir(path):
        if IGNORE_MNGR.needtoInclude(name, is_dir=True):
            tree = {
                "name": name, "type": "directory",
                "timestamp": os.path.getmtime(path),
                "smax": os.path.getsize(path),
                "path": path, "children": []
            }
            try:
                for item in os.scandir(path):
                    child = _get_tree(item.path, verbose, progress,task,hashing,ask,notify)
                    if child:
                        tree["children"].append(child)
            except PermissionError:
                tree["error"] = "Access Denied"
        else:
            return None
    else:
        if IGNORE_MNGR.needtoInclude(name, is_dir=False):
            size = os.path.getsize(path)
            tree = {
                "name": name, "type": "file",
                "timestamp": os.path.getmtime(path),
                "smax": size,
                "checksum": compute_hash(path, COMPUTER.get_optimal_speed()) if hashing else None,
                "path": path
            }
            if progress is not None:
                progress.advance(task, advance=size)
        else:
            return None
    return tree

def get_node(path):
    path = os.path.abspath(path)
    name = os.path.basename(path)
    if os.path.isdir(path):
        node={
            "name": name,
            "type": "directory",
            "timestamp": os.path.getmtime(path),
            "smax": os.path.getsize(path),
            "path": path,
            "children": []
        }
        try: 
            for item in sorted(os.scandir(path), key=lambda x: (x.is_file(),x.name.lower())):
                child={"name":os.path.basename(item),
                       "timestamp":os.path.getmtime(item),
                       "smax":os.path.getsize(item),
                       "path":item,
                       }
                node["children"].append(child)
        except PermissionError:
            node["error"] = "Access Denied"
    else:
        node = {
                "name": name,
                "type": "file",
                "timestamp": os.path.getmtime(path),
                "smax": os.path.getsize(path),
                "checksum": compute_hash(path,COMPUTER.get_optimal_speed()),
                "path": path
        }
    return node

def get_unified_tree(path,verbose=False,progress=None,hashing=True,label=None,ask=lang.prompt,notify=lang.notify):
    """Tell if it's a zip or a folder and send back the corresponding tree"""
    p = Path(path)
    if p.suffix.lower() == '.zip':
        return get_zip_tree(p,verbose,progress=progress,label=label or "verify",ask=ask,notify=notify)
    # Else we use the function of pathtree.py
    return get_tree(p,verbose,progress=progress,hashing=hashing,label=label or "analyse",ask=ask,notify=notify)


def count_tree(tree):
    nb = 0
    if tree["type"] == 'directory':
        for file in tree["children"]:
            nb += 1
            if file['type'] == 'directory':
                nb += count_tree(file)
    return nb