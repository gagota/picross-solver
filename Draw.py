import tkinter as tk
import tkinter.font as tkfont
import numpy as np

import Solver


# ---------- Paramètres ----------
winSize = (1600,800)
showProbas = False

gridDrawSize = (min(winSize) / 2, min(winSize) / 2)
solGridPos = (gridDrawSize[0]/2, gridDrawSize[1]/2)
searchGridPos = (gridDrawSize[0]*5/2, gridDrawSize[1]/2)

window = None

# ---------- Info ----------

def InitWindow(solGrid, guideNumbersAxis) :
    global window
    # Window settings
    window = tk.Tk()
    window.geometry(f"{winSize[0]}x{winSize[1]}")
    window.title("Picross Solver")
    window["bg"] = "white"
    window.resizable(height=False, width=False)

    # Grids
    # solution grid
    ShowGrid(solGrid, gridDrawSize, solGridPos)
    # Guide Numbers
    showGuideNumbers(guideNumbersAxis)

    # Pause Things
    # Binds
    window.bind("<Button-1>", Clic) # Joue "clic" quand le clic gauche de la souris est appuyé
    window.bind("<space>", SpacePressed)
    window.bind("<Return>", ReturnPressed)
    # UI
    pauseModLabel = tk.Label(window, text = f"pause mod : {Solver.pauseMod}")
    pauseLabel = tk.Label(window, text = f"Pause : {Solver.pause}")
    pauseModLabel.pack(side=tk.TOP, anchor=tk.NW)
    pauseLabel .pack(side=tk.TOP, anchor=tk.NW)

def LoopDisplay():
    global window
    window.mainloop()

def ShowStep(searchGrid) :
    ShowGrid(searchGrid, gridDrawSize, searchGridPos, showProbas)
    ScreenRefresh()

def ScreenRefresh() :
    window.update_idletasks()
    window.update()

def ShowGrid(grid:np.array, drawShape, position, showProbas = False) :
    global currentProbas
    global window
    canvas = tk.Canvas(window, width = drawShape[0], height = drawShape[1])
    shape = grid.shape
    for i in range( shape[0] ): # i = numéro de ligne
        for j in range( shape[1] ): # j = numéro de colonne
            # On calcule les coordonées de la case
            x1 = drawShape[0]*j/shape[0]
            y1 = drawShape[1]*i/shape[1]
            x2 = drawShape[0]*(j+1)/shape[0]
            y2 = drawShape[1]*(i+1)/shape[1]

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

def showGuideNumbers(guideNumbersAxis) :
    global window
    # On commence par les lignes
    nbLines = len(guideNumbersAxis[0])
    maxNbNumbers = findMaxLength(guideNumbersAxis[0])
    fontSize = int( (gridDrawSize[1] / nbLines)  * (3/4) /2) # "4/3" c'est pour convertir les pixels en points
    font = tkfont.Font(size = fontSize)

    # On set le canvas sur lequel on va placer les nombres
    borderWidth = 2
    canvasSize = (solGridPos[0], gridDrawSize[1])
    canvasPos = (0,solGridPos[1])
    canvas = tk.Canvas(window, width = canvasSize[0], height = canvasSize[1] + borderWidth+1)

    for i, numbers in enumerate(guideNumbersAxis[0]) :
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
    nbColonnes = len(guideNumbersAxis[1])
    maxNbNumbers = findMaxLength(guideNumbersAxis[1])
    fontSize = int( (gridDrawSize[1] / nbLines)  * (3/4) /2) # "4/3" c'est pour convertir les pixels en points
    font = tkfont.Font(size = fontSize)

    # On set le canvas sur lequel on va placer les nombres
    borderWidth = 2
    canvasSize = (gridDrawSize[0], solGridPos[1])
    canvasPos = (solGridPos[0], 0)
    canvas = tk.Canvas(window, width = canvasSize[0]  + borderWidth+1, height = canvasSize[1])

    for j, numbers in enumerate(guideNumbersAxis[1]) :
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

# ---------- Utile ----------
def findMaxLength(listes):
    maxLength = 0
    for liste in listes:
        currentLength = len(liste)
        if currentLength > maxLength:
            maxLength = currentLength
    return maxLength

# ---------- Interaction ----------
def Clic(mouseEvent) :
    # Pour avoir la position de la souris : mouseEvent.x ou mouseEvent.y
    # Si on a cliqué, on veut passer à l'itération suivante en mode pause
    if Solver.pauseMod :
        Solver.pause = False

def SpacePressed(KeyEvent) :
    # On active ou désactive le mode pause
    Solver.pauseMod = not Solver.pauseMod

def ReturnPressed(keyEvent) :
    Solver.pause = False

def CheckUserInput() :
    # On a juste besoin de refresh la fenêtre pour check si on appuie sur une touche
    ScreenRefresh()




