from portabilite import set_computer
from pygnore import *
from pathlib import Path
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
#     |        |---->checksum.py (we are here)
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
#     |------>.config-file (and here...maybe)
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.


_CONFIG_INSTANCE= None


class configfile():
    def __init__(self):
        self.PC= set_computer()
        self.BASE_DIR=self.PC.get_app_root()
        self._path=f"{self.BASE_DIR}/.configfile"
        self.DIR=self.PC.get_app_root()
        self.WORKINGDIR=None
        self.MAX_OLD_SAVE=5
        self.LANG="en"
        self.OPT_SPEED=-0xC4FE
        self.SIM_THRESHOLD=45
        self.THEME="minimal"
        self.ACCENT=""
        
        
        if Path(self._path).exists():
            self.load()
        else:
            self.OPT_SPEED=self.PC.set_optimal_speed()
            self.write()
        if self.OPT_SPEED==-0xC4FE:
            self.OPT_SPEED=self.PC.set_optimal_speed()
        self.PC._optimal_speed=self.OPT_SPEED
    
    def load(self):
        with open(self._path,encoding="utf-8",mode="r")as conf:
            for lines in conf:
                lines=lines.strip()
                parts=lines.split("\t")
                if len(parts)==2:
                    key,value= parts
                    if key=="DIR":
                        if value not in ("None","","404"):
                            self.DIR=value
                    if key=="WORKINGDIR":
                        self.WORKINGDIR=value if value not in ("None","","404") else None
                    if key=="MAX_OLD_SAVE":
                        self.MAX_OLD_SAVE=int(value)
                    if key=="LANG":
                        self.LANG=value
                    if key=="OPT_SPEED":
                        self.OPT_SPEED=int(value)
                    if key=="SIM_THRESHOLD":
                        self.SIM_THRESHOLD=int(value)
                    if key=="THEME":
                        self.THEME=value if value not in ("None","") else "minimal"
                    if key=="ACCENT":
                        self.ACCENT="" if value in ("None","") else value

    def write(self):
        env=[
            f"DIR\t{self.DIR}\n",
            f"WORKINGDIR\t{self.WORKINGDIR}\n",
            f"MAX_OLD_SAVE\t{self.MAX_OLD_SAVE}\n",
            f"LANG\t{self.LANG}\n",
            f"OPT_SPEED\t{self.OPT_SPEED}\n",
            f"SIM_THRESHOLD\t{self.SIM_THRESHOLD}\n",
            f"THEME\t{self.THEME}\n",
            f"ACCENT\t{self.ACCENT}\n"
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
    def get_SIMThreshold(self):
        return self.SIM_THRESHOLD
    
    def get_OPT_speed(self):
        return self.OPT_SPEED
    
    def getDIR(self):
        """Return app location """
        return self.DIR
    
    def getMOS(self):
        """Return the MAX_OLD_SAVE"""
        return self.MAX_OLD_SAVE
    
    def getLANG(self):
        """Return current lang"""
        return self.LANG
    
    def getWORKINGDIR(self):
        """Return the workingdir location"""
        return self.WORKINGDIR
    
    def getTHEME(self):
        """Return the stylesheet name, without path nor extension"""
        return self.THEME
    
    def getACCENT(self):
        """Return the user accent as #rrggbb """
        return self.ACCENT

    def setWORKINGDIR(self,pt):
        """Set the workingdir location"""
        p=self.get_abs(pt)
        if p==404:
            return False
        self.WORKINGDIR=p
        self.write()
        return True        
    def setDIR(self,pt):
        """Set saves location"""
        p=self.get_abs(pt)
        if p==404:
            return False
        self.DIR=p
        self.write()
        return True
    
    def setLANG(self, lang:str):
        """Set a different lang"""
        self.LANG=lang
        self.write()
        return True
    
    def setMOS(self,MaxOld:int):
        """Set the MaxOldSave"""
        try:
            value=int(MaxOld)
        except(TypeError,ValueError):
            return False
        if value<1:
            return False
        self.MAX_OLD_SAVE=value
        self.write()
        return True
        
    def setSIMThreshold(self,Threshold:int):
        try:
            value=int(Threshold)
        except(TypeError,ValueError):
            return False
        if value<1 or value>100:
            return False
        self.SIM_THRESHOLD=value
        self.write()
        return True
    
    def setOPTspeed(self,speed):
        self.OPT_SPEED = speed
        self.PC._optimal_speed=speed
        self.write()
        
    def setTHEME(self,theme:str):
        name=str(theme).strip()
        if not name or not name.replace("_","-").replace("-","").isalnum():
            return False
        self.THEME=name
        self.write()
        return True
    
    def setACCENT(self,accent:str):
            value=str(accent).strip()
            if value =="":
                self.ACCENT=""
                self.write()
                return True
            if len(value)!=7 or value[0]!="#":
                return False
            try:
                int(value[1:],16)
            except ValueError:
                return False
            self.ACCENT=value.lower()
            self.write()
            return True
        
def get_cfg():
    """Returns the configfile instance in the running process
    Mirrors `set_computer` 
    
    
    Returns: 
      configfile: the shared configuration object
    """
    
    global _CONFIG_INSTANCE
    if _CONFIG_INSTANCE is None:
        _CONFIG_INSTANCE=configfile()
    return _CONFIG_INSTANCE