import subprocess
from pathlib import Path
import platform
import xxhash
import time
import tempfile
import os
import sys
import re
from getpass import getuser
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

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
#     |        |---->portabilite.py (we are here)
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

# Portabilite.py is a program that aim to make the whole process anyOS compatible so in definition it will be by a class named computer wich takes only one parameter
# his self.os and maybe his self.sessionid wich will help us select a bunch of command to make Pygit compatible with Linux / Windows and Mac

class NullProgress():
    ""
    def __enter__(self):
        return self
    def __exit__(self,*exc):
        return False
    def add_task(self,description,total=None):
        return None
    def advance(self,task,advance=1):
        pass
    def update(self,task,completed=None,**kwargs):
        pass
def make_progress(description,computer=None):
    pc = computer if computer is not None else set_computer()
    if not pc.is_CLI():
        return NullProgress()
    safe = description.replace("{","{{").replace("}","}}")
    return Progress(
        SpinnerColumn(),TextColumn(safe),
        BarColumn(bar_width=30),TextColumn("[green]{task.percentage:3.0f}%")
    )


#==================================ZIP================================== 
_ZIP_LINE = re.compile(r"^\s*adding:\s+(.+?)\s+\((?:deflated|stored)")

def compute_hash(path,speed,verbose=False):
    """Compute the hash of a standard file in xxh32."""
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
def _dir_size(path):
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    total += _dir_size(entry.path) if entry.is_dir(follow_symlinks=False) else entry.stat().st_size
                except (PermissionError, FileNotFoundError):
                    continue
    except PermissionError:
        pass
    return total
    
    
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
            print(f"--- Test with a file of {file_size}")
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
                    print(f"File hash in {round(duration,3)}s to a speed of  {round(vitesse,1)}MB/s")
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
        print(f"--- Benchmark Ended ---")
        print(f"Optimized size is : {optimal_size} Bytes")
    return optimal_size
#==================================PORTABILITE==================================
_COMPUTER_INSTANCE=None

def run_command(cmd,cwd=None):
    try:
        result = subprocess.run(cmd, check=True,cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        return False
    
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
        
    return _COMPUTER_INSTANCE
    
        
class computer():
    
    #construct
    def __init__(self,uname,hostname):
        self._os= uname 
        self._sessionid=hostname
        self._optimal_speed=32
        self._mode="cli"  # "cli" ou "gui"
        

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
        self._optimal_speed=benchmark_optimal_chunk_size()
        return self._optimal_speed
    
    def get_app_root(self,parents=True):

        if getattr(sys,'frozen',False):
            if parents:
                BASE_DIR=Path(sys.executable).resolve().parent.parent
            else:
                BASE_DIR=Path(sys.executable).resolve().parent 
        else:
            if parents:
                BASE_DIR = Path(__file__).resolve().parent.parent
            else:
                BASE_DIR = Path(__file__).resolve().parent
        return BASE_DIR
    
    def is_CLI(self):
        """Renvoie True si le script est lancé dans un CLI"""
        return self._mode=="cli" and sys.stdout.isatty()
        
    def set_mode(self,mode):
        self._mode=mode
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
    def zip(self,src,dest,lvl=7,progress=None):
        """Zip a file

        Args:
            src (Path): Which folder/ file you want to compress
            dest (Path): where you wanna compress the file
            lvl (int, optional): Set the level of compression you want. Defaults to 7.

        Returns:
            boolean: if the compression succeed or not
        """
        import lang
        NO_COMPRESS_EXT = ".iso:.zip:.7z:.rar:.gz:.xz:.bz2:.mp4:.mkv:.avi:.jpg:.jpeg:.png:.webp:.mp3:.flac"
        src=Path(src)
        cmd=["zip","-r",f"-{lvl}","-n",NO_COMPRESS_EXT,str(dest),src.name]
        
        owned = progress is None
        if owned:
            progress=make_progress(lang.t("zip_compress",name=src.name),computer=self)
            progress.__enter__()
        total = _dir_size(src) if src.is_dir() else src.stat().st_size
        try:
            proc = subprocess.Popen(cmd, cwd=str(src.parent), stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1)
        except Exception:
            if owned:
                progress.__exit__(None,None,None)
            return False
        
        try:
            task = progress.add_task("compress", total=max(total, 1))
            for line in proc.stdout:
                m = _ZIP_LINE.match(line)
                if m:
                    fpath = src.parent / m.group(1)
                    try:
                        progress.advance(task, advance=fpath.stat().st_size)
                    except OSError:
                        pass
            proc.wait()
            progress.update(task, completed=total)
        finally:
            if owned:
                progress.__exit__(None,None,None)

        return proc.returncode == 0

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
    
    def zip(self, src, dest, lvl=7,progress=None):
        """Zip a file

        Args:
            src (Path): Which folder/ file you want to compress
            dest (Path): where you wanna compress the file
            lvl (int, optional): does nothing on Windows... (trust me...)

        Returns:
            boolean: if the compression succeed or not
        """
        import lang
        src, dest = Path(src), Path(dest)
        cmd = ["powershell", "-Command", "Compress-Archive", "-Path", str(src), "-DestinationPath", str(dest)]

        owned=progress is None
        if owned:
            progress = make_progress(lang.t("zip_compress",name=src.name),computer=self)
            progress.__enter__()

        total = _dir_size(src) if src.is_dir() else src.stat().st_size
        try:
            proc = subprocess.Popen(cmd)
        except Exception:
            if owned:
                progress.__exit__(None,None,None)
            return False

        try:
            task = progress.add_task("compress", total=max(total, 1))
            while proc.poll() is None:
                try:
                    current = dest.stat().st_size if dest.exists() else 0
                except OSError:
                    current = 0
                progress.update(task, completed=min(current, total * 0.99))
                time.sleep(0.3)
            progress.update(task, completed=total)
        finally:
            if owned:
                progress.__exit__(None,None,None)

        return proc.returncode == 0

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

    def zip(self,src,dest,lvl=7,progress=None):
            """Zip a file
    
            Args:
                src (Path): Which folder/ file you want to compress
                dest (Path): where you wanna compress the file
                lvl (int, optional): Set the level of compression you want. Defaults to 7.
    
            Returns:
                boolean: if the compression succeed or not
            """
            import lang
            owned=progress is None
            NO_COMPRESS_EXT = ".iso:.zip:.7z:.rar:.gz:.xz:.bz2:.mp4:.mkv:.avi:.jpg:.jpeg:.png:.webp:.mp3:.flac"
            src=Path(src)
            cmd=["zip","-r",f"-{lvl}","-n",NO_COMPRESS_EXT,str(dest),src.name]
            
            if owned:
                progress=make_progress(lang.t("zip_compress",name=src.name),computer=self)
                progress.__enter__()
            total = _dir_size(src) if src.is_dir() else src.stat().st_size
            try:
                proc = subprocess.Popen(cmd, cwd=str(src.parent), stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, text=True, bufsize=1)
            except Exception:
                if owned:
                    progress.__exit__(None,None,None)
                return False
    
            try:
                task = progress.add_task("compress", total=max(total, 1))
                for line in proc.stdout:
                    m = _ZIP_LINE.match(line)
                    if m:
                        fpath = src.parent / m.group(1)
                        try:
                            progress.advance(task, advance=fpath.stat().st_size)
                        except OSError:
                            pass
                proc.wait()
                progress.update(task, completed=total)
            finally:
                if owned:
                    progress.__exit__(None,None,None)
            return proc.returncode == 0
    

        
    def unzip(self,src,dest):
        """Unzip a file

        Args:
            src (Path): the ziped folder you want to unzip
            dest (Path): where you want to put the unziped folder

        Returns:
            boolean: if the compression succeed or not
        """
        return run_command(["unzip",f"{src}","-d",f"{dest}"])        
        
