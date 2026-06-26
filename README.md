Pygit

 ██████╗ ██╗   ██╗ ██████╗ ██╗████████╗
 ██╔══██╗╚██╗ ██╔╝██╔════╝ ██║╚══██╔══╝
 ██████╔╝ ╚████╔╝ ██║  ███╗██║   ██║
 ██╔═══╝   ╚██╔╝  ██║   ██║██║   ██║
 ██║        ██║   ╚██████╔╝██║   ██║
 ╚═╝        ╚═╝    ╚═════╝ ╚═╝   ╚═╝


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

pygit/
├── current_save/          # Most recent snapshot
│   ├── {date}.zip
│   └── jsontree.json      # Cached file tree for fast diff
├── old_save/              # Older snapshots (capped by MAX_OLD_SAVE)
│   └── {date}.zip
├── py/                    # Application source (can live anywhere)
│   ├── CLI.py             # Entry point — interactive command loop
│   ├── save.py            # Save, dry-run, and restore logic
│   ├── checksum.py        # File and folder integrity checking
│   ├── pathtree.py        # Unified tree builder (folder or zip)
│   ├── pygnore.py         # Include/exclude pattern manager
│   ├── configfile.py      # Persistent config loader/writer
│   ├── portabilite.py     # Cross-platform abstraction layer
│   ├── README.py          # README file reader/writer
│   ├── lang.py            # Translation loader
│   └── lang/              # Language files
│       ├── en.json
│       ├── fr.json
│       └── ...
├── .pygnore               # Ignore rules (similar to .gitignore)
└── .configfile            # Stored user configuration


# Getting Started
## Install dependencies:
```bash
pip install rich prompt_toolkit
```

## Running Pygit
```bash
cd pygit/py
python CLI.py
```
On first launch, Pygit will load your config and .pygnore settings, then drop you into the interactive prompt.

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

en · fr · es · de · it · pt · nl · pl · jap · zh · la · arr · om · qu · hex

Switch language at runtime with setlang.


## Version History

Version  Date          Notes  
A      13/04/2026    Initial release
B      27/04/2026    .pygnore management, basic CLI commands
C      06/05/2026    Persistent config file, pygnore and save commands
D      13/05/2026    Multilingual support, pathtree, checksum, readme commands


# Notes


This project is developed for personal and educational purposes as a Python interpretation of Git's core concepts.
A GUI version is planned but not yet developed.
The project is actively in development — contributions and feedback are welcome.

# An inspirational quote that make me launch the project
"Où finit la paresse, où commence la contemplation?" — Jean Dutourd
wich means "Where does laziness end, where does contemplation begin?"
