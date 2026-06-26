
from pathlib import Path
import json
import zipfile
import os
from datetime import datetime
from pygnore import *
from rich.progress import track
from portabilite import set_computer
from portabilite import compute_hash
from portabilite import compute_zip_hash
import lang

COMPUTER=set_computer()
COMPUTER.set_optimal_speed()


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
#     |        |---->pathree.py (we are here)
#     |        |---->README.py
#     |        |---->portabilite.py
#     |        |---->pygnore.py
#     |        |---->configfile.py
#     |        |---->CLI.py
#     |
#     |------> README.txt
#     |------>.pygnore
#     |------>.config-file
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.

IGNORE_MNGR=pygnore()



#===========Potentiellement à corriger===========
def flat_tree(node, root_path):
    flat = {}
    path_str=node['path']
    #il faut pouvoir différencier s'il provient d'un zip ou pas
    if '://' in path_str:
        innerzipfile= path_str.split('://',1)[1]
        parts=innerzipfile.split("/",1)
        rel_path = parts[1] if len(parts) >1 else parts[0]
    else:
        rel_path = os.path.relpath(node['path'], root_path)
    if node['type'] == 'file':
        if not ('checksum' in node):
            #il faut pouvoir différencier s'il provient d'un zip ou pas
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


def get_child_list(path):
    p = Path(path)
    children = []
    if p.is_dir():
        try:
            for item in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                children.append(item)
        except PermissionError:
            print(lang.t("child_list_no"))
        return children
    else:
        return 0

# GESTION DES ARBRES


def tree_to_json(tree,path):
    with open(f"{path}/jsontree.json", "w") as jsonobj:
        json.dump(tree, jsonobj, indent=4)


def json_to_tree(path):
    p = Path(path)
    if not p.exists():
        print(lang.t("jtot_error"),path=path)
        return 0
    with open(p, "r") as jsonfile:
        return json.load(jsonfile)


def get_zip_tree(zip_path,verbose=False,is_root=True):
    """Génère une structure similaire à get_tree mais pour un fichier .zip"""

    # on ajoute une gestion du include /exclude en comptant qu'ils viennent de get_unified_tree donc deux dictionnaires sous la forme {"type":"","names":[]}
    if verbose:
        print(lang.t("ziptree_verbose"),path=zip_path)
    zip_path=Path(zip_path)
    name=zip_path.name
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
           if is_root and COMPUTER.is_CLI():
            loop = track(infos, description=f"Lecture du ZIP {name}...")
           else:
               loop=infos
           for info in loop:
                full_path=info.filename
                is_dir= info.is_dir() or full_path.endswith("/")
                
                parts = full_path.rstrip('/').split('/')
                dir_parts = parts if is_dir else parts[:-1]
                
                current_rel_path=""
                skip=False
                
                for part in dir_parts:
                    parent_rel_path = current_rel_path
                    current_rel_path = f"{current_rel_path}/{part}".strip('/')
                    
                    if current_rel_path not in dir_nodes:
                        if IGNORE_MNGR.needtoInclude(part,is_dir=True):
                            new_node = {
                                "name": part,
                                "type": "directory",
                                "path": f"{zip_path}://{current_rel_path}",
                                "timestamp": datetime(*info.date_time).timestamp(),
                                "smax": 0,
                                "children": []
                            }
                            # On ajoute le dossier à la liste "children" de son parent
                            dir_nodes[parent_rel_path]["children"].append(new_node)
                            # On le référence pour pouvoir lui ajouter des enfants plus tard
                            dir_nodes[current_rel_path] = new_node
                        else:
                            dir_nodes[current_rel_path] = None
                            skip = True
                            break
                    else:
                        # Si l'entrée du dossier existait déjà mais qu'on tombe sur l'entrée 
                        # officielle du dossier dans le ZIP, on met à jour son timestamp
                        if is_dir and current_rel_path == full_path.rstrip('/'):
                            if dir_nodes[current_rel_path] is not None:
                                dir_nodes[current_rel_path]["timestamp"] = datetime(*info.date_time).timestamp()
                
                # Si un des dossiers parents a été exclu, on passe au fichier suivant
                if skip or dir_nodes.get(current_rel_path) is None:
                    continue
                
                if not is_dir:
                    file_name = parts[-1]
                    if IGNORE_MNGR.needtoInclude(file_name,is_dir=False):
                        p = f"{zip_path}://{full_path}"
                        dt = datetime(*info.date_time)
                        
                        try:
                            with z.open(full_path) as f:
                                checksum = compute_zip_hash(f)
                        except Exception:
                            checksum = "Error"
                            
                        # On ajoute le fichier dans la liste "children" du dossier parent trouvé
                        dir_nodes[current_rel_path]["children"].append({
                            "name": file_name,
                            "type": "file",
                            "timestamp": dt.timestamp(),
                            "smax": info.file_size,
                            "checksum": checksum,
                            "path": p,
                        })
                        
           for node in dir_nodes.values():
                if node and "children" in node:
                    node["children"].sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
                    
    except Exception as e:
        tree["error"] = f"Erreur lors de la lecture du ZIP : {str(e)}"
        
    return tree
            


def get_tree(path,verbose=False,is_root=True):
    path = os.path.abspath(path)
    name = os.path.basename(path)
    # on ajoute une gestion du include /exclude en comptant qu'ils viennent de get_unified_tree donc deux dictionnaires sous la forme {"type":"","names":[]}
    if verbose:
        print(lang.t("tree_verbose"),path=path)
    if os.path.isdir(path):
        if IGNORE_MNGR.needtoInclude(name,is_dir=True):
            tree = {
                "name": name,
                "type": "directory",
                "timestamp": os.path.getmtime(path),
                "smax": os.path.getsize(path),
                "path": path,
                "children": []
            }
            try:
                items=list(os.scandir(path))
                if is_root and COMPUTER.is_CLI():
                    loop=track(items,description=f"Analyse de {os.path.basename(path)}...") 
                else:
                    loop = items
                for item in loop:
                    child=get_tree(item.path,verbose,is_root=False)
                    if child:
                        tree["children"].append(child)
            except PermissionError:
                tree["error"] = "Access Denied"
        else:
            return None
    else:
        if IGNORE_MNGR.needtoInclude(name,is_dir=False):
            tree = {
                "name": name,
                "type": "file",
                "timestamp": os.path.getmtime(path),
                "smax": os.path.getsize(path),
                "checksum": compute_hash(path,COMPUTER.get_optimal_speed()),
                "path": path
            }
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

def get_unified_tree(path,verbose=False):
    """Détermine si c'est un zip ou un dossier et renvoie l'arbre correspondant"""
    p = Path(path)
    if p.suffix.lower() == '.zip':
        return get_zip_tree(p,verbose)
    # Sinon on utilise la fonction de pathtree.py
    return get_tree(p,verbose)


def count_tree(tree):
    nb = 0
    if tree["type"] == 'directory':
        for file in tree["children"]:
            nb += 1
            if file['type'] == 'directory':
                nb += count_tree(file)
    return nb