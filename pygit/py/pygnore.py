from pathlib import Path
from portabilite import *
import fnmatch
COMPUTER = set_computer()
BASE_DIR = COMPUTER.get_app_root()

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
#     |        |---->README.py
#     |        |---->portabilite.py
#     |        |---->pygnore.py(we are here)
#     |        |---->configfile.py
#     |        |---->CLI.py
#     |
#     |------> README.txt
#     |------>.pygnore(and here... maybe)
#     |------>.config-file
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.

# Ici on va attaquer le chantier de .pygnore

class pygnore():
    
    def __init__(self):
        self._path=BASE_DIR #le pyignore sera toujours recherché à la base du projet à moins d'un set demandé par l'utilisateur
        #pygnore constructor under here |
        self._path=f"{BASE_DIR}/.pygnore"
        self.inc=[]
        self.exc=[]
        if Path(self._path).exists():
            self.load()
        else:
            self._create_default()


    def _create_default(self):
        """Crée le fichier par défaut et charge les règles"""
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
        """Réécrit proprement le fichier à partir des listes en mémoire"""
        with open(self._path, encoding="utf-8", mode="w") as pgi:
            pgi.write("# Fichier .pygnore mis à jour\n")
            for typ, pattern in self.exc:
                pgi.write(f"> {typ} {pattern}\n")
            for typ, pattern in self.inc:
                pgi.write(f"< {typ} {pattern}\n")  
            
        
    def load(self):
        """Charge le .pygnore et remplit les listes d'exclude et d'include"""
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
        """SETTER du path du fichier .pyignore"""
        self._path=path
        
    def get_path(self):
        """GETTER du path du fichier .pyignore"""
        return self._path
        
    def add_exclude(self,typ,pattern):
        """Ajoute un exclude"""
        if (typ, pattern) not in self.exc:
            self.exc.append((typ, pattern))
            with open(self._path, "a", encoding="utf-8") as pgi:
                pgi.write(f"\n> {typ} {pattern}")
        self.load()

    def del_exclude(self,typ,pattern):
        if (typ, pattern) in self.exc:
            self.exc.remove((typ, pattern))
        self.forcewrite()
        self.load()
    
    def add_include(self,typ,pattern):
        """Ajoute un include"""
        if (typ, pattern) not in self.inc:
            self.inc.append((typ, pattern))
            with open(self._path, "a", encoding="utf-8") as pgi:
                pgi.write(f"\n< {typ} {pattern}")
        self.load()

    def del_include(self,typ,pattern):
        if (typ, pattern) in self.inc:
            self.inc.remove((typ, pattern))
        self.forcewrite()
        self.load()
    

    
    def needtoInclude(self,name, is_dir=False):
        """Détermine si un fichier/dossier doit être traité
        Priorité: Include > Exclude >Default(Include)"""
        #1. On gère les includes
        current_type="fo" if is_dir else "fi"
        for rule_type, pattern in self.inc:
            if rule_type==current_type:
                if fnmatch.fnmatch(name, pattern):
                    return True
        #2. On gère les excludes
        for rule_type, pattern in self.exc:
            if rule_type==current_type:
                if fnmatch.fnmatch(name, pattern):
                    return False   
        #3. Par défaut on intègre
        return True