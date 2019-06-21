
"""
Testing.py
MDH, June 2019
"""

import numpy as np
import pickle
from Coast import *

# define files
MHWS = "D:\\NCCA2\\StAndrews\\MHWS\\MHWS_2018.shp"
DEM = "D:\\NCCA2\\StAndrews\\DTM\\StAn_2018_DTM.tif"

# run analysis
ThisCoast = Coast(MHWS)
ThisCoast.MergeCoastLines()
ThisCoast.SmoothCoastLines()
ThisCoast.ReconfigureCoastLines("E")
ThisCoast.GenerateNormals(10.,100.,500.)
ThisCoast.ExtractTransectTopography(DEM)

Filename2SaveCoast = "d:\\NCCA2\\StAndrews\\Coast.pydata"
with open(Filename2SaveCoast, 'wb') as PFile:
    pickle.dump(ThisCoast, PFile)
    

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
