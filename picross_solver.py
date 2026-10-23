# Le but de se programme est de coder la grille, les numéros d'indication, et de créer automatiquement les numéros à partir d'une grille coloriée
import numpy as np
import tkinter as tk
import tkinter.font as tkfont
import sys

gridSize = (10,10)
winSize = (1600,800)
# Base Grid
#np.random.seed(1)
grid = np.random.randint(0,2,gridSize)
gridDrawSize = (min(winSize) / 2, min(winSize) / 2)
gridPos = (gridDrawSize[0]/2, gridDrawSize[1]/2)
# Solution grid
solutionGrid = np.zeros(gridSize)
solGridSize = gridDrawSize
solGridPos = (solGridSize[0]*5/2, solGridSize[1]/2)
currentProbas = np.zeros(gridSize)

colGuideNumbers = []
linGuideNumbers = []

SolutionGrid = np.zeros(gridSize)

pauseMod = False # indique si on doit attendre une action de l'utilisateur à chaque boucle
pause = False # utilisé pour savoir quand l'utilisateur indique qu'il faut continuer


# ------------------------------------------------
# ---------- Création de nombres random ----------
# ------------------------------------------------

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



# --------------------------------
# ---------- Résolution ----------
# --------------------------------

def ClearGrid() :
    global grid
    grid= np.zeros(gridSize)
    print("grid cleared :", grid)

def Solve(grid, linGuideNumbers, colGuideNumbers, gridSize) :
    noError, res = Assumption(0, grid.copy(), linGuideNumbers, colGuideNumbers, gridSize)
    if noError == False :
        print("Les numéros semblent pas bons")
        return None
    else :
        print("Finito !")
        ShowGrid(res, solGridSize, solGridPos, showProbas = True)
        return res
        
def Assumption(layer, grid, linGuideNumbers, colGuideNumbers, gridSize) :
    global currentProbas
    
    print("entering assumption at layer :", layer)
    solved = False
    
    linFillProbas = np.zeros(gridSize)
    linCrossProbas = np.zeros(gridSize)
    colFillProbas = np.zeros(gridSize)
    colCrossProbas = np.zeros(gridSize)
    fillProbas = np.zeros(gridSize)
    crossProbas = np.zeros(gridSize)
    
    # Boucle principale
    while(not solved) :
        if pauseMod :
            Pause()
        # We show the result at runtime
        ShowGrid(grid, solGridSize, solGridPos, showProbas = True)
        ScreenRefresh()

        # On calcule les probas pour les lignes et les colonnes
        # On s'assure au passage qu'il n'y a aucune erreur de trouvée
        noError1, res1 = FindProbas(linGuideNumbers.copy(), grid, axis = 0)
        noError2, res2 = FindProbas(colGuideNumbers.copy(), grid, axis = 1)
        
        if (noError1 == False) | (noError2 == False):
            return False, None
        
        else :
            # On stock les probas trouvées dans les variables correspondantes
            linFillProbas, linCrossProbas = res1
            colFillProbas, colCrossProbas = res2
            
            fillProbas = (linFillProbas + colFillProbas) / 2
            currentProbas = fillProbas
            
            # On place les remplissages et les croix là où la proba = 1
            fillMask = ((linFillProbas == 1) | (colFillProbas == 1)) & (grid == 0)
            crossMask = ((linCrossProbas == 1) | (colCrossProbas == 1)) & (grid == 0)
            
            # Si il y a des trucs sûrs, on les place et on  recommence à calculer les probas
            if np.any(fillMask) | np.any(crossMask) :
                grid[fillMask] = 1
                grid[crossMask] = 2
                
                # On les place aussi dans la grille qui va nous permettre de vérifier s'il y a des erreurs
                newlyPlacedThings = np.zeros(gridSize)
                newlyPlacedThings[fillMask] = 1
                newlyPlacedThings[crossMask] = 2
                
                # On vérifie qu'il n'y a pas d'erreur
                if CheckErrors(grid, newlyPlacedThings, linGuideNumbers.copy(), colGuideNumbers.copy()) :
                    return False, None
                
                # On vérifie si on a complété la grille
                if (linGuideNumbers, colGuideNumbers) == findNumbers(grid, gridSize) :
                    solved = True
                
            # Sinon on entre dans une nouvelle supposition
            else :
                # On supperpose les probabilités de ligne et de colonne
                fillProbas = (linFillProbas + colFillProbas) / 2
                crossProbas = (linCrossProbas + colFillProbas) / 2
                # On enlève les probas là où on a déjà placé des trucs
                fillProbas[grid != 0] = 0
                crossProbas[grid != 0] = 0
                newGrid = np.copy(grid)
                '''
                print("gonna do an assumption")
                print("linFillProbas :", linFillProbas)
                print("fillProbas :", fillProbas)
                '''
                # La supposition qu'on va faire est là où il y a la plus forte proba sur la grille
                fillAssumptionPos = np.unravel_index(np.argmax(fillProbas), fillProbas.shape)
                crossAssumptionPos = np.unravel_index(np.argmax(crossProbas), crossProbas.shape)
                
                # si la proba de fill est plus grande que la proba de cross, la supposition sera un fill
                if fillProbas[fillAssumptionPos] > crossProbas[crossAssumptionPos] :
                    assumption = 1
                    assumptionPos = fillAssumptionPos
                # Sinon cross
                else :
                    assumption = 2
                    assumptionPos = crossAssumptionPos
                newGrid[assumptionPos] = assumption
                noError, res = Assumption(layer+1, newGrid, linGuideNumbers.copy(), colGuideNumbers.copy(), gridSize)
                
                # Si la cette supposition a mené à une contradiction,
                # on sait donc mtn que c'est l'inverse de la supposition à cet endroit
                if noError == False :
                    if assumption == 1 :
                        grid[assumptionPos] = 2
                    else :
                        grid[assumptionPos] = 1
                # Si ça a mené à une bonne solution, on a résolu l'affaire
                else :
                    grid = res
                    solved = True
                        
    # On sort de la boucle si la solution a été trouvée
    print("Come back from layer :", layer)
    return True, grid

def FindProbas(guideNumbers, grid, axis):
    fillProbas = np.zeros(grid.shape)
    crossProbas = np.zeros(grid.shape)
    
    # Si on veut s'occuper des lignes
    if axis == 0 :
        for i in range(gridSize[0]) :
            numbers = guideNumbers[i]
            gridLine = grid[i,:].ravel()
            noError, res = FindProbasInLine(numbers.copy(), gridLine)
            # Si une contradiction a été trouvé
            if noError == False :
                return False, None
            # Dans ce cas les probas ont été trouvées
            else :
                fillLineProbas, crossLineProbas = res
                # On les ajoute aux grilles
                fillProbas[i,:] = fillLineProbas
                crossProbas[i,:] = crossLineProbas

    # Si on veut s'occuper des colonnes
    else :
        for j in range(gridSize[1]) :
            numbers = guideNumbers[j]
            gridLine = grid[:,j]
            noError, res = FindProbasInLine(numbers.copy(), gridLine)
            # Si une contradiction a été trouvé
            if noError == False :
                return False, None
            # Dans ce cas les probas ont été trouvées
            else :
                fillLineProbas, crossLineProbas = res
                # On les ajoute aux grilles
                fillProbas[j,:] = fillLineProbas
                crossProbas[j,:] = crossLineProbas
        # On doit transposer les matrices à la fin car elles ne sont pas dans le bon sens pour les colonnes
        fillProbas = fillProbas.T
        crossProbas = crossProbas.T

    return True, (fillProbas, crossProbas)

def FindProbasInLine(numbers, gridLine) :
    atLeastOnePossibility, possibilities = FindPossibilitiesInLine([], numbers.copy(), gridLine, 0)

    # Si nbPossibilities = 0, ça veut dire qu'il y a une contradiction
    if not atLeastOnePossibility :
        return False, None
    else :
        nbPossibilities = possibilities.shape[0]
        
        # On traite d'abord les remplissages :
        # On crée un mask avec True là où la case est remplie comme ta soeur
        fillPossibilities = (possibilities == 1)
        # On calcule les probas de chaque case
        fillProbas = fillPossibilities.sum(axis = 0, dtype = np.float16) / nbPossibilities
        
        # Puis les croix :
        crossPossibilities = (possibilities == 2)
        print(crossPossibilities) # Pour vérifier que c'est bien un mask
        crossProbas = crossPossibilities.sum(axis = 0, dtype = np.float16) / nbPossibilities
        return True, (fillProbas, crossProbas)
        
def FindPossibilitiesInLine(partialPossibility, numbersLeft, gridLine, couche, checkAtLeastOnePossibility = False) :
    # partialPossibility est le schema rempli pour les nombres précédant celui qui va être traité
    # numbersLeft c'est ceux qui ont pas encore été placés
    # lineFromGrid est la ligne telle qu'elle est actuellement dessinée dans la grille. permet de savoir si notre possibilité créée correspond à ce qui est déjà écrit dans la grille
    
    # On commence par calculer la place totale minimale que prennent les numbersLeft
    # (ça pourra nous indiquer le nombre de possibilités pour le nombre à traiter dans cette récursion)
    spaceNeeded = sum(numbersLeft) + (len(numbersLeft)-1) # l'espace que prends le remplissage + l'espace que prennent les croix
    spaceLeft = len(gridLine) - len(partialPossibility)
    nbPossibilities = spaceLeft+1 - spaceNeeded # le nombre de placement possibles pour notre nombre courant
    atLeastOnePossibility = False # Tells if there's at least one possibility
    
    # Si notre ligne est à plat, le nombre qui nous intéresse est celui le plus à gauche dans les numbersLeft
    # On sait maintenant que la première possibilité est de le placer le plus à gauche possible
    # et que sa dernière possibilité est décalé de nbPossibilities
    # On va donc fabriquer ces possibilités et appeler FindPossibilities pour les autres nombres restants s'il y en a
    # On retire notre nombre de la liste
    
    try :
        currentNumber = numbersLeft.pop(0)
    except :
        print("j'ai chié dans la soupe", couche)
        sys.exit()
    partialPossibilities = np.array([]) # Matrice partielle des possibilités, remplie par ce qui suit
    
    for i in range(nbPossibilities) :
        newPartialPossibility = partialPossibility.copy()
        # On insère les éventuelles croix (quand i = 1 il n'y en a pas, car on place notre nombre tout à gauche)
        for k in range(i):
            newPartialPossibility.append(2)
        # Puis on ajoute notre nombre
        for k in range(currentNumber) :
            newPartialPossibility.append(1)
        
        weGood = True # dit si on est good avec la grille
        # On vérifie que la possibilité partielle correspond à ce qui est déjà connu sur la grille
        for i, cell in enumerate(newPartialPossibility) :
            # S'il y a une différence avec la grille, we not good
            if (gridLine[i] != 0) & (cell != gridLine[i]) :
                weGood = False
                break
        
        # On traite la possibilité partielle que si on est good
        if weGood :
            # Si ce n'était pas le dernier nombre de la liste, on appelle FindPossibilities pour les restants
            if len(numbersLeft) > 0 :
                # D'abord on ajoute une croix pour le séparer des chunks suivants
                newPartialPossibility.append(2)
                currentAtLeastOnePossibility, possibility = FindPossibilitiesInLine(newPartialPossibility, numbersLeft.copy(), gridLine, couche+1)
                # Si on a trouvé une possibilité, on set "atLeastOnePossibility" à true
                # Sinon on continue de chercher les possibilités
                if currentAtLeastOnePossibility :
                    atLeastOnePossibility = True
                    # We don't have to search further if "checkAtLeastOnePossibility" is set to true
                    if checkAtLeastOnePossibility :
                        return atLeastOnePossibility, None
                
            # Sinon c'est le dernier de la liste, et donc la possibilité est presque prête
            else :
                # On vient de trouver une possibilité, donc on a pas besoin d'aller plus loin
                # Si "checkAtLeastOnePossibility" == True
                atLeastOnePossibility = True
                if checkAtLeastOnePossibility :
                    print("at least on possibility :", atLeastOnePossibility, "couche :", couche)
                    return atLeastOnePossibility, None
                
                # On commence par remplir l'espace à droite de croix
                spaceLeft = len(gridLine) - len(newPartialPossibility)
                for k in range(spaceLeft) :
                    newPartialPossibility.append(2)
                # C'est maintenant une possibilité toute prête sortie du four
                possibility = newPartialPossibility.copy()
                # On transforme possibility en array numpy pour la convénience
                possibility = np.array(possibility)
                possibility = possibility.reshape(1,possibility.shape[0]) # Pour éviter des bugs à la concaténation
            
            # On ajoute cette possibilité préparée avec soin à notre matrice de possibilités
            # Cependant il se peut que possibility soit vide, donc on vérifie d'abord qu'elle ne l'est pas
            if possibility.size != 0 :
                # La manipe diffère selon si partialPossibilities est vide ou pas
                if(partialPossibilities.size == 0) :
                    partialPossibilities = possibility
                else :
                    partialPossibilities = np.vstack((partialPossibilities, possibility))
        
        

    # Une fois toutes les possibilités explorées pour notre currentNumber,
    # On remonte notre matrice de possibilités
    return atLeastOnePossibility, partialPossibilities

def findMaxLength(listes):
    maxLength = 0
    for liste in listes :
        currentLength = len(liste)
        if currentLength > maxLength :
            maxLength = currentLength
    return maxLength

def CheckErrors(grid, newlyPlacedThings, linNumbers, colNumbers) :
    # le but est de vérifier pour chaque croix et chaque remplissage qui viennent d'être placés
    # s'il n'engendrent pas d'erreur, cad qu'ils ne réduisent pas à 0 le nombre de possibilité
    # dans leurs colonnes et lignes respectives
    
    # "newlyPlacedThings" est une grille qui contient uniquement ce qui vient d'être placé
    # "grid" contient aussi les éléments qui viennent d'être placés
    
    # On commence par calculer dans quelles colonnes est ce qu'on va faire nos vérifications
    linesToCheck, colsToCheck = np.where(newlyPlacedThings != 0)
    
    # On commence la vérification par les lignes
    for i in linesToCheck :
        res = FindPossibilitiesInLine([], linNumbers[i].copy(), grid[i,:], 0, checkAtLeastOnePossibility=True)
        if res[0] == False :
            print(f"Check Errors line {i}, noErrors = False")
            print("guide numbers :", linNumbers)
            return True
    # Ensuite les colonnes
    for j in colsToCheck :
        res = FindPossibilitiesInLine([], colNumbers[j].copy(), grid[:,j], 0, checkAtLeastOnePossibility=True)
        if res[0] == False :
            print(f"Check Errors column {j}, noErrors = False")
            print("guide numbers :", colNumbers)
            return True
    # Si on a rien trouvé, on retourne False
    print("hey2")
    return False

def RemoveDuplicatesFromList(listyBoy):
    # Transformer en dict enlève les duplications pcq il peut pas y avoir 2 fois la même clé
    return list(dict.fromkeys(listyBoy))

def Pause() :
    global pause
    global pauseMod
    pause = True
    while pause & pauseMod :
        CheckPause()

# ----------------------------------------
# ----------- Tkinter methods ------------
# ----------------------------------------

def CheckPause() :
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
    
    '''
    nbColonnes = len(colGuideNumbers)
    maxNbNumbers = findMaxLength(colGuideNumbers)
    for i, numbers in enumerate(colGuideNumbers) :
        for j, number in enumerate(numbers) :
            
            text = tk.Label(window, text = str(number), justify = "center", anchor = tk.CENTER)
            x = gridPos[0] + i * gridDrawSize[0] / nbColonnes
            y = j * gridPos[1] / maxNbNumbers
            text.place(x = x, y = y)
            '''
            
# ----------------------------------------------
# ---------- Programme hors graphique ----------
# ----------------------------------------------

# Création de nombres random
linGuideNumbers, colGuideNumbers = findNumbers(grid, gridSize)

# Résolution
#ClearGrid()


# ---------- zone de test ----------
'''
numbers = [2,2]
gridLine = [0,0,0,0,0]
print(FindProbasInLine(numbers, gridLine)[0])
'''
#print((FindProbas(colGuideNumbers, solutionGrid, 1))[0])
#print(FindProbas(linGuideNumbers, SolutionGrid, 0)[0])
# ----------------------------------



# --------------------------------------
# ---------- Aspect graphique ----------
# --------------------------------------

window = tk.Tk()
window.geometry(f"{winSize[0]}x{winSize[1]}")
window.title("Picross Solver")
window["bg"] = "white"
window.resizable(height = False, width = False)

# Base grid
ShowGrid(grid, gridDrawSize, gridPos)

# Solution grid
ShowGrid(SolutionGrid, solGridSize, solGridPos, showProbas = True)

# Guide Numbers
showGuideNumbers()

# Pause
window.bind("<Button-1>", Clic) # Joue "clic" quand le clic gauche de la souris est appuyé
window.bind("<space>", SpacePressed)
window.bind("<Return>", ReturnPressed)

pauseModLabel = tk.Label(window, text = f"pause mod : {pauseMod}")
pauseLabel = tk.Label(window, text = f"Pause : {pause}")

pauseModLabel.pack(side=tk.TOP, anchor=tk.NW)
pauseLabel .pack(side=tk.TOP, anchor=tk.NW)

SolutionGrid = Solve(solutionGrid, linGuideNumbers, colGuideNumbers, gridSize)

window.mainloop()
