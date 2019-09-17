# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 11:25:01 2019

@author: mh322u
"""

import traceback

import sys
import pickle
import pathlib
from Coast import *

#sys.setrecursionlimit(10000)
#print(sys.getrecursionlimit)

# define file names for analysis
Folder = "/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/WS1_Natural_Flood_Defences/"
Site = "StAndrews"
SiteFolder = Folder+Site+"/"
PlotFolder = SiteFolder+"Plots/" 
LineShp = "MHWS_2018_Smooth.shp"
DTM = "StAn_2018_DTM_1m.tif"
WindowSize = 2001

# Montrose Mean High Water Springs
MHWS = 2.5

# make folder for plots if it doesnt already exist
p = pathlib.Path(PlotFolder)
p.mkdir(parents=True, exist_ok=True)

# set up a file name to save the coast object
Filename2SaveCoast = SiteFolder+ "Coast.pydata"

# this checks to see whether coast object already exists
try:
    ThisCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object " + Filename2SaveCoast)

except:
    print("Creating New Coast Object")
    
    # SET UP THE COAST
    ThisCoast = Coast(SiteFolder+LineShp)
    
    # SIMPLIFY COASTLINE
    #ThisCoast.MergeCoastLines()
    #ThisCoast.SmoothCoastLines(WindowSize=WindowSize)
    ThisCoast.ReconfigureCoastLines("E")
    
    # WRITE COASTLINE TO SHAPEFILE
    #ThisCoast.WriteCoastShp(SiteFolder+"Coast.shp")
    
    # GENERATE TRANSECTS
    ThisCoast.GenerateTransectsNormals(10.,200.,400.)
    ThisCoast.WriteTransectsShp(SiteFolder+"Transects.shp")
    ThisCoast.ExtractTransectTopography(SiteFolder+DTM)   
    
    # SAVE ENTIRE COAST OBJECT
    print("Saving Coast Object as " + Filename2SaveCoast)
    with open(Filename2SaveCoast, 'wb') as PFile:
        pickle.dump(ThisCoast, PFile)

## ANALYSE TRANSECTS
#ThisCoast.FindRockyCoast()
#ThisCoast.SetMHWS(MHWS)
#ThisCoast.AnalyseTransectMorphology()
#ThisCoast.AnalyseBarrierWidths([4.,5.,6.])

# SAVE ENTIRE COAST OBJECT
#print("Saving Coast Object as " + Filename2SaveCoast)
#with open(Filename2SaveCoast, 'wb') as PFile:
#    pickle.dump(ThisCoast, PFile)

# write transects
    
# plot the results
ThisCoast.PlotTransects(PlotFolder)

# write some stuff
ThisCoast.WriteCoastShp(SiteFolder+"Coast.shp")
ThisCoast.WriteTransectsShp(SiteFolder+"Transects.shp")
ThisCoast.WriteCliffShp(SiteFolder+"Cliffs.shp")
ThisCoast.WriteBarrierShp(SiteFolder+"Barriers.shp")
ThisCoast.WriteCrestLinesShp(SiteFolder+"CrestLines.shp")
ThisCoast.WriteCrestPointsShp(SiteFolder+"CrestPoints.shp")
ThisCoast.WriteFrontPointsShp(SiteFolder+"FrontPoints.shp")
ThisCoast.WriteExtremeLevelsShp(SiteFolder+"Extreme.shp")