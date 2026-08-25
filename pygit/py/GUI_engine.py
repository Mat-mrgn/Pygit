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
#     |        |---->GUI_engine.py (we are here)
#     |        |---->GUI.py 
#     |
#     |------> README.txt
#     |------>.pygnore
#     |------>.config-file
#                                       This architecture does not care of a specific environment
#                                       because everything that is outside this architecture work
#                                       With absolute Path.

import threading
#==================================================================================
#=================================== Statiques ====================================
#==================================================================================
_QUESTIONS = []
_AUTO  = []
_BAILOUT = []
MAX_RETRY = 5
BEFAULT_BAILOUT='exit'


# ETAT
waiting = 0
running= 1
done = 2
failed = 3
#==================================================================================
#====================================== Job =======================================
#==================================================================================

class Job:
    pass
    def __init__(self,id,kind):
        self.id=id
        self.kind=kind
        self._lock=threading.Lock
        self._state=waiting
        self._lines = list
        self._event = threading.Event
        self._question = None
        self._answer = ""
        self._preset = {}
        self._asked = 0
        self._tasks = {}
        self._result = None
        self._next_task=0
        
        
    def __enter__(self):
        pass
    
    def __exit__(self,*exc):
        return False
    
    def add_task(self,description,total=None):
        #empile et renvoie un identifiant
        pass
    
    def advance(self,task,advance=1):
        #ne pas verouiller (lock)
        pass
    
    def update(self,task,completed=None,**kwargs):
        
        pass

#==================================================================================
#===================================== Engine =====================================
#==================================================================================

class Engine:
    pass


#==================================================================================
#================================= _normalize_*() =================================
#================================================================================== 
def _normalize_():
    pass



#==================================================================================
#=========================== LISTE DES COMMANDES UTILES ===========================
#==================================================================================
#   _________________
#   |               |
#   |      HELP     | sont des commandes dites "boutons" disponibles à tout moment
#   |  QUIT - EXIT  | Help renvoi l'aide de la page actuelle, about les informations de l'app
#   |     ABOUT     | Quit la fameuse croix en haut à droite de la fenêtre
#   |_______________| 
#
# PARAMETRES DE SAUVEGARDES
#   _________*__________
#   |                  |
#   |  DIR   -   WDIR  | DIR et WDIR ne sont pas des commandes le résultat est directement affiché
#   |                  | SETDIR et SETWDIR provoquent un changement et sont disponibles dans les paramètres de sauvegardes
#   | SETDIR - SETWDIR | Dans les paramètres de sauvegardes on retrouvera tout ceux avec une * en haut de la boite ASCII
#   |__________________|
#
#   _________*__________
#   |                  |
#   | exclude  include | Mention honorable aux showinc et showexc qui ne sont pas marqués puisque ils seront par défaut afficher 
#   |   add      add   | Add et Del devront représenter deux petits boutons en bas des menus d'affichages des includes et excludes
#   |   del      del   | Need to Include sera sur une barre avec à côté un espace "explorateur de fichier" ou l'on pourra sélectionner un fichier à analyser
#   |   needtoinclude  |
#   |__________________|
#
#   _________*__________
#   |                  |
#   | setsimthreshold  | Manifest: Les getsimthreshold et listsaves ne sont pas disponibles car affiché par défaut. 
#   | unlinksave       |
#   |                  | Le unlink save sera disponible un peu comme un sélecteur. Un arbre présente toutes les saves différentes et leur liens,
#   |                  | Via le sélecteur on peut un unlink de 1 à plusieurs? En les sélectionnant puis appuyer sur le bouton "unlink"
#   |                  |
#   |__________________|
#
#   PARAMETRES GENERAUX
#   _________#__________
#   |                  |
#   |      setlang     | getlang est affiché par défaut setlang permet de modifier la langue.
#   |__________________|
#
#   _________#__________
#   |                  |
#   |     maxoldsave   | La possibilité de changer le nombre de save maximale que l'on garde en arrière
#   |     OPT_SPEED    | La possibilité de recalculer la vitesse optimale de hash
#   |     Computer     | La possibilité de changer d'ordinateur. Et donc de demander à recalculer la compatibilité ^^
#   |__________________|
#
#      SAVE
#
#   _________O__________
#   |                  |
#   |      SAVE        | Lancer une sauvegarde (un peu le but de l'app)
#   |      RESTORE     | Restaurer une sauvegarde
#   |      DRYRUN      | Réaliser une "dryrun" afin de vérifier les modifications potentielles
#   |    READDRYRUN    | Lire le résultat de la dernière dryrun (redirige vers une nouvelle "page" fermable)
#   |    READREADME    | "           "             "     sauvegarde   "    "      "            "         "
#   |__________________|
#