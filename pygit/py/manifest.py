import json
from pathlib import Path
from datetime import datetime

from pathtree import get_unified_tree,json_to_tree,flat_tree
import lang
#---------------------------------ARCHITECTURE OF PYGIT-----------------------------------------
#
#    PYGIT (folder)
#     |
#     |----->saves (folder)
#     |        |            
#     |        |----->save_0 (folder)                       
#     |        |        |----->current_save (folder)                        
#     |        |        |             |----->jsontree.json (the tree of the date.zip folder)
#     |        |        |             |----->{date}.zip (the current save named by the date it was make at the format dd:mm:yy_hh:mm.zip)
#     |        |        |----->old_save (folder)
#     |        |                      |
#     |        |                      |---->{date}.zip an old save. In the old_save folder a maximum number of save is fixed by the user in this file right above
#     |        |                      |... and beyond until MAX_OLD_SAVE is reached
#     |       ...
#     |        |----->save_N (folder)
#     |        |-----> manifest.json (and here)
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
#     |        |---->pathree.py
#     |        |---->README.py 
#     |        |---->portabilite.py 
#     |        |---->pygnore.py
#     |        |---->configfile.py
#     |        |---->CLI.py
#     |        |---->manifest.py (we are here)
#     |        |---->GUI_engine.py
#     |        |---->GUI.py 
#     |
#     |------> README.txt
#     |------>.pygnore
#     |------>.config-file
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.

class manifest():
    def __init__(self,cfg):
        self.cfg=cfg
        self.manifestPATH= Path(cfg.DIR) /"saves"/"manifest.json"
        self.manifest_dict={}
        
        
    def load(self):
        """Load the manifest (manifest.json) that links each save_N slot to its known source path(s).

        Args:
            cfg (configfile): the loaded app configuration
        
        Return:s
            dict: the manifest, an empty dict if it doesn't exist

        """
        if not self.manifestPATH.exists():
            self.manifest_dict={}
            return self.manifest_dict
        with open(self.manifestPATH,"r",encoding="utf-8") as f:
            self.manifest_dict=json.load(f) 
        return self.manifest_dict
            
    def write(self,index=None):
        """Persist the manifest (manifest.json) to disk.
 
    Args:
        cfg (configfile): the loaded app configuration
        index (dict): the manifest to write
 
    Returns:
        bool: True once the manifest has been written, False on error
        """
        if index is not None:
            self.manifest_dict=index
        self.manifestPATH.parent.mkdir(parents=True,exist_ok=True)
        try:
            with open(self.manifestPATH,"w",encoding="utf-8") as f:
                json.dump(self.manifest_dict,f,indent=4)
            return True
        except Exception:
            return False
    
    def find_by_path(self,abs_src):
        """Look for a direct match between an absolute path and a known save_N slot.

        Args:
            abs_src (Path): the absolute path of the source we are looking for (wdir)

        Returns:
            str: the save_N name if found, None otherwise
        """
        abs_src = str(abs_src)
        for slot,entry in self.manifest_dict.items():
            if abs_src in entry.get("paths",[]):
                return slot
        return None
    
    def _similarity_ratio(self,tree_a,tree_b):
        """Compute a similarity ratio (0-100) between two trees, based on relative paths and checksum

        Args:
            tree_a (dict): a tree as returned by get_unified_tree()/json_to_tree()
            tree_b (dict): a tree as returned by get_unified_tree()/json_to_tree()

        Returns:
            int: the similarity ratio between the two trees
        """
        flat_a=flat_tree(tree_a,tree_a['path'])
        flat_b=flat_tree(tree_b,tree_b['path'])
        paths_a=set(flat_a.keys())
        paths_b=set(flat_b.keys())
        union = paths_a | paths_b
        if not union:
            return 0
        matched=sum(1 for p in paths_a & paths_b if flat_a[p]['checksum']==flat_b[p]['checksum'])
        return int((matched/len(union))*100)
        
    def find_by_similarity(self,abs_src,src_tree,progress=None,ask=lang.prompt,notify=lang.notify):
        """Look for an existing save_N whose saved tree is similar enough to src_tree, and ask
        the user to confirm the link if a good enough candidate is found.
 
        This is used when a source can't be found by its absolute path (find_by_path), which
        typically happens after the user moved a working directory: the content stays mostly
        the same, only the root path changes.
 
        Note: this relies on saves/save_N/current_save/jsontree.json. If a slot was only ever
        saved once and jsontree.json was never generated, it is silently skipped here (falls
        back to a fresh slot in resolve_save_slot).
 
        Args:
            abs_src (Path): the absolute path of the source we are looking for
            src_tree (dict): the tree of abs_src, as returned by get_unified_tree()
 
        Returns:
            str: the save_N name if the user confirmed a match, None otherwise
        """
        threshold=self.cfg.get_SIMThreshold()
        best_slot,best_score=None,0
 
        for slot in self.manifest_dict:
            jsonfile=Path(self.cfg.DIR)/"saves"/slot/"current_save"/"jsontree.json"
            if not jsonfile.exists():
                continue
            saved_tree=json_to_tree(jsonfile,ask=ask,notify=notify)
            if not saved_tree:
                continue
            score=self._similarity_ratio(saved_tree,src_tree)
            if score>best_score:
                best_slot,best_score=slot,score
 
        if best_slot is None or best_score<threshold:
            return None
 
        # default stays "no" on anything but an explicit "y": a missed link only costs a new
        # slot, a wrong link would silently merge two different sources together.
        notify("manifest_similarity_found",score=round(best_score),path=str(abs_src))
        answer=str(ask("manifest_similarity_confirm")).lower()
        if answer=="y":
            notify("manifest_similarity_confirmed")
            return best_slot
        notify("manifest_similarity_declined")
        return None

    def register(self,slot,abs_src):
        """Add or complete a manifest entry with a new known path for a save_N slot.
 
        Args:
            slot (str): the save_N slot name
            abs_src (Path): the absolute path to link to this slot
 
        Returns:
            dict: the updated manifest
        """
        abs_src=str(abs_src)
        if slot not in self.manifest_dict:
            self.manifest_dict[slot]={"paths":[],"created":datetime.now().isoformat()}
        if abs_src not in self.manifest_dict[slot]["paths"]:
            self.manifest_dict[slot]["paths"].append(abs_src)
        return self.manifest_dict
 
    def _resolve_known_slot(self,abs_src,progress=None,ask=lang.prompt,notify=lang.notify):
        """Look up abs_src against the manifest, without allocating a new slot.

        Order of resolution:
            1) direct match on the absolute path in the manifest
            2) similarity match against existing save_N trees (with user confirmation)
            

        Args:
            abs_src (Path): the absolute path of the source to look for
            ask (callable): prompts for the y/n confirmation, defaults to input() (CLI).
                Pass a GUI-friendly callable (e.g. a Qt dialog) to use this outside a terminal.
            notify (callable): reports progress, defaults to rprint() (CLI).

        Returns:
            str: the save_N name if a known source matches, None otherwise
        """
        self.load()
        slot=self.find_by_path(abs_src)
        if slot is None:
            src_tree=get_unified_tree(abs_src,progress=progress,ask=ask,notify=notify)
            slot=self.find_by_similarity(abs_src,src_tree,progress=progress,ask=ask,notify=notify)
        return slot

    def resolve_save_slot(self,abs_src,progress=None,ask=lang.prompt,notify=lang.notify):
        """Resolve which saves/save_N folder should be used as the "dest" of save() for a given source.
 
        Order of resolution:
            1) direct match on the absolute path in the manifest
            2) similarity match against existing save_N trees (with user confirmation)
            3) fallback: create a brand new save_N slot
 
        Args:
            abs_src (Path): the absolute path of the source to save
 
        Returns:
            Path: the absolute path of the save_N folder to use as "dest"
        """
        slot=self._resolve_known_slot(abs_src,progress=progress,ask=ask,notify=notify)
 
        if slot is None:
            slot=f"save_{len(self.manifest_dict)}"
            notify("manifest_new_slot",slot=slot)
 
        self.register(slot,abs_src)
        self.write()
        slot_path=Path(self.cfg.DIR)/"saves"/slot
        # save()/get_abs() require "dest" to already exist on disk (unlike cfg.DIR, a
        # freshly allocated save_N slot doesn't exist yet on its first use), so it is
        # created here, right where the slot itself gets allocated.
        slot_path.mkdir(parents=True,exist_ok=True)
        return slot_path

    def resolve_existing_slot(self,abs_src,progress=None,ask=lang.prompt,notify=lang.notify):
        """Resolve which saves/save_N folder holds the latest save of abs_src, WITHOUT ever
        allocating a new slot.

        Meant for read-only operations like dryrun(): if the source has never been saved,
        there is simply nothing to compare, and no slot should be created just to check that.

        Args:
            abs_src (Path): the absolute path of the source to look for
            ask (callable): prompts for the y/n confirmation, defaults to input() (CLI).
            notify (callable): reports progress, defaults to rprint() (CLI).

        Returns:
            Path: the absolute path of the matching save_N folder, or None if abs_src is
                  unknown to the manifest
        """
        slot=self._resolve_known_slot(abs_src,progress=progress,ask=ask,notify=notify)
        if slot is None:
            return None
        return Path(self.cfg.DIR)/"saves"/slot

    def unregister(self,abs_src):
        """Unlink a known path from its save_N slot, e.g. to undo a wrong similarity match
        confirmation (find_by_similarity).

        This ONLY edits the manifest.json mapping: the actual saves/save_N folder and its
        zip archives are never touched or deleted here. If the slot ends up with no path
        left, its manifest entry is dropped too (but the folder on disk stays untouched).

        Args:
            abs_src (Path): the absolute path to unlink

        Returns:
            str: the save_N slot the path was removed from, or None if abs_src was unknown
        """
        abs_src=str(abs_src)
        self.load()
        for slot,entry in list(self.manifest_dict.items()):
            paths=entry.get("paths",[])
            if abs_src in paths:
                paths.remove(abs_src)
                if not paths:
                    del self.manifest_dict[slot]
                self.write()
                return slot
        return None

    def list_sources(self):
        """List every known source path and the save_N slot it is linked to.

        Returns:
            dict: {absolute_path: save_N}, one entry per known path (a moved source can end up
                  with several paths pointing to the same slot, see find_by_similarity)
        """
        self.load()
        sources={}
        for slot,entry in self.manifest_dict.items():
            for p in entry.get("paths",[]):
                sources[p]=slot
        return sources
 
    def resolve_restore_target(self,progress=None,ask=lang.prompt,notify=lang.notify):
        """Resolve which saves/save_N folder should be used as the "dest" of restore().
 
        If a single source is known, it is returned directly without asking the user anything.
        If several sources are known, the user is asked which working directory (path) they want
        to restore: the save_N slot itself stays transparent to them.
 
        Returns:
            Path: the absolute path of the save_N folder to restore from, or None if no source is
                  known yet or the user interrupted the selection
        """
        self.load()
        path_to_slot=self.list_sources()
        if not path_to_slot:
            notify("manifest_restore_no_source")
            return None
 
        if len(path_to_slot)==1:
            only_path=next(iter(path_to_slot))
            return Path(self.cfg.DIR)/"saves"/path_to_slot[only_path]
 
        filelist="\n".join(path_to_slot.keys())
        condition=False
        choice=None
        while not condition:
            choice=str(ask("manifest_restore_choice",filelist=filelist))
            if choice.lower()=="exit":
                notify("manifest_restore_exit")
                return None
            elif choice in path_to_slot:
                condition=True
            else:
                notify("manifest_restore_invalid")
 
        return Path(self.cfg.DIR)/"saves"/path_to_slot[choice]
 
 
"Le meilleur code est celui qu'on comprend six mois plus tard sans grimacer."