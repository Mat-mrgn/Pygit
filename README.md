Pygit
```
 ██████╗ ██╗   ██╗ ██████╗ ██╗████████╗ 
 ██╔══██╗╚██╗ ██╔╝██╔════╝ ██║╚══██╔══╝ 
 ██████╔╝ ╚████╔╝ ██║  ███╗██║   ██║ 
 ██╔═══╝   ╚██╔╝  ██║   ██║██║   ██║ 
 ██║        ██║   ╚██████╔╝██║   ██║ 
 ╚═╝        ╚═╝    ╚═════╝ ╚═╝   ╚═╝ 
```

── local save manager · inspired by git ──



A personal, Python-based local file backup manager inspired by Git. Pygit lets you save, compare, and restore snapshots of any folder on your machine — entirely offline, with a clean interactive CLI powered by Rich.

# Features
- **Save** Create a timestamped `.zip` snapshot of any working directory
- **Dry-run** preview what has changed (created, modified, moved, deleted) before committing a save
- **Restore** unzip any snapshot (current or older) back to a target folder
- **Integrity check1** SHA-based checksum comparison between saves and source to detect corruption
- **Pygnore** a .pygnore file (analogous to .gitignore) to include/exclude files and folders by pattern
- **Tree inspection** explore the file tree of any folder or .zip archive
- **Multilingual interface** supports 15+ languages (English, French, Spanish, German, Italian, Portuguese, Dutch, Polish, Japanese, Chinese, Latin, and more)
- **Persistent config** save path, working directory, and max old-saves limit are stored in a .configfile
- **Command history** CLI remembers your previous commands across sessions

# Project Structure
```
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
#     |        |---->manifest.py
#     |        |---->GUI_engine.py
#     |        |---->GUI.py (we are here)
#     |
#     |------> README.txt
#     |------>.pygnore
#     |------>.config-file
```

# Getting Started
## Install dependencies in the py folder:
```bash
pip install -r requirements.txt
```

## Running Pygit
```bash
cd pygit/py
python CLI.py
```
On first launch, Pygit will load a default config and .pygnore settings, then drop you into the interactive prompt.

press Enter or help to get all the commands.

## Pygnore

Pygit ships with a default .pygnore that excludes common noise:
```
> fo __pycache__
> fo .git
> fi *.DS_Store
> fi desktop.ini
> fo .venv
> fo env
```
- Lines starting with > are excludes, < are includes
- fo targets folders, fi targets files
- Patterns support wildcards (e.g. *.log, temp_*)

## Supported Languages

de · en · es · fr · id · it · jap · ko · la · nl · pl · pt · qu · ru · tr · vi · arr · hex

Switch language at runtime with setlang.

For most of the langages, it is done by the help of AI because I'm not familiar with every langages but I want it as accessible for everyone as possible... 
Some langages were reviewed by native speaker (French, English, Deutsch) but still some errors could be in.
## Version History

Version  Date          Notes  
A      13/04/2026    Initial release
B      27/04/2026    .pygnore management, basic CLI commands
C      06/05/2026    Persistent config file, pygnore and save commands
D      13/05/2026    Multilingual support, pathtree, checksum, readme commands and other commands. Multilingual support extended to all PyGit commands and even inside the program internals
E      25/08/2026    CLI fully functionable, more langages and the start of the GUI interface. There is no a manifest and the save is done differently to provide more saves capability management.


# Notes


This project is developed for personal and educational purposes as a Python interpretation of Git's core concepts.
A GUI version is planned but not yet developed.
The project is actively in development — contributions and feedback are welcome.

# An inspirational quote that make me launch the project
"Où finit la paresse, où commence la contemplation?" — Jean Dutourd
wich means "Where does laziness end, where does contemplation begin?"
