
"""
Testing.py
MDH, June 2019
"""

import numpy as np
import itertools
from Node import *
from Transect import *
from Line import *
from Coast import *

TESTFILE = "D:\\NCCA2\\StAndrews\\MHWS\\MHWS_2018.shp"
ThisCoast = Coast(TESTFILE)
#ThisCoast.MergeCoastlines()
#TESTFILE2 = "D:\\NCCA2\\StAndrews\\MHWS\\MHWS_2018_TEST.shp"
#ThisCoast.WriteCoastShp(TESTFILE2)

StartNodes = [CoastLine.Nodes[0] for CoastLine in ThisCoast.CoastLines]
EndNodes = [CoastLine.Nodes[-1] for CoastLine in ThisCoast.CoastLines]

JoinsList = np.zeros(len(StartNodes),dtype=int)-9999
JoinedList = np.zeros(len(StartNodes),dtype=int)-9999

for i, EndNode in enumerate(EndNodes):
    for j, StartNode in enumerate(StartNodes):
        if StartNode == EndNode:
            JoinsList[i] = j
            JoinedList[j] = i
            
print(JoinsList)
print(JoinedList)
StartList = np.where(JoinedList < 0)
print(StartList)
#mask = JoinList > -1
#sorted_indices = np.argsort(JoinList)
#sorted_filter = sorted_indices[mask]
#filtered_sorted_indices = sorted_indices[sorted_filter == True]
#print(filtered_sorted_indices)
