from portabilite import *
from pygnore import *
from pathlib import Path
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
#     |------>.config-file (and here...maybe)
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.





class configfile():
    def __init__(self):
        self.PC= set_computer()
        self.PC.set_optimal_speed()
        self.BASE_DIR=self.PC.get_app_root()
        self._path=f"{self.BASE_DIR}/.configfile"
        
        self.DIR=self.PC.get_app_root()
        self.WORKINGDIR=None
        self.MAX_OLD_SAVE=5
        self.LANG="en"
        
        if Path(self._path).exists():
            self.load()
        else:
            self.write()
    
    def load(self):
        with open(self._path,encoding="utf-8",mode="r")as conf:
            for lines in conf:
                lines=lines.strip()
                parts=lines.split("\t")
                if len(parts)==2:
                    key,value= parts
                    if key=="DIR":
                        self.DIR=value
                    if key=="WORKINGDIR":
                        self.WORKINGDIR=value
                    if key=="MAX_OLD_SAVE":
                        self.MAX_OLD_SAVE=int(value)
                    if key=="LANG":
                        self.LANG=value

    def write(self):
        env=[
            f"DIR\t{self.DIR}\n",
            f"WORKINGDIR\t{self.WORKINGDIR}\n",
            f"MAX_OLD_SAVE\t{self.MAX_OLD_SAVE}\n",
            f"LANG\t{self.LANG}\n"
        ]
        with open(self._path,encoding="utf-8",mode="w") as conf:
            conf.writelines(env)
            
    def get_abs(self,path):
        f"""A sublim method that gives you the absolute path. If not already it will use the {self.BASE_DIR} folder

        Args:
            path (string): A path that could be absolute nor 

        Returns:
            Path: the absolute path 
        """
        p=None
        if Path(path).is_absolute():
            p=Path(path)
        else:
            p=Path(self.BASE_DIR / path)
        
        if p.exists():
            return p
        else:
            return 404
    
    def getDIR(self):
        """Renvoie l'emplacement de l'application """
        return self.DIR
    
    def getLANG(self):
        """Renvoie la langue actuel"""
        return self.LANG
    
    def getWORKINGDIR(self):
        """Renvoie l'emplacement définit pour le workingdir"""
        return self.WORKINGDIR

    def setWORKINGDIR(self,pt):
        """Permet de définir le workingdir"""
        self.WORKINGDIR=self.get_abs(pt)
        self.write()
        
    def setDIR(self,pt):
        """Permet de définir l'emplacement des sauvegardes"""
        self.DIR=self.get_abs(pt)
        self.write()
    
    def setLANG(self, lang:str):
        """Permet de changer la langue de l'interface"""
        self.LANG=lang
        self.write()
        
        
 