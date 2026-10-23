# Le but de se programme est de coder la grille, les numéros d'indication, et de créer automatiquement les numéros à partir d'une grille coloriée
import time

import Grid
import Draw
import Solver


def Test1() :
    gridShape = (20,20)
    solGrid = Grid.CreateRandomGrid(gridShape)
    guideNumbersAxis = Grid.FindNumbers(solGrid)
    Draw.InitWindow(solGrid, guideNumbersAxis)

    Solver.Solve(guideNumbersAxis, gridShape, _showTkinter=True, _pauseMod=False)

    Draw.LoopDisplay()

def TestTime():
    sizes = range(4, 30)
    seeds = range(20)
    timeMatrix = []  # axis 0 : sizes, axis 1 : seeds
    for size in sizes:
        shape = (size, size)
        print(f"Tests sur la taille : {shape}")
        timeList = []
        for seed in seeds:
            print(f"Test avec la seed : {seed}")
            grid = Grid.CreateRandomGrid(shape, seed)
            guideNumbersAxis = Grid.FindNumbers(grid)

            startChrono = time.time()
            solveRes = Solver.Solve(guideNumbersAxis, grid.shape, _showTkinter=True)
            endChrono = time.time()

            # On vérifie qu'il n'y a pas eus de problème à la résolution
            solved = solveRes[1]
            if solved:
                timeList.append(endChrono - startChrono)

        timeMatrix.append(timeList)

    return timeMatrix


Test1()

#print(TestTime())






