import numpy as np
from enum import Enum
import sys
import time

import Draw
import Grid


# ---------- Enum ----------
class State(Enum):
    SEARCHING = 0
    SOLVED = 1
    ERROR = 2

# ---------- Paramêtres ----------
showTkinter = True
pauseMod = True

# ---------- Infos ----------
gridShape: tuple[int, int]
pause = False

def Solve(guideNumbersAxis, _gridShape, _showTkinter=True, _pauseMod=False):  # Retourne solutionGrid, solved
    global gridShape
    global showTkinter
    global pauseMod
    gridShape = _gridShape
    showTkinter = _showTkinter
    pauseMod = _pauseMod

    solutionGrid = np.zeros(gridShape)
    # We enter into the first layer of assumption
    # Here the assumption is that our guide numbers can give a solution

    error, solutionGrid = Assumption(0, solutionGrid, guideNumbersAxis)

    if error == State.ERROR:
        print("les nombre sont pas bons ou alors c'est le programme qui est pas bon")
        return solutionGrid, False
    else:
        #print("Solved !")
        if showTkinter :
            Draw.ShowStep(solutionGrid)
        return solutionGrid, True

def Assumption(layer, currentSolGrid, guideNumbersAxis, axisToSearch=0):  # Renvoie state, solutionGrid
    # "searchOnAxis" dit si on doit calculer les probas sur les colonnes ou sur les lignes

    # Probas
    crossProbasAxis = [np.zeros(gridShape),  # the first one is for the line probas,
                       np.zeros(gridShape)]  # the second for the col probas
    fillProbasAxis = [np.zeros(gridShape),
                      np.zeros(gridShape)]
    # Moyenne des probas de ligne et de colonne
    fillProbas = np.zeros(gridShape)
    crossProbas = np.zeros(gridShape)

    state = State.SEARCHING

    hadPlacedThingsOnAxis = [True, True]

    # Boucle principale
    while state == State.SEARCHING:
        # On montre le process pendant la résolution
        if showTkinter:
            Draw.ShowStep(currentSolGrid)

        # On pause que si pauseMod est activé
        if pauseMod:
            Pause()

        # On calcule les probas pour les lignes ou les colonnes
        # On s'assure au passage qu'il n'y a aucune erreur de trouvée
        error, thingsProbas = FindProbas(guideNumbersAxis[axisToSearch].copy(), currentSolGrid,
                                                axis=axisToSearch)
        # "thingsProbas" contient les grille de proba de fill et de cross pour l'axe courant

        # S'il y a une erreur de trouvée, on arrête tout et on remonte l'info
        if error:
            '''
            Normalement ça devrait suffir pour détecter les contradictions, mais j'en suis pas complètement sûr
            '''
            return State.ERROR, None

        else:  # Pas d'erreur, on peut continuer
            # On stock les probas trouvées dans les variables correspondantes
            fillProbasAxis[axisToSearch], crossProbasAxis[axisToSearch] = thingsProbas

            # On commence par essayer de placer des trucs sûrs
            hadPlacedThingsOnAxis[axisToSearch], currentSolGrid, thingsNotChanged = PlaceSure(
                fillProbasAxis[axisToSearch], crossProbasAxis[axisToSearch], currentSolGrid)

            # Si on a rien réussi à placer aver certitude, ni sur les lignes ni sur les colonnes,
            # on entre dans une nouvelle supposition
            if (not hadPlacedThingsOnAxis[0]) & (not hadPlacedThingsOnAxis[1]):
                fillProbas = (fillProbasAxis[0] + fillProbasAxis[1]) / 2
                crossProbas = (crossProbasAxis[0] + crossProbasAxis[1]) / 2
                newState, currentSolGrid = StartNewAssumption(layer + 1, np.copy(currentSolGrid),
                                                                     guideNumbersAxis,
                                                                     gridShape, fillProbas, crossProbas)

                # On vérifie si la grille a été résolue après cette supposition
                if newState == State.SOLVED:
                    return State.SOLVED, currentSolGrid

            ''' 
            Après avoir placé des trucs, il est temps de vérifier si on a résolu la grille
            '''
            if CheckSolved(currentSolGrid, fillProbasAxis, crossProbasAxis):
                return State.SOLVED, currentSolGrid

            # On change l'axis de recherche pour la prochaine itération de la boucle
            axisToSearch = 1 if (axisToSearch == 0) else 0
    return state, currentSolGrid

def CheckSolved(currentSolGrid, FillProbasAxis, CrossProbasAxis):
    '''
    Le but va être de voir si on a placé les bons trucs là où la proba = 1
    et que la grille est bien remplie comme ta
    '''

    # print("CheckSolved()")

    fillCompletionMask = ((FillProbasAxis[0] == 1) | (FillProbasAxis[1] == 1)) & (currentSolGrid == 1)
    crossCompletionMask = ((CrossProbasAxis[0] == 1) | (CrossProbasAxis[1] == 1)) & (currentSolGrid == 2)
    completionMask = fillCompletionMask | crossCompletionMask

    solved = np.all(completionMask)

    return solved

def StartNewAssumption(layer, currentSolGrid, guideNumbersAxis, gridShape, fillProbas, crossProbas):
    '''
    Renvoie : state, newGrid
    '''

    #print("Nouvelle supposition !")

    # On commence par enlever toutes les probas là où il y a déjà un truc de placé
    fillProbas[currentSolGrid != 0] = 0
    crossProbas[currentSolGrid != 0] = 0

    # La supposition qu'on va faire est là où il y a la plus forte proba sur la grille
    fillAssumptionPos = np.unravel_index(np.argmax(fillProbas), fillProbas.shape)
    crossAssumptionPos = np.unravel_index(np.argmax(crossProbas), crossProbas.shape)

    # si la proba de fill est plus grande que la proba de cross, la supposition sera un fill
    if fillProbas[fillAssumptionPos] > crossProbas[crossAssumptionPos]:
        assumption = 1
        assumptionPos = fillAssumptionPos
        #print("la case à", assumptionPos, "est un remplissage")
    # Sinon cross
    else:
        assumption = 2
        assumptionPos = crossAssumptionPos
        #print("la case à", assumptionPos, "est une croix")
    currentSolGrid[assumptionPos] = assumption

    Pause()

    state, solvedGrid = Assumption(layer, currentSolGrid, guideNumbersAxis)

    # Si la cette supposition a mené à une contradiction,
    # on sait donc mtn que c'est l'inverse de la supposition à cet endroit
    if state == State.ERROR:
        #print("Mauvaise supposition !")
        if assumption == 1:
            currentSolGrid[assumptionPos] = 2
        else:
            currentSolGrid[assumptionPos] = 1
        return State.ERROR, currentSolGrid
    # Si ça a mené à une bonne solution, on a résolu l'affaire
    else:  # state == State.SOLVED
        return State.SOLVED, solvedGrid

def PlaceSure(fillProbas, crossProbas, currentSolGrid):  # Renvoie hadPlacedThings, newSolGrid, (linesNotChanged, colsNotChanged)
    # On crée des masks avec true là où proba = 1
    fillMask = (fillProbas == 1) & (currentSolGrid == 0)
    crossMask = (crossProbas == 1) & (currentSolGrid == 0)

    # S'il y a des trucs sûrs, on les places et on remonte l'information qu'on a réussi à en placer
    if np.any(fillMask) | np.any(crossMask):
        currentSolGrid[fillMask] = 1
        currentSolGrid[crossMask] = 2

        # On cherche les lignes et colonnes où on a rien placé
        linesNotChanged, colsNotChanged = np.where(np.invert(fillMask | crossMask))
        # On enlève les indices en double
        linesNotChanged = RemoveDuplicatesFromList
        colsNotChanged = RemoveDuplicatesFromList

        return True, currentSolGrid, (linesNotChanged, colsNotChanged)
    else:
        return False, currentSolGrid, None

def FindProbas(guideNumbers, currentSolGrid, axis):  # Renvoie error, (fillProbas, crossProbas)
    '''
    Le but de cette méthode est de renvoyer 2 grilles de probabilité.
    Chaque grille correspond aux probabilités de remplissage et de croix,
    par rapport aux guide numbers de colonne OU de ligne (selon l'axis).
    La méthode renvoie l'information de si une erreur a été trouvé
    et la grille si aucune erreur a été trouvée.
    '''

    # On va appeler pour chaque ligne ou chaque colonne la méthode "FindProbasInLine"
    # Et regrouper les résultats de chaque appel dans les 2 grilles
    fillProbas = np.zeros(gridShape)
    crossProbas = np.zeros(gridShape)

    for k in range(gridShape[axis]):
        numbers = guideNumbers[k]

        # On coupe la tranche de grille que l'on veut
        if axis == 0:
            gridLine = currentSolGrid[k, :].ravel()
        else:  # axis == 1
            gridLine = currentSolGrid[:, k].ravel()

        # On appelle "FindProbasInLine"
        # Si jamais il y a une erreur, "error" = True
        error, thingsLineProbas = FindProbasInLine(numbers.copy(), gridLine)
        # Si une contradiction a été trouvé, On remonte tout de suite pour le dire
        if error == True:
            return True, None
        # Dans ce cas les probas ont été trouvées
        else:
            fillLineProbas, crossLineProbas = thingsLineProbas
            # On les ajoute aux grilles
            fillProbas[k, :] = fillLineProbas
            crossProbas[k, :] = crossLineProbas

        # Pause()

    # Si axis = 1, il faut transposer les matrices de proba pour qu'elles collent avec la grille
    if axis == 1:
        fillProbas = fillProbas.T
        crossProbas = crossProbas.T

    return False, (fillProbas, crossProbas)

def FindProbasInLine(guideNumbers, gridLine):  # Renvoie error, (fillLineProbas, crossLineProbas)
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
    if len(guideNumbers) == 0:
        fillProbas = [0 for k in range(len(gridLine))]
        crossProbas = [1 for k in range(len(gridLine))]
    else:
        possibilities = FindPossibilitiesInLine(guideNumbers.copy(), gridLine)

        # Si aucune possibilité n'à été trouvé, cela veut dire qu'il y a une erreur.
        # Du coup on le balance à la maitresse (FindProbas)
        nbPossibilities = possibilities.shape[0]
        if nbPossibilities == 0:
            return True, None
        # Sinon tout baigne, on peut continuer nos calculs
        else:
            # On traite d'abord les remplissages :
            # On crée un mask avec True là où la case est remplie comme ta soeur
            fillPossibilities = (possibilities == 1)
            # On calcule les probas de chaque case
            fillProbas = fillPossibilities.sum(axis=0, dtype=np.float16) / nbPossibilities

            # Puis les croix :
            crossPossibilities = (possibilities == 2)
            # print("crossPossibilities :",crossPossibilities) # Pour vérifier que c'est bien un mask
            crossProbas = crossPossibilities.sum(axis=0, dtype=np.float16) / nbPossibilities

    return False, (fillProbas, crossProbas)

def FindPossibilitiesInLine(numbersLeft, gridLine, partialPossibility=[], couche=0):
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
    nbPossibilities = FindNbPossibilities(numbersLeft.copy(), len(gridLine),
                                                 len(partialPossibility))  # le nombre de placement possibles pour notre nombre courant

    # On extrait le nombre qui nous intéresse de la liste
    # (j'ai mis un try except pcq des fois y a une erreur là dessus et j'essaie de comprendre pk)
    try:
        currentNumber = numbersLeft.pop(0)
    except:
        print("---------- Erreur ----------")
        print("On a essayé de pop un nombre de numbersLeft sauf que y en a plus")
        print("méthode : FindPossibilitiesInLine()")
        print("couche :", couche)
        print("numbersLeft :", numbersLeft)
        sys.exit()

    # On remplie mtn la matrice partielle de possibilités
    partialPossibilities = np.array([])
    for i in range(nbPossibilities):
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
        if not error:
            # On agit différemment si currentNumber était le dernier de la liste ou pas
            if len(numbersLeft) > 0:  # Si ce n'est pas le dernier de la liste
                # On place une croix pour séparer le nombre des suivants
                newPartialPossibility.append(2)
                # On continue la formation des possibilités avec le nombre suivant
                possibility = FindPossibilitiesInLine(numbersLeft.copy(), gridLine, newPartialPossibility,
                                                             couche=couche + 1)
                '''
                A noter que possibility ici peut regrouper plusieurs possibilités,
                vu que FindPossibilitiesInLine renvoie plusieurs possibilités.
                Ce n'est pas un problème pour la suite, on ajoute cette matrice de possibilité à partialPossibilities
                de la même façon qu'on ajouterait une seule possibilité
                
                /!\ Par contre il peut n'y avoir aucune possibilité de trouvé, et là il faut faire attention
                '''

                # Une fois la possibilité créée, il faut l'ajouter à la matrice de possibilités
                partialPossibilities = AddPossibilityToMatrix(possibility, partialPossibilities)

            else:  # c'était le dernier nombre de la liste
                possibility = FinishPossibility(newPartialPossibility.copy(), len(gridLine))
                # Il faut s'assurer que les croix ajoutées ne font pas d'erreur avant d'ajouter la possibilité
                if not CheckErrorPartialPossibility(possibility.ravel(), gridLine.copy()):
                    partialPossibilities = AddPossibilityToMatrix(possibility, partialPossibilities)

    # Maintenant on a terminé la branche, et donc on peut remonter le résultat
    return partialPossibilities

def AddPossibilityToMatrix(possibility, partialPossibilities):
    # Il faut faire attention au cas ou possibility est vide
    if possibility.size == 0:
        return partialPossibilities
    # S'il n'y a aucune possibilité encore dans partialPossibilities
    elif partialPossibilities.size == 0:
        return possibility
    else:
        return np.vstack((partialPossibilities, possibility))

def FinishPossibility(partialPossibility, gridLineLength):  # Renvoie possibility
    # On commence par remplir l'espace à droite de croix
    spaceLeft = gridLineLength - len(partialPossibility)
    for k in range(spaceLeft):
        partialPossibility.append(2)
    # C'est maintenant une possibilité toute prête sortie du four
    possibility = partialPossibility
    # On transforme possibility en array numpy pour la convénience
    possibility = np.array(possibility)
    possibility = possibility.reshape(1, possibility.shape[0])  # Pour éviter des bugs à la concaténation

    return possibility

def MakeNewPartialPossibility(possIndex, oldPartialPossibility, currentNumber):  # Renvoie newPartialPossibility
    '''
    possIndex indique la combien-t-ième possibilité est-ce qu'on est en train de faire
    '''
    # On insère les croix (quand i = 0 il n'y en a pas, car on place notre nombre tout à gauche)
    newPartialPossibility = oldPartialPossibility
    for k in range(possIndex):
        newPartialPossibility.append(2)
    # Puis on ajoute notre nombre
    for k in range(currentNumber):
        newPartialPossibility.append(1)

    return newPartialPossibility

def CheckErrorPartialPossibility(partialPossibility, gridLine):  # Renvoie error
    # On vérifie que la possibilité partielle correspond à ce qui est déjà connu sur la grille
    for i, cell in enumerate(partialPossibility):
        # S'il y a une différence avec la grille, we not good
        if (gridLine[i] != 0) & (cell != gridLine[i]):
            return True

    # Si tout s'est bien passé
    return False

def FindNbPossibilities(numbersLeft, gridLineLength, partialPossibilityLength):
    spaceNeeded = sum(numbersLeft) + (
                len(numbersLeft) - 1)  # l'espace que prends le remplissage + l'espace que prennent les croix
    spaceLeft = gridLineLength - partialPossibilityLength  # l'espace qui n'est pas pris par "partialPossibility
    return spaceLeft + 1 - spaceNeeded  # le nombre de placement possibles pour notre nombre courant

def Pause():
    global pause
    pause = True
    while pause & pauseMod:
        Draw.CheckUserInput()
    pause = False # Au cas où on sorte pcq pauseMod est passé à False

# ---------- Utiles ----------
def RemoveDuplicatesFromList(listyBoy):
    # Transformer en dict enlève les duplications pcq il peut pas y avoir 2 fois la même clé
    return list(dict.fromkeys(listyBoy))










