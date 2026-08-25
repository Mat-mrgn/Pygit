from pathlib import Path
from portabilite import *
import fnmatch
COMPUTER = set_computer()
BASE_DIR = COMPUTER.get_app_root()
_IGNORE_INSTANCE=None

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
#     |        |---->pygnore.py (we are here)
#     |        |---->configfile.py
#     |        |---->CLI.py 
#     |        |---->manifest.py
#     |        |---->GUI_engine.py
#     |        |---->GUI.py 
#     |
#     |------> README.txt
#     |------>.pygnore (and here)
#     |------>.config-file
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.

# Here we will work on the gestion of  .pygnore

class pygnore():
    
    def __init__(self):
        self._path=BASE_DIR #The pyignore will always be searched at the root of the py folder. Except if the user set it specifically 
        #pygnore constructor under here |
        self._path=f"{BASE_DIR}/.pygnore"
        self.inc=[]
        self.exc=[]
        if Path(self._path).exists():
            self.load()
        else:
            self._create_default()


    def _create_default(self):
        """Create the default file"""
        default_rules = [
            "# default exclude\n",
            "> fo __pycache__\n",
            "> fo .git\n",
            "> fi *.DS_Store\n",
            "> fi desktop.ini\n",
            "> fo .venv\n",
            "> fo env\n"
        ]
        with open(self._path, encoding="utf-8", mode="w") as pgi:
            pgi.writelines(default_rules)
        self.load()
        

    def forcewrite(self):
        """Rewrite properly the file with the list in memory"""
        with open(self._path, encoding="utf-8", mode="w") as pgi:
            pgi.write("# File .pygnore up to date!\n")
            for typ, pattern in self.exc:
                pgi.write(f"> {typ} {pattern}\n")
            for typ, pattern in self.inc:
                pgi.write(f"< {typ} {pattern}\n")  
            
        
    def load(self):
        """load .pygnore and fill the include / exclude list"""
        self.inc=[]
        self.exc=[]
        with open(self._path,encoding="utf-8",mode="r")as pgi:
            for line in pgi:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts=line.split(maxsplit=2)
                if len(parts) < 3:
                    continue
                symbol, typ, pattern = parts
                if symbol == ">":
                    self.exc.append((typ, pattern))
                elif symbol == "<":
                    self.inc.append((typ, pattern))
        

    def set_path(self,path):
        """SETTER of the path of the file .pyignore"""
        self._path=path
        
    def get_path(self):
        """GETTER of the path of the file .pyignore"""
        return self._path
        
    def add_exclude(self,typ,pattern):
        """Add a exclude"""
        if (typ, pattern) not in self.exc:
            self.exc.append((typ, pattern))
            with open(self._path, "a", encoding="utf-8") as pgi:
                pgi.write(f"\n> {typ} {pattern}")
        self.load()

    def del_exclude(self,typ,pattern):
        """Delete an exclude"""
        if (typ, pattern) in self.exc:
            self.exc.remove((typ, pattern))
        self.forcewrite()
        self.load()
    
    def add_include(self,typ,pattern):
        """Add an include"""
        if (typ, pattern) not in self.inc:
            self.inc.append((typ, pattern))
            with open(self._path, "a", encoding="utf-8") as pgi:
                pgi.write(f"\n< {typ} {pattern}")
        self.load()

    def del_include(self,typ,pattern):
        """Delete an include"""
        if (typ, pattern) in self.inc:
            self.inc.remove((typ, pattern))
        self.forcewrite()
        self.load()
    

    
    def needtoInclude(self,name, is_dir=False):
        """Say if a folder/ file need to be included or not
        Priority: Include > Exclude >Default(Include)"""
        #1. Manage includes
        current_type="fo" if is_dir else "fi"
        for rule_type, pattern in self.inc:
            if rule_type==current_type:
                if fnmatch.fnmatch(name, pattern):
                    return True
        #2. Manage excludes
        for rule_type, pattern in self.exc:
            if rule_type==current_type:
                if fnmatch.fnmatch(name, pattern):
                    return False   
        #3. By default it's integrated
        return True
    
def get_ignore():
    """Returns a singleton of a pygnore instance
    It's the third singleton after 'set_computer()' and 'get_cfg()'
    
    Returns:
       pygnore: the shared  include/exclude manager
    """
    
    global _IGNORE_INSTANCE
    if _IGNORE_INSTANCE is None:
        _IGNORE_INSTANCE = pygnore()
    return _IGNORE_INSTANCE