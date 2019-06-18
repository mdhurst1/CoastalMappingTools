
"""
Testing.py
MDH, June 2019
"""

import numpy as np
from Node import *
from Transect import *
from Line import *
from Coast import *

x = 1
y = 2
ID = "test"

ThisNode = Node(ID,x,y)
print(ThisNode)

x1 = 5
x2 = 4
y1 = 7
y2 = 5

ThisTransect = Transect(ID,x1,y1,x2,y2)
print(ThisTransect)

X = np.arange(0.,2.*np.pi,0.1)
Y = np.sin(X)

ThisLine = Line(ID, X, Y)
print(ThisLine)

TESTFILE = "D:\\NCCA2\\StAndrews\\MHWS\\MHWS_2018.shp"
ThisCoast = Coast(TESTFILE)
print(ThisCoast)