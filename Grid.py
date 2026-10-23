import numpy as np




def CreateRandomGrid(gridShape: (int, int), seed=None):
    if seed is not None:
        np.random.seed(seed)  # Il galère de ouf sur la seed 3 avec la taille 20x20
    grid = np.random.randint(0, 2, gridShape)
    return grid

# ---------- Recherche des nombres d'indication ----------
def FindNumbers(grid: np.array):
    guideNumbersAxis = [[], []]
    # On commence par parcourir les lignes
    for i in range(grid.shape[0]):
        line = list(grid[i, :].ravel())
        guideNumbersAxis[0].append(FindNumbersFromLine(line))
    # Puis les colonnes
    for j in range(grid.shape[1]):
        line = list(grid[:, j].ravel())
        guideNumbersAxis[1].append(FindNumbersFromLine(line))

    return guideNumbersAxis

def FindNumbersFromLine(line):
    chunk = 0  # désigne le nombre de cases qu'il y a à la suite dans la série
    currentList = []  # liste de nombres d'indication pour cette ligne, qui sera ajouté à
    # guideNumbersAxis[0] ou guideNumbersAxis[1] une fois complété
    for j in range(len(line)):
        if line[j] == 1:  # si la case est remplie
            # on ajoute 1 case remplie au compteur
            chunk += 1
        elif chunk > 0:
            # On ajoute le chunk à la liste
            currentList.append(chunk)
            # On reset le compteur
            chunk = 0
    # Si le dernier chunk n'a pas été validé à la sortie de la boucle, on le valide mtn
    if chunk > 0:
        currentList.append(chunk)
    # On peut enfin retourner le résultat
    return currentList
