# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 11:25:01 2019

@author: mh322u
"""

import pickle
import pathlib
from Coast import *

# define file names for analysis
Folder = "C:\\Users\\mh322u\\OneDrive - University of Glasgow\\Projects\\DynamicCoast2\\WP1_TopographicAnalysis\\"
Site = "Montrose"
SiteFolder = Folder+Site+"\\"
PlotFolder = SiteFolder+"Plots\\" 
TransectsFolder = SiteFolder+"Transects\\"
LineShp = "Montrose_CoastTrend.shp"
DTM = "DTM_1m.tif"

# Montrose Mean High Water Springs
MHWS = 2.

# make folder for plots and transects if it doesnt already exist
p = pathlib.Path(PlotFolder)
p.mkdir(parents=True, exist_ok=True)
p = pathlib.Path(TransectsFolder)
p.mkdir(parents=True, exist_ok=True)

# set up a file name to save the coast object
Filename2SaveCoast = SiteFolder+ "Coast.pydata"
#Filename2SaveCoast = SiteFolder+ "Coast.pydata_DUMMY"

# this checks to see whether coast object already exists
try:
    ThisCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object " + Filename2SaveCoast)

except:
    print("Creating New Coast Object")
    
    # SET UP THE COAST
    ThisCoast = Coast(SiteFolder+LineShp)
    ThisCoast.SetMHWS(MHWS)
    
    # SIMPLIFY COASTLINE
    ThisCoast.MergeCoastLines()
    ThisCoast.SmoothCoastLines(WindowSize=51)
    ThisCoast.ReconfigureCoastLines("E")
    
    # WRITE COASTLINE TO SHAPEFILE
    ThisCoast.WriteCoastShp(SiteFolder+"Coast.shp")
    
    # GENERATE TRANSECTS
    ThisCoast.GenerateNormals(10.,200.,200.)
    ThisCoast.WriteTransectsShp(SiteFolder+"Transects.shp")
    ThisCoast.ExtractTransectTopography(SiteFolder+DTM)
    
    # SAVE ENTIRE COAST OBJECT
    print("Saving Coast Object as " + Filename2SaveCoast)
    with open(Filename2SaveCoast, 'wb') as PFile:
        pickle.dump(ThisCoast, PFile)
        
    # WRITE TRANSECTS TO CSV
    ThisCoast.WriteTransectsCSV(Folder=TransectsFolder)

## ANALYSE TRANSECTS
ThisCoast.FindRockyCoast()
ThisCoast.SetMHWS(MHWS)
ThisCoast.AnalyseTransectMorphology()
ThisCoast.AnalyseBarrierWidths([4.,5.,6.])

# SAVE
print("Saving Coast Object as " + Filename2SaveCoast)   
with open(Filename2SaveCoast, 'wb') as PFile:
        pickle.dump(ThisCoast, PFile)

    
## plot the results
#ThisCoast.PlotTransects(PlotFolder)

## write some stuff
ThisCoast.WriteCliffShp(SiteFolder+"Cliffs.shp")
ThisCoast.WriteBarrierShp(SiteFolder+"Barriers.shp")
ThisCoast.WriteTransectsShp(SiteFolder+"Transects.shp")
ThisCoast.WriteCrestLinesShp(SiteFolder+"CrestLines.shp")
ThisCoast.WriteCrestPointsShp(SiteFolder+"CrestPoints.shp")
ThisCoast.WriteFrontPointsShp(SiteFolder+"FrontPoints.shp")
ThisCoast.WriteExtremeLevelsShp(SiteFolder+"Extreme.shp")
