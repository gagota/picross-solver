# Le but de se programme est de coder la grille, les numéros d'indication, et de créer automatiquement les numéros à partir d'une grille coloriée
import numpy as np
import tkinter as tk
import tkinter.font as tkfont
import sys
from enum import Enum

# ---------------------------------------------------
# -------------------- VARIABLES --------------------
# ---------------------------------------------------

# ---------- Enum ----------
class State(Enum) :
    SEARCHING = 0
    SOLVED = 1
    ERROR = 2

# ---------- Paramètres ----------
gridSize = (15,15)
winSize = (1600,800)
showTkinter = True
showProbas = False

# ---------- Grids ----------
np.random.seed(1)
grid = np.random.randint(0,2,gridSize)
solutionGrid = np.zeros(gridSize)

# ---------- Tkinter ----------
# Model grid
gridDrawSize = (min(winSize) / 2, min(winSize) / 2)
gridPos = (gridDrawSize[0]/2, gridDrawSize[1]/2)
# Solution grid
solGridDrawSize = gridDrawSize
solGridPos = (solGridDrawSize[0]*5/2, solGridDrawSize[1]/2)

# ----------- Infos -----------
colGuideNumbers = [] # Numéros d'indication en haut de la grille
linGuideNumbers = [] # Même chose sur le côté
pauseMod = True # indique si on doit attendre une action de l'utilisateur à chaque boucle
pause = False # utilisé pour savoir quand l'utilisateur indique qu'il faut continuer
currentProbas = np.zeros(gridSize) # Grille des probas courantes
# Probas
linFillProbas = np.zeros(gridSize)
linCrossProbas = np.zeros(gridSize)
colFillProbas = np.zeros(gridSize)
colCrossProbas = np.zeros(gridSize)
fillProbas = np.zeros(gridSize)
crossProbas = np.zeros(gridSize)



# --------------------------------------------------
# -------------------- METHODES --------------------
# --------------------------------------------------

# ---------- Recherche des nombres d'indication ----------
def findNumbers(grid, gridSize) :
    linGuideNumbers = []
    colGuideNumbers = []
    # On commence par parcourir les lignes
    for i in range(gridSize[0]) :
        line = grid[i,:].ravel()
        linGuideNumbers.append(findNumbersFromLine(line))
    # Puis les colonnes
    for j in range(gridSize[1]) :
        line = grid[:,j].ravel()
        colGuideNumbers.append(findNumbersFromLine(line))
    
    return linGuideNumbers, colGuideNumbers

def findNumbersFromLine(line) :
    chunk  = 0 # désigne le nombre de cases qu'il y a à la suite dans la série
    currentList = [] # liste de nombres d'indication pour cette ligne, qui sera ajouté à linGuideNumbers ou colGuideNumbers une fois complété
    for j in range(gridSize[1]) :
        if line[j] == 1 : # si la case est remplie
            # on ajoute 1 case remplie au compteur
            chunk += 1
        elif chunk > 0 :
            # On ajoute le chunk à la liste
            currentList.append(chunk)
            # On reset le compteur
            chunk = 0
    # Si le dernier chunk n'a pas été validé à la sortie de la boucle, on la valide mtn
    if chunk > 0 :
        currentList.append(chunk)
    # On peut enfin retourner le résultat
    return currentList


# ---------- Résolution ----------
def Solve(linGuideNumbers, colGuideNumbers, gridSize) :
    global currentProbas
    solutionGrid = np.zeros(gridSize)
    # We enter into the first layer of assumption
    # Here the assumption is that our guide numbers can give a solution
    
    error, solutionGrid = Assumption(0, solutionGrid, linGuideNumbers, colGuideNumbers, gridSize)
    
    if error == State.ERROR :
        print("les nombre sont pas bons ou alors c'est le programme qui est pas bon")
        return solutionGrid
    else :
        print("Solved !")
        ShowStep(solutionGrid)
        return solutionGrid

def Assumption(layer, currentSolGrid, linGuideNumbers, colGuideNumbers, gridSize) : # Renvoie state, solutionGrid
    print("entering assumption at layer :", layer)
    
    global currentProbas
    state = State.SEARCHING
    
    # Boucle principale
    while state == State.SEARCHING :
        print("nouvelle itération à la couche :", layer)
        print("currentSolGrid :\n", currentSolGrid)
        
        # We show the result at runtime
        if showTkinter :
            ShowStep(currentSolGrid)
        
        # We pause if pauseMod is activated
        if pauseMod :
            Pause()
    
        # On calcule les probas pour les lignes et les colonnes
        # On s'assure au passage qu'il n'y a aucune erreur de trouvée
        print("Calcul probas")
        errorLin, thingsLinProbas = FindProbas(linGuideNumbers.copy(), currentSolGrid, axis = 0)
        errorCol, thingsColProbas = FindProbas(colGuideNumbers.copy(), currentSolGrid, axis = 1)
        
        
        # S'il y a une erreur de trouvée, on arrête tout et on remonte l'info
        if errorLin | errorCol :
            print("Erreur trouvée")
            return State.ERROR, None
            '''
            Normalement ça devrait suffir pour détecter les contradictions, mais j'en suis pas complètement sûr
            '''
        else : # Pas d'erreur, on peut continuer
            print("Pas d'erreur")
            # On stock les probas trouvées dans les variables correspondantes
            linFillProbas, linCrossProbas = thingsLinProbas
            colFillProbas, colCrossProbas = thingsColProbas
            
            print("linFillProbas :\n", linFillProbas)
            print("linCrossProbas :\n", linCrossProbas)
            
            # On commence par essayer de placer des trucs sûrs
            print("placement trucs sûrs")
            hadPlacedThings, currentSolGrid, thingsChanged = PlaceSure(linFillProbas, colFillProbas, linCrossProbas, colCrossProbas, currentSolGrid)
            
            # Si on a rien réussi à placer aver certitude, on entre dans une nouvelle supposition
            if not hadPlacedThings :
                print("Rien placé avec certitude")
                fillProbas = (linFillProbas + colFillProbas) /2
                crossProbas = (linCrossProbas + colCrossProbas) /2
                print("Nouvelle Supposition")
                newState, currentSolGrid = StartNewAssumption(layer+1, np.copy(currentSolGrid), linGuideNumbers, colGuideNumbers,
                                   gridSize, fillProbas, crossProbas)                
                
                # On vérifie si la grille a été résolue après cette supposition
                if newState == State.SOLVED :
                    print("La grille a été résolue")
                    return State.SOLVED, currentSolGrid
            
            ''' 
            Après avoir placé des trucs, il est temps de vérifier si on a résolu la grille
            '''
            if CheckSolved(linFillProbas, colFillProbas, linCrossProbas, colCrossProbas, currentSolGrid) :
                return State.SOLVED, currentSolGrid
    return state, currentSolGrid

def CheckSolved(linFillProbas, colFillProbas, linCrossProbas, colCrossProbas, currentSolGrid) :
    '''
    Le but va être de voir si on a placé les bons trucs là où la proba = 1
    et que la grille est bien remplie comme ta
    '''
    
    #print("CheckSolved()")
    
    fillCompletionMask = ((linFillProbas == 1) | (colFillProbas == 1)) & (currentSolGrid == 1)
    crossCompletionMask = ((linCrossProbas == 1) | (colCrossProbas == 1)) & (currentSolGrid == 2)
    completionMask = fillCompletionMask | crossCompletionMask
    
    solved = np.all(completionMask)
    
    return solved

def StartNewAssumption(layer, currentSolGrid, linGuideNumbers, colGuideNumbers, gridSize, fillProbas, crossProbas) :
    '''
    Renvoie : state, newGrid
    '''
    print("StartNewAsumption()")
    
    # On commence par enlever toutes les probas là où il y a déjà un truc de placé
    fillProbas[currentSolGrid != 0] = 0
    crossProbas[currentSolGrid != 0] = 0
    
    # La supposition qu'on va faire est là où il y a la plus forte proba sur la grille
    fillAssumptionPos = np.unravel_index(np.argmax(fillProbas), fillProbas.shape)
    crossAssumptionPos = np.unravel_index(np.argmax(crossProbas), crossProbas.shape)
    
    # si la proba de fill est plus grande que la proba de cross, la supposition sera un fill
    if fillProbas[fillAssumptionPos] > crossProbas[crossAssumptionPos] :
        assumption = 1
        assumptionPos = fillAssumptionPos
        print("On va remplir à :", fillAssumptionPos)
    # Sinon cross
    else :
        assumption = 2
        assumptionPos = crossAssumptionPos
        print("On va placer une croix à :", crossAssumptionPos)
    print("grid before assumption :\n", currentSolGrid)
    currentSolGrid[assumptionPos] = assumption
    print("grid after assumption :\n", currentSolGrid)
    
    Pause()
    
    state, solvedGrid = Assumption(layer, currentSolGrid, linGuideNumbers.copy(), colGuideNumbers.copy(), gridSize)
    
    # Si la cette supposition a mené à une contradiction,
    # on sait donc mtn que c'est l'inverse de la supposition à cet endroit
    if state == State.ERROR :
        if assumption == 1 :
            currentSolGrid[assumptionPos] = 2
        else :
            currentSolGrid[assumptionPos] = 1
        return State.ERROR, currentSolGrid
    # Si ça a mené à une bonne solution, on a résolu l'affaire
    else : # state == State.SOLVED
        return State.SOLVED, solvedGrid
    
def CheckError(currentSolGrid, linesChanged, colsChanged) :
    '''
    Ca va fonctionner globalement très similairement à FindPossibilities,
    sauf que là on va revenir en arrière dès qu'une possibilité a été trouvée
    '''

def PlaceSure(linFillProbas, colFillProbas, linCrossProbas, colCrossProbas, currentSolGrid) : # Renvoie hadPlacedThings, newSolGrid, (linesChanged, colsChanged)
    # On crée des masks avec true là où proba = 1
    fillMask = ((linFillProbas == 1) | (colFillProbas == 1)) & (currentSolGrid == 0)
    crossMask = ((linCrossProbas == 1) | (colCrossProbas == 1)) & (currentSolGrid == 0)
    
    # S'il y a des trucs sûrs, on les places et on remonte l'information qu'on a réussi à en placer
    if np.any(fillMask) | np.any(crossMask) :
        currentSolGrid[fillMask] = 1
        currentSolGrid[crossMask] = 2
        
        linesChanged, colsChanged = np.where(fillMask | crossMask)
        
        return True, currentSolGrid, (linesChanged, colsChanged)
    else :
        return False, currentSolGrid, None


def FindProbas(guideNumbers, currentSolGrid, axis) : # Renvoie error, (fillProbas, crossProbas)
    #print("FindProbas()")
    '''
    Le but de cette méthode est de renvoyer 2 grilles de probabilité.
    Chaque grille correspond aux probabilités de remplissage et de croix,
    par rapport aux guide numbers de colonne OU de ligne (selon l'axis).
    La méthode renvoie l'information de si une erreur a été trouvé
    et la grille si aucune erreur a été trouvée.
    '''
    
    # On va appeler pour chaque ligne ou chaque colonne la méthode "FindProbasInLine"
    # Et regrouper les résultats de chaque appel dans les 2 grilles
    fillProbas = np.zeros(grid.shape)
    crossProbas = np.zeros(grid.shape)
    
    for k in range(gridSize[axis]) :
        '''
        print("------------")
        print("Calcul Probas sur axe :", axis)
        print("Index :", k)
        '''
        numbers = guideNumbers[k]
        
        # On coupe la tranche de grille que l'on veut
        if axis == 0 :    
            gridLine = currentSolGrid[k,:].ravel()
        else : # axis == 1
            gridLine = currentSolGrid[:,k].ravel()
                
        # On appelle "FindProbasInLine"
        # Si jamais il y a une erreur, "error" = True
        error, thingsLineProbas = FindProbasInLine(numbers.copy(), gridLine)
        # Si une contradiction a été trouvé, On remonte tout de suite pour le dire
        if error == True :
            return True, None
        # Dans ce cas les probas ont été trouvées
        else :
            fillLineProbas, crossLineProbas = thingsLineProbas
            # On les ajoute aux grilles
            fillProbas[k,:] = fillLineProbas
            crossProbas[k,:] = crossLineProbas
            
        #Pause()
            
    # Si axis = 1, il faut transposer les matrices de proba pour qu'elles collent avec la grille
    if axis == 1 :
        fillProbas = fillProbas.T
        crossProbas = crossProbas.T
        
    return False, (fillProbas, crossProbas)

def FindProbasInLine(guideNumbers, gridLine) : # Renvoie error, (fillLineProbas, crossLineProbas)
    #print("FindProbasInLine()")
    '''
    /!\ Attention "line" ici peut désigner une colonne, mais ça revient au même ici
    
    Le but va être de calculer toutes les possibilités de placement et d'en faire la moyenne pour chaque case
    "possibilities" est une matrice avec 1 colonne pour chaque case de la ligne "line",
    et 1 ligne pour chaque possibilité
    
    Il y a un bug si il n'y a aucun guide number dans guideNumbers.
    Ce cas arrive quand il n'y a aucun remplissage dans la ligne.
    Pour éviter ce bug, on va d'abord vérifier qu'il y a des nombres dans guideNumbers,
    et s'il y a en pas, on sait que la ligne est remplie de croix
    '''
    
    # On vérifie si on est dans le cas particulier où il n'y a pas de guide number
    if len(guideNumbers) == 0 :
        fillProbas = [0 for k in range(len(gridLine))]
        crossProbas = [1 for k in range(len(gridLine))]
    else :
        possibilities = FindPossibilitiesInLine(guideNumbers.copy(), gridLine)
        
        # Si aucune possibilité n'à été trouvé, cela veut dire qu'il y a une erreur.
        # Du coup on le balance à la maitresse (FindProbas)
        nbPossibilities = possibilities.shape[0]
        if nbPossibilities == 0 :
            return True, None
        # Sinon tout baigne, on peut continuer nos calculs
        else :
            # On traite d'abord les remplissages :
            # On crée un mask avec True là où la case est remplie comme ta soeur
            fillPossibilities = (possibilities == 1)
            # On calcule les probas de chaque case
            fillProbas = fillPossibilities.sum(axis = 0, dtype = np.float16) / nbPossibilities
            
            # Puis les croix :
            crossPossibilities = (possibilities == 2)
            #print("crossPossibilities :",crossPossibilities) # Pour vérifier que c'est bien un mask
            crossProbas = crossPossibilities.sum(axis = 0, dtype = np.float16) / nbPossibilities
        
    return False, (fillProbas, crossProbas)

def FindPossibilitiesInLine(numbersLeft, gridLine, partialPossibility = [], couche = 0) :
    #print("FindPossibilitiesInLine()")
    '''
    Le but est de créer une matrice qui représente toutes les possibilités
    avec comme infos les guide numbers et ce qui est déjà connu sur la ligne de la grille.
    La matrice a 1 colonne pour chaque case de la ligne "line", et 1 ligne pour chaque possibilité
    
    On appelle la fonction par récurrence pour faire une recherche en arbre.
    Du coup le but est de coller les bouts de matrices ensemble
    au fur et à mesure qu'ils sont créés.
    
    "numberLeft" est la liste des guides numbers qui n'ont pas encore été placé
    dans notre possibilité.
    '''

    # On commence par chercher le nombre de placements possibles
    # pour le nombre de la liste qui nous intéresse (cad le premier de "numbersLeft")
    nbPossibilities = FindNbPossibilities(numbersLeft.copy(), len(gridLine), len(partialPossibility))# le nombre de placement possibles pour notre nombre courant
    
    # On extrait le nombre qui nous intéresse de la liste
    # (j'ai mis un try except pcq des fois y a une erreur là dessus et j'essaie de comprendre pk)
    try :
        currentNumber = numbersLeft.pop(0)
        '''
        print("poped successfully")
        print("currentNumber :", currentNumber)
        print("numbersLeft :", numbersLeft)
        print("couche :", couche)
        '''
    except :
        print("---------- Erreur ----------")
        print("On a essayé de pop un nombre de numbersLeft sauf que y en a plus")
        print("méthode : FindPossibilitiesInLine()")
        print("couche :", couche)
        print("numbersLeft :", numbersLeft)
        sys.exit()
        
    # On remplie mtn la matrice partielle de possibilités
    partialPossibilities = np.array([])
    for i in range(nbPossibilities) :
        '''
        Ici on veut fabriquer "nbPossibilities" débuts de possibilités.
        D'abord il y a le début de possibilité (partialPossibility) qu'on a reçu du call de cette récursion.
        Maintenant on veut ajouter notre nombre de cette façon :
            si - "partialPossibility" est disons "11x1x", où "1" représente un replissage et "x" un croix
               - qu'il y a 3 nouveaux débuts de possibilités à faire
               - avec le nombre 2,
            nos 3 possibilités vont être :
                11x1x11
                11x1xx11
                11x1xxx11
        En gros on décale notre nombre de 1 à chaque fois.
        A noter quand même que "partialPossibility" qui nous a été donné se termine par une croix,
        et que donc il faut aussi terminer notre newPartialPossibility par une croix SI CE N'EST PAS LE DERNIER NOMBRE
        '''
        # On fabrique la nouvelle possibilité
        newPartialPossibility = MakeNewPartialPossibility(i, partialPossibility.copy(), currentNumber)
        # On vérifie qu'il n'y a pas de contradiction avec ce qu'on connais déjà de la grille
        error = CheckErrorPartialPossibility(newPartialPossibility.copy(), gridLine.copy())
        
        # On ne traite cette new possibilité partiel que si elle n'a aucune contradiction avec la grille
        if not error :
            # On agit différemment si currentNumber était le dernier de la liste ou pas
            if len(numbersLeft) > 0 : # Si ce n'est pas le dernier de la liste
                # On place une croix pour séparer le nombre des suivants
                newPartialPossibility.append(2)
                # On continue la formation des possibilités avec le nombre suivant
                possibility = FindPossibilitiesInLine(numbersLeft.copy(), gridLine, newPartialPossibility, couche = couche+1)
                '''
                A noter que possibility ici peut regrouper plusieurs possibilités,
                vu que FindPossibilitiesInLine renvoie plusieurs possibilités.
                Ce n'est pas un problème pour la suite, on ajoute cette matrice de possibilité à partialPossibilities
                de la même façon qu'on ajouterait une seule possibilité
                
                /!\ Par contre il peut n'y avoir aucune possibilité de trouvé, et là il faut faire attention
                '''
                
                #Une fois la possibilité créée, il faut l'ajouter à la matrice de possibilités
                partialPossibilities = AddPossibilityToMatrix(possibility, partialPossibilities)
                
            else : # c'était le dernier nombre de la liste
                print("Finish possibility :")
                possibility = FinishPossibility(newPartialPossibility.copy(), len(gridLine))
                print("element of possibility :", possibility.ravel()[0])
                # Il faut s'assurer que les croix ajoutées ne font pas d'erreur avant d'ajouter la possibilité
                if not CheckErrorPartialPossibility(possibility.ravel(), gridLine.copy()) :
                    print("Pas d'erreur dans finishPossibility")        
                    
                    partialPossibilities = AddPossibilityToMatrix(possibility, partialPossibilities)
                
            
    
    # Maintenant on a terminé la branche, et donc on peut remonter le résultat    
    return partialPossibilities

def AddPossibilityToMatrix(possibility, partialPossibilities) :
    # Il faut faire attention au cas ou possibility est vide
    if possibility.size == 0:
        return partialPossibilities
    # S'il n'y a aucune possibilité encore dans partialPossibilities
    elif partialPossibilities.size == 0 :
        return possibility
    else :
        return np.vstack((partialPossibilities, possibility))

def FinishPossibility(partialPossibility, gridLineLength) : # Renvoie possibility
    # On commence par remplir l'espace à droite de croix
    spaceLeft = gridLineLength - len(partialPossibility)
    for k in range(spaceLeft) :
        partialPossibility.append(2)
    # C'est maintenant une possibilité toute prête sortie du four
    possibility = partialPossibility
    # On transforme possibility en array numpy pour la convénience
    possibility = np.array(possibility)
    possibility = possibility.reshape(1,possibility.shape[0]) # Pour éviter des bugs à la concaténation
    
    return possibility

def MakeNewPartialPossibility(possIndex, oldPartialPossibility, currentNumber) : # Renvoie newPartialPossibility
    '''
    possIndex indique la combien-t-ième possibilité est-ce qu'on est en train de faire
    '''
    # On insère les croix (quand i = 0 il n'y en a pas, car on place notre nombre tout à gauche)
    newPartialPossibility = oldPartialPossibility
    for k in range(possIndex):
        newPartialPossibility.append(2)
    # Puis on ajoute notre nombre
    for k in range(currentNumber) :
        newPartialPossibility.append(1)
    
    return newPartialPossibility
    
def CheckErrorPartialPossibility(partialPossibility, gridLine) : # Renvoie error
    print("CheckErrorPartialPossibility")
    # On vérifie que la possibilité partielle correspond à ce qui est déjà connu sur la grille
    for i, cell in enumerate(partialPossibility) :
        # S'il y a une différence avec la grille, we not good
        if (gridLine[i] != 0) & (cell != gridLine[i]) :
            print("Erreur")
            print("partialPossibility :", partialPossibility, "gridLine :", gridLine)
            return True
    
    # Si tout s'est bien passé
    print("Pas d'erreur")
    print("partialPossibility :", partialPossibility, "gridLine :", gridLine)
    return False
        
def FindNbPossibilities(numbersLeft, gridLineLength, partialPossibilityLength) :
    spaceNeeded = sum(numbersLeft) + (len(numbersLeft)-1) # l'espace que prends le remplissage + l'espace que prennent les croix
    spaceLeft = gridLineLength - partialPossibilityLength # l'espace qui n'est pas pris par "partialPossibility
    return spaceLeft+1 - spaceNeeded # le nombre de placement possibles pour notre nombre courant
    
def Pause() :
    global pause
    global pauseMod
    pause = True
    while pause & pauseMod :
        CheckUserInput()
        
# ---------- Utiles ----------
def findMaxLength(listes):
    maxLength = 0
    for liste in listes :
        currentLength = len(liste)
        if currentLength > maxLength :
            maxLength = currentLength
    return maxLength

def RemoveDuplicatesFromList(listyBoy):
    # Transformer en dict enlève les duplications pcq il peut pas y avoir 2 fois la même clé
    return list(dict.fromkeys(listyBoy))


# ---------- Tkinter ----------
def ShowStep(solGrid) :
    ShowGrid(solGrid, solGridDrawSize, solGridPos, showProbas)
    ScreenRefresh()

def CheckUserInput() :
    # On a juste besoin de refresh la fenêtre pour check si on appuie sur une touche
    ScreenRefresh()

def ScreenRefresh() :
    window.update_idletasks()
    window.update()

def Clic(mouseEvent) :
    # Pour avoir la position de la souris : mouseEvent.x ou mouseEvent.y
    # Si on a cliqué, on veut passer à l'itération suivante en mode pause
    if pauseMod :
        global pause
        pause = False

def SpacePressed(KeyEvent) :
    # On active ou désactive le mode pause
    global pauseMod
    pauseMod = not pauseMod
    
def ReturnPressed(keyEvent) :
    global pause
    pause = False

def ShowGrid(grid, size, position, showProbas = False) :
    global currentProbas
    global window
    canvas = tk.Canvas(window, width = gridDrawSize[0], height = gridDrawSize[1])
    shape = grid.shape
        
    for i in range( shape[0] ): # i = numéro de ligne
        for j in range( shape[1] ): # j = numéro de colonne
            # On calcule les coordonées de la case
            x1 = size[0]*j/gridSize[0]
            y1 = size[1]*i/gridSize[1]
            x2 = size[0]*(j+1)/gridSize[0]
            y2 = size[1]*(i+1)/gridSize[1]
            
            thing = grid[i][j]
            if thing == 1:
                # On rempli la case
                canvas.create_rectangle(x1, y1, x2, y2, width = 2, fill = "black")
            elif thing == 2:
                # On dessine une croix
                canvas.create_rectangle(x1, y1, x2, y2, width = 2, fill = "white")
                canvas.create_line(x1, y1, x2, y2, width = 2, fill = "black")
                canvas.create_line(x1, y2, x2, y1, width = 2, fill = "black")
            else :
                canvas.create_rectangle(x1, y1, x2, y2, width = 2, fill = "white")
                # On affiche la proba que s'il n'y a rien dans la case
                if showProbas :
                    proba = currentProbas[i][j]
                    
                    probaLabel = tk.Label(canvas, text = str(proba), width = 4, anchor = tk.NW)
                    probaLabel.place(x = x1+3, y = y1+3)
                    '''
                    print(hex(int(255*proba))[3:5])
                    color = f'{hex(int(255 - 255*proba))}{hex(int(255*proba))}00'
                    canvas.create_rectangle(x1, y1, x2, y2, width = 2, fill = color)
                    '''
    canvas.place(x = position[0], y = position[1])

def showGuideNumbers() :
    global window
    # On commence par les lignes
    nbLines = len(linGuideNumbers)
    maxNbNumbers = findMaxLength(linGuideNumbers)
    fontSize = int( (gridDrawSize[1] / nbLines)  * (3/4) /2) # "4/3" c'est pour convertir les pixels en points
    font = tkfont.Font(size = fontSize)
    
    # On set le canvas sur lequel on va placer les nombres
    borderWidth = 2
    canvasSize = (gridPos[0], gridDrawSize[1])
    canvasPos = (0,gridPos[1])
    canvas = tk.Canvas(window, width = canvasSize[0], height = canvasSize[1] + borderWidth+1)
    
    for i, numbers in enumerate(linGuideNumbers) :
        nbNumbers = len(numbers) # Onen a besoin pour placer les nombres correctement
        for j, number in enumerate(numbers) :
            xShift = (maxNbNumbers - nbNumbers) * canvasSize[0] / maxNbNumbers
            yShift = borderWidth+1
            # On place d'abord le cadre
            x1 = j * canvasSize[0] / maxNbNumbers + xShift
            y1 = i * canvasSize[1] / nbLines + yShift
            x2 = (j+1) * canvasSize[0] / maxNbNumbers + xShift
            y2 = (i+1) * canvasSize[1] / nbLines + yShift
            canvas.create_rectangle(x1, y1, x2, y2, width = borderWidth, fill = "white")
            
            # Puis le texte
            text = tk.Label(window, text = str(number),
                            justify = "center",
                            font = font)
            textX = canvasPos[0] + (j+0.5) * canvasSize[0] / maxNbNumbers + xShift
            textY = canvasPos[1] + (i+0.5) * canvasSize[1] / nbLines
            text.place(x = textX, y = textY, anchor = tk.CENTER)
    canvas.place(x = canvasPos[0], y = canvasPos[1] - (borderWidth+1))
    
    
    # Puis les colonnes
    nbColonnes = len(colGuideNumbers)
    maxNbNumbers = findMaxLength(colGuideNumbers)
    fontSize = int( (gridDrawSize[1] / nbLines)  * (3/4) /2) # "4/3" c'est pour convertir les pixels en points
    font = tkfont.Font(size = fontSize)
    
    # On set le canvas sur lequel on va placer les nombres
    borderWidth = 2
    canvasSize = (gridDrawSize[0], gridPos[1])
    canvasPos = (gridPos[0], 0)
    canvas = tk.Canvas(window, width = canvasSize[0]  + borderWidth+1, height = canvasSize[1])
    
    for j, numbers in enumerate(colGuideNumbers) :
        nbNumbers = len(numbers) # Onen a besoin pour placer les nombres correctement
        for i, number in enumerate(numbers) :
            xShift = borderWidth+1
            yShift = (maxNbNumbers - nbNumbers) * canvasSize[1] / maxNbNumbers
            # On place d'abord le cadre
            x1 = j * canvasSize[0] / nbColonnes + xShift
            y1 = i * canvasSize[1] / maxNbNumbers + yShift
            x2 = (j+1) * canvasSize[0] / nbColonnes + xShift
            y2 = (i+1) * canvasSize[1] / maxNbNumbers + yShift
            canvas.create_rectangle(x1, y1, x2, y2, width = 2, fill = "white")
            
            # Puis le texte
            text = tk.Label(window, text = str(number),
                            justify = "center",
                            font = font)
            textX = canvasPos[0] + (j+0.5) * canvasSize[0] / nbColonnes
            textY = canvasPos[1] + (i+0.5) * canvasSize[1] / maxNbNumbers + yShift
            text.place(x = textX, y = textY, anchor = tk.CENTER)
    canvas.place(x = canvasPos[0] - (borderWidth+1), y = canvasPos[1])





# ------------------------------------------------------------
# -------------------- CORPS DU PROGRAMME --------------------
# ------------------------------------------------------------

# ---------- Génération ----------
linGuideNumbers, colGuideNumbers = findNumbers(grid, gridSize)


# ---------- Tkinter ----------
if showTkinter :
    # Window settings
    window = tk.Tk()
    window.geometry(f"{winSize[0]}x{winSize[1]}")
    window.title("Picross Solver")
    window["bg"] = "white"
    window.resizable(height = False, width = False)
    
    # Grids
    # Base grid
    ShowGrid(grid, gridDrawSize, gridPos)
    # Solution grid
    ShowGrid(solutionGrid, solGridDrawSize, solGridPos, showProbas)
    # Guide Numbers
    showGuideNumbers()
    
    # Pause Things
    # Binds
    window.bind("<Button-1>", Clic) # Joue "clic" quand le clic gauche de la souris est appuyé
    window.bind("<space>", SpacePressed)
    window.bind("<Return>", ReturnPressed)
    # UI
    pauseModLabel = tk.Label(window, text = f"pause mod : {pauseMod}")
    pauseLabel = tk.Label(window, text = f"Pause : {pause}")
    pauseModLabel.pack(side=tk.TOP, anchor=tk.NW)
    pauseLabel .pack(side=tk.TOP, anchor=tk.NW)
    
    
    # We start the solving after the tkinter settings because we want to show the process
    solutionGrid = Solve( linGuideNumbers, colGuideNumbers, gridSize)
    
    
    window.mainloop()


# ---------------------------------------------------
# -------------------- Test zone --------------------
# ---------------------------------------------------

solutionGrid = Solve( linGuideNumbers, colGuideNumbers, gridSize)

'''
# ---------- FindPossibilitiesInLine() ----------
print("---------- Test FindPossibilitiesInLine() :")
guideNumbers = [1, 2]
gridLine = [0,0,0,0,0]
print("linGuideNumbers :", guideNumbers)
print("gridline :", gridLine)
print("possibilities :\n", FindPossibilitiesInLine(guideNumbers.copy(), gridLine))
# Good !
'''
'''
# ---------- FindProbasInLine() ----------
print("---------- Test FindProbasInLine() :")
#guideNumbers = [2,1,3]
#gridLine = [0,1,0,0,0,0,0,0,0,0]
#print("linGuideNumbers :", guideNumbers)
#print("gridline :", gridLine)
print("probas :\n",FindProbasInLine(guideNumbers.copy(), gridLine)[1][0])
# Good !
'''
'''
# ---------- FindProbas() ----------
print("---------- Test FindProbas() :")
print("grid :\n",grid)
print("linguideNumbers :", linGuideNumbers)
print("Probas :\n", (FindProbas(linGuideNumbers, np.zeros(gridSize), axis = 0))[1][0])
# Good !
'''

