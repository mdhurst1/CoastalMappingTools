# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 11:25:01 2019

@author: mh322u
"""

import pickle
from Coast import *

# define file names for analysis
Folder = "D:\\NCCA2\\"
Site = "Montrose"
SiteFolder = Folder+Site+"\\"
LineShp = "Montrose_CoastTrend.shp"
DTM = "DTM_1m.tif"

# SET UP THE COAST
ThisCoast = Coast(SiteFolder+LineShp)

# SIMPLIFY COASTLINE
ThisCoast.MergeCoastLines()
ThisCoast.SmoothCoastLines()
ThisCoast.ReconfigureCoastLines("E")

# WRITE COASTLINE TO SHAPEFILE
ThisCoast.WriteCoastShp(SiteFolder+"Coast.shp")

# GENERATE TRANSECTS
ThisCoast.GenerateNormals(10.,100.,500.)
ThisCoast.WriteTransectsShp(SiteFolder+"Transects.shp")
ThisCoast.ExtractTransectTopography(DTM)

Filename2SaveCoast = SiteFolder+ "Coast.pydata"
with open(Filename2SaveCoast, 'wb') as PFile:
    pickle.dump(ThisCoast, PFile)