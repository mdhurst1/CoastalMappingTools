
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
ThisCoast.MergeCoastLines()
TESTFILE2 = "D:\\NCCA2\\StAndrews\\MHWS\\MHWS_2018_Merge.shp"
ThisCoast.WriteCoastShp(TESTFILE2)
ThisCoast.SmoothCoastlines()
TESTFILE3 = "D:\\NCCA2\\StAndrews\\MHWS\\MHWS_2018_Smooth.shp"
ThisCoast.WriteCoastShp(TESTFILE3)
ThisCoast.GenerateNormals()

#StartNodes = [CoastLine.Nodes[0] for CoastLine in ThisCoast.CoastLines]
#EndNodes = [CoastLine.Nodes[-1] for CoastLine in ThisCoast.CoastLines]#

#JoinsList = np.zeros(len(StartNodes),dtype=int)-9999
#JoinedList = np.zeros(len(StartNodes),dtype=int)-9999

#for i, EndNode in enumerate(EndNodes):
#    for j, StartNode in enumerate(StartNodes):
#        #print(i, EndNode.X, EndNode.Y, j, StartNode.X, StartNode.Y)
#        if i == j:
#            continue
#        
#        if StartNode == EndNode:
#            JoinsList[i] = j
#            JoinedList[j] = i##
#
#        (i [i for i, x in enumerate(StartNodes) if x==StartNode]
#print(i, for i,)            
#print(JoinsList)
#print(JoinedList)
#StartList = np.where(JoinedList < 0)
#print(StartList)
#mask = JoinList > -1
#sorted_indices = np.argsort(JoinList)
#sorted_filter = sorted_indices[mask]
#filtered_sorted_indices = sorted_indices[sorted_filter == True]
#print(filtered_sorted_indices)
