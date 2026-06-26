import subprocess
from pathlib import Path
import platform
import xxhash
import time
import tempfile
import os
import sys
from getpass import getuser

#---------------------------------ARCHITECTURE OF PYGIT-----------------------------------------
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
#     |        |---->portabilite.py (we are here)
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

# Portabilite.py is a program that aim to make the whole process anyOS compatible so in definition it will be by a class named computer wich takes only one parameter
# his self.os and maybe his self.sessionid wich will help us select a bunch of command to make Pygit compatible with Linux / Windows and Mac

#==================================ZIP================================== 
def compute_hash(path,speed,verbose=False):
    """Calcule le hash d'un fichier standard."""
    if verbose:
        print(f"\tHash de {path} en cours...")
    hasher = xxhash.xxh32()
    try:
        buffer = bytearray(speed)
        view = memoryview(buffer)
        with open(path, 'rb',buffering=0) as md:
            while True:
                chunk=md.readinto(view)
                if chunk==0:
                    break
                hasher.update(view[:chunk])
        return hasher.hexdigest()
    except Exception:
        return 'Error'

    
    
def compute_zip_hash(stream):
    hasher=xxhash.xxh32()
    try:
            for chunk in iter(lambda: stream.read(8192),b""):
                hasher.update(chunk)
            return hasher.hexdigest()
    except Exception:
        return "Error"

def benchmark_optimal_chunk_size(verbose=False):
    chunk_sizes = [4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304, 8388608]
    test_files_mb = [10, 50, 100, 250]
    
    total_scores = {size: 0 for size in chunk_sizes}
    
    for file_size in test_files_mb:
        file_results = []
        if verbose:
            print(f"--- TEST avec un fichier de {file_size}")
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(os.urandom(1024 * 1024 * file_size))
            test_path = tmp.name
        try:
            for size in chunk_sizes:
                start = time.perf_counter()
                compute_hash(test_path, size)
                duration = time.perf_counter() - start
                vitesse = file_size / duration
                if verbose:
                    print(f"Fichier hasher en {round(duration,3)}s à une vitesse de {round(vitesse,1)}Mo/s")
                file_results.append((size, vitesse))
            
            file_results.sort(key=lambda x: x[1], reverse=True)
            
            for rank, (size, vitesse) in enumerate(file_results):
                points = len(chunk_sizes) - rank  # Le 1er gagne 12 pts, le dernier 1 pt
                total_scores[size] += points
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)
                
    optimal_size = max(total_scores, key=total_scores.get)
    if verbose:
        print(f"--- Benchmark terminé ---")
        print(f"Taille optimale sélectionnée : {optimal_size} octets")
    return optimal_size
#==================================PORTABILITE==================================
_COMPUTER_INSTANCE=None

def run_command(cmd,cwd=None):
    try:
        result = subprocess.run(cmd, check=True,cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        return e
    
def set_computer():
    global _COMPUTER_INSTANCE
    if _COMPUTER_INSTANCE is not None:
        return _COMPUTER_INSTANCE
    u=platform.uname()
    if u.system=="Linux":
        _COMPUTER_INSTANCE = Linux(u.system,getuser())
    elif u.system=="Windows":
        _COMPUTER_INSTANCE = Win(u.system,getuser())
    elif u.system=="Darwin":
        _COMPUTER_INSTANCE = Mac(u.system,getuser())
        
    if _COMPUTER_INSTANCE is not None:
        _COMPUTER_INSTANCE.set_optimal_speed()
    return _COMPUTER_INSTANCE
    
        
class computer():
    
    #construct
    def __init__(self,uname,hostname):
        self._os= uname 
        self._sessionid=hostname
        self._optimal_speed=32
        

    #====================================================================
    #========================= COMPATIBLE METHOD ========================
    #====================================================================
    def get_optimal_speed(self):
        return self._optimal_speed
    
    def get_os(self):
        return self._os
    
    def get_sessionid(self):
        return self._sessionid
    
    def set_optimal_speed(self):
        if self._optimal_speed != 32:
            return self._optimal_speed
        OPSPEED=benchmark_optimal_chunk_size()
        self._optimal_speed=OPSPEED
        return OPSPEED
    
    def get_app_root(self):

        if getattr(sys,'frozen',False):
            BASE_DIR=Path(sys.executable).resolve().parent.parent
        else:
            BASE_DIR = Path(__file__).resolve().parent.parent
        return BASE_DIR
    def is_CLI(self):
        """Renvoie True si le script est lancé dans un CLI"""
        return sys.stdout.isatty()
        
#============================================================================================================================================================  
#=========================================================================Classe Linux=======================================================================
#============================================================================================================================================================ 
        
class Linux(computer):

    #====================================================================
    #============================ DIR METHOD ============================
    #====================================================================
    def ls_dir(self,dir):
        output=subprocess.run(["ls","-a",dir],text=True,capture_output=True)
        res=output.stdout.split("\n")
        result=[]
        for f in res:
            if f:
                result.append(f)
        return result
    
    def current_directory(self):
        self.cd=Path.cwd()
        return self.cd
    
    def set_cd(self,current):
        self.cd=Path(current)
        return True
        
    def mv_dir(self,dir,dest):
        """move a file Careful to handle with respect

        Args:
            dir (path): the directory you want to move
            dest (path): where you want to move it 

        Returns:
            boolean: the command succeed or not 
        """
        return run_command(["mv",dir,dest])

    def rm_dir(self,dir):
        """remove a file Careful to handle with respect

        Args:
            dir (path): the directory you want to delete

        Returns:
            boolean: the command succeed or not 
        """
        return run_command(["rm",'-f',dir])
    
    def get_mountpoint(self):
        """Get if there is a mountpoint on computer

        Returns:
            array: An array of the mountpoint /path existing to the folders
        """
        self.mountpoint=[]
        output=subprocess.run(["lsblk","-nlo","NAME,HOTPLUG,MOUNTPOINT"],text=True,capture_output=True).stdout
        
        #treatment
        name_list=[]
        for line in output.splitlines():
            parts=line.split()
            if parts[1]=='1' and len(parts)>=3:
                name=parts[2]
                if len(parts)>3:
                    for namepart in parts[3:]:
                        name=name+" "+namepart
                name_list.append(name)
        return name_list
    #====================================================================
    #============================ ZIP METHOD ============================
    #====================================================================
    def zip(self,src,dest,lvl=7):
        """Zip a file

        Args:
            src (Path): Which folder/ file you want to compress
            dest (Path): where you wanna compress the file
            lvl (int, optional): Set the level of compression you want. Defaults to 7.

        Returns:
            boolean: if the compression succeed or not
        """
        src=Path(src)
        return run_command(["zip","-r",f"-{lvl}",str(dest),src.name],cwd=str(src.parent))
        
    def unzip(self,src,dest):
        """Unzip a file

        Args:
            src (Path): the ziped folder you want to unzip
            dest (Path): where you want to put the unziped folder

        Returns:
            boolean: if the compression succeed or not
        """
        return run_command(["unzip",f"{src}","-d",f"{dest}"])
        
    
                
#============================================================================================================================================================  
#=========================================================================Classe Win=========================================================================
#============================================================================================================================================================  
class Win(computer):
    
    #====================================================================
    #============================ DIR METHOD ============================
    #====================================================================
    
    def current_directory(self):
        self.cd=Path.cwd()
        return self.cd
    
    def get_mountpoint(self):
        return "Not Implemented Yet"
    
    def mv_dir(self,src,dest):
        """move a file Careful to handle with respect

        Args:
            src (path): the directory you want to move
            dest (path): where you want to move it 

        Returns:
            boolean: the command succeed or not 
        """
        return run_command(["powershell","-Command","Move-Item","-Path",src,"-Destination",dest])
    
    def rm_dir(self,file):
        """remove a file Careful to handle with respect

        Args:
            file (path): the directory you want to delete

        Returns:
            boolean: the command succeed or not 
        """
        return run_command(["powershell","-Command","Remove-Item","-Path",file,"-Force"])
    
    def ls_dir(self,dir):
        output=subprocess.run(["powershell","-Command","Get-ChildItem",dir,"-Name","-Force"],text=True,capture_output=True)
        res=output.stdout.split("\n")
        result=[]
        for f in res:
            f=f.strip()
            if f:
                result.append(f)
        return result
    
    
    #====================================================================
    #============================ ZIP METHOD ============================
    #====================================================================
    
    def zip(self,src,dest,lvl=7):
        """Zip a file

        Args:
            src (Path): Which folder/ file you want to compress
            dest (Path): where you wanna compress the file
            lvl (int, optional): does nothing on Windows... (trust me...)

        Returns:
            boolean: if the compression succeed or not
        """
        return run_command(["powershell","-Command","Compress-Archive","-Path",f"{src}","-DestinationPath",f"{dest}"])

    def unzip(self,src,dest):
        """Unzip a file

        Args:
            src (Path): the ziped folder you want to unzip
            dest (Path): where you want to put the unziped folder
            force (boolean): If you want to overwrite existing file or not .Default set to True

        Returns:
            boolean: if the compression succeed or not
        """
        return run_command(["powershell","-Command","Expand-Archive","-LiteralPath",f"{src}","-DestinationPath",f"{dest}","-Force"])

            
    

    
#============================================================================================================================================================  
#=========================================================================Classe MAC=========================================================================
#============================================================================================================================================================  

class Mac(computer):
    
    #====================================================================
    #============================ DIR METHOD ============================
    #====================================================================
    
    def current_directory(self):
        self.cd=Path.cwd()
        return self.cd
    
    def get_mountpoint(self):
        return "Not Implemented Yet"
    
    def mv_dir(self,dir,dest):
        """move a file Careful to handle with respect

        Args:
            dir (path): the directory you want to move
            dest (path): where you want to move it 

        Returns:
            boolean: the command succeed or not 
        """
        return run_command(["mv",dir,dest])

    def rm_dir(self,dir):
        """remove a file Careful to handle with respect

        Args:
            dir (path): the directory you want to delete

        Returns:
            boolean: the command succeed or not 
        """
        return run_command(["rm",'-R',dir])
    
    def ls_dir(self,dir):
        output=subprocess.run(["ls","-a",dir],text=True,capture_output=True)
        res=output.stdout.split("\n")
        result=[]
        for f in res:
            if f:
                result.append(f)
        return result
    #====================================================================
    #============================ ZIP METHOD ============================
    #====================================================================

    def zip(self,src,dest,lvl=7):
        """Zip a file

        Args:
            src (Path): Which folder/ file you want to compress
            dest (Path): where you wanna compress the file
            lvl (int, optional): Set the level of compression you want. Defaults to 7.

        Returns:
            boolean: if the compression succeed or not
        """
        src=Path(src)
        return run_command(["zip","-r",f"-{lvl}",str(dest),src.name],cwd=str(src.parent))

        
    def unzip(self,src,dest):
        """Unzip a file

        Args:
            src (Path): the ziped folder you want to unzip
            dest (Path): where you want to put the unziped folder

        Returns:
            boolean: if the compression succeed or not
        """
        return run_command(["unzip",f"{src}","-d",f"{dest}"])        
        
