# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 11:25:01 2019

@author: mh322u
"""

import pickle
from Coast import *

# define file names for analysis
LineShp = "D:\\NCCA2\\Montrose\\Montrose_CoastTrend.shp"
DTM = "D:\\NCCA2\\Montrose\\DTM_1m.tif"

# run analysis
ThisCoast = Coast(LineShp)
ThisCoast.MergeCoastLines()
ThisCoast.SmoothCoastLines()
ThisCoast.ReconfigureCoastLines("E")
ThisCoast.GenerateNormals(10.,100.,500.)
ThisCoast.ExtractTransectTopography(DTM)

Filename2SaveCoast = "d:\\NCCA2\\StAndrews\\Coast.pydata"
with open(Filename2SaveCoast, 'wb') as PFile:
    pickle.dump(ThisCoast, PFile)