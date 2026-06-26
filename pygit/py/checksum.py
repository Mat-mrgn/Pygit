from pathlib import Path
# comparaison de deux fichiers ou dossiers
from pathtree import *
import portabilite
from portabilite import compute_hash
from portabilite import compute_zip_hash
COMPUTER=portabilite.set_computer()
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
#     |        |---->checksum.py (we are here)
#     |        |---->pathree.py
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

def checksumfiles(p1, p2):
    """Check if the content of p1 == the content of p2 by using the hashcode of the file 

    @Args:
        p1(Path) or (tree): struct can be both tree or path it will be handled  
        p2(Path) or (tree): struct can be both tree or path it will be handled
    @Returns:
        bool: the result of the operation
    @seealso:
        - checksumfolder(p1,p2)
        - get_tree (from pathree.py)
    """
    res=None
    if type(p1) == dict and type(p2)==dict:
        res= p1["checksum"] == p2["checksum"]
    elif type(p1)==dict and type(p2)!=dict:
        res=p1["checksum"] == compute_hash(p2,COMPUTER.get_optimal_speed())
    elif type(p1) !=dict and type(p2)==dict:
        res= compute_hash(p1,COMPUTER.get_optimal_speed()) == p2["checksum"]
    else:
        res= compute_hash(p1,COMPUTER.get_optimal_speed()) == compute_hash(p2,COMPUTER.get_optimal_speed())
    return res


def comparefolder(tree_of_p1, tree_of_p2):
    """Check if the content of the folder p1 == the content of the folder p2 recursivly to check every files
        It does the same as checksumfolder but return the list of the modified files

    @Args:
        tree_of_p1 (dict): a dictionnary that describe the whole content of a folder is considered as the working directory
        tree_of_p2 (dict): a dictionnary that describe the whole content of a folder is considered as the save

    @Returns:
        bool: the result of the operation
        diff: a dictionnary of all the differences find between the two tree

    @seealso:
        - checksumfiles(p1,p2)
    """
    diff = {
        "Created": [],
        "Deleted": [],
        "Modified": [],
        "Moved": []
    }
    c1 = flat_tree(tree_of_p1, tree_of_p1['path'])
    c2 = flat_tree(tree_of_p2, tree_of_p2['path'])
    paths1 = set(c1.keys())
    paths2 = set(c2.keys())

    for p in paths1 & paths2:
        f1 = c1[p]
        f2 = c2[p]

        if f1['timestamp'] == f2['timestamp'] and f1['smax'] == f2['smax']:
            continue
        if f1['checksum'] != f2['checksum']:
            diff["Modified"].append((p, p))

    p_deleted = list(paths1 - paths2)
    p_created = list(paths2 - paths1)

    r_deleted = []
    for p_del in p_deleted:
        file_md_del = c1[p_del]

        match_found = False

        for p_crea in p_created[:]:
            if c2[p_crea]['checksum'] == file_md_del['checksum']:
                diff['Moved'].append((p_del, p_crea))
                p_created.remove(p_crea)
                match_found = True
                break
        if not match_found:
            r_deleted.append((p_del, None))
    for p_crea in p_created:
        diff['Created'].append((None, p_crea))

    diff['Deleted'] = r_deleted

    if len(diff['Created']) == 0 and len(diff['Deleted']) == 0 and len(diff['Modified']) == 0 and len(diff['Moved']) == 0:
        return True, diff

    return False, diff


       
