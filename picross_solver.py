# Le but de se programme est de coder la grille, les numéros d'indication, et de créer automatiquement les numéros à partir d'une grille coloriée
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk

gridSize = (10,10)
winSize = (800,800)
canvasSize = (400,400)
grid = np.random.randint(0,2,gridSize)
gridPos = (winSize[0]/4, winSize[1]/4)
colGuideNumbers = []
linGuideNumbers = []


def findNumbers() :
    # On commence par parcourir les lignes
    for i in range(gridSize[0]) :
        line = grid[i,:].ravel()
        linGuideNumbers.append(findNumbersFromLine(line))
    # Puis les colonnes
    for j in range(gridSize[1]) :
        line = grid[:,j].ravel()
        colGuideNumbers.append(findNumbersFromLine(line))

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

def showGuideNumbers() :
    # On commence par les lignes
    nbLines = len(linGuideNumbers)
    maxNbNumbers = findMaxLength(linGuideNumbers)
    for i, numbers in enumerate(linGuideNumbers) :
        for j, number in enumerate(numbers) :
            text = tk.Label(window, text = str(number), justify = "center")
            x = j * gridPos[0] / maxNbNumbers
            y = gridPos[1] + i * canvasSize[1] / nbLines
            text.place(x = x, y = y)
    
    # Puis les colonnes
    nbColonnes = len(colGuideNumbers)
    maxNbNumbers = findMaxLength(colGuideNumbers)
    for i, numbers in enumerate(colGuideNumbers) :
        for j, number in enumerate(numbers) :
            text = tk.Label(window, text = str(number), justify = "center")
            x = gridPos[0] + i * canvasSize[0] / nbColonnes
            y = j * gridPos[1] / maxNbNumbers
            text.place(x = x, y = y)

def findMaxLength(listes):
    maxLength = 0
    for liste in listes :
        currentLength = len(liste)
        if currentLength > maxLength :
            maxLength = currentLength
    return maxLength


def screenRefresh() :
    window.update_idletasks()
    window.update()

def clic(mouseEvent) :
    # Pour avoir la position de la souris : mouseEvent.x ou mouseEvent.y
    return

# ----------------------------------------------
# ---------- Programme hors graphique ----------
# ----------------------------------------------

findNumbers()

# --------------------------------------
# ---------- Aspect graphique ----------
# --------------------------------------

window = tk.Tk()
window.geometry(f"{winSize[0]}x{winSize[1]}")
window.title("Picross Solver")
window["bg"] = "white"
window.resizable(height = False, width = False)

# Grid
canvas = tk.Canvas(window, width = canvasSize[0], height = canvasSize[1])
shape = grid.shape
for i in range( shape[0] ): # i = numéro de ligne
    for j in range( shape[1] ): # j = numéro de colonne
        if grid[i][j] == 1:
            # On rempli la case
            canvas.create_rectangle(canvasSize[0]*j/gridSize[0],
                                    canvasSize[1]*i/gridSize[1],
                                    canvasSize[0]*(j+1)/gridSize[0],
                                    canvasSize[1]*(i+1)/gridSize[1],
                                    width = 2, fill = "black")
        else:
            canvas.create_rectangle(canvasSize[0]*j/gridSize[0],
                                    canvasSize[1]*i/gridSize[1],
                                    canvasSize[0]*(j+1)/gridSize[0],
                                    canvasSize[1]*(i+1)/gridSize[1],
                                    width = 2, fill = "white")
canvas.place(x = winSize[0]/4, y = winSize[1]/4)

# Guide Numbers
showGuideNumbers()

window.mainloop()