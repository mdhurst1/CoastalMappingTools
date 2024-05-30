# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 11:25:01 2019

@author: mh322u
"""

#import modules
import pickle
import pathlib
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent
SitePath = WorkingPath / "Montrose"
PlotPath = SitePath / "Plots/" 
TransectPath = SitePath / "Transects/"

#input data
LineShp = "Montrose_CoastTrend.shp"
DTM = "DTM_1m.tif"

# make folder for plots and transects if it doesnt already exist
p = pathlib.Path(PlotPath)
p.mkdir(parents=True, exist_ok=True)
p = pathlib.Path(TransectPath)
p.mkdir(parents=True, exist_ok=True)

# set up a file name to save the coast object
Filename2SaveCoast = str(SitePath / "Coast.pydata")

# this checks to see whether coast object already exists
try:
    ThisCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object " + Filename2SaveCoast)

except:
    print("Creating New Coast Object")
    
    # SET UP THE COAST
    ThisCoast = Coast(str(SitePath / LineShp))
    
    # SIMPLIFY COASTLINE
    ThisCoast.MergeCoastLines()
    ThisCoast.SmoothCoastLines(WindowSize=51)
    ThisCoast.ReconfigureCoastLines("E") # point to bathy for using on other coasts
    
    # WRITE COASTLINE TO SHAPEFILE
    ThisCoast.WriteCoastShp(str(SitePath / "Coast.shp"))
    
    # GENERATE TRANSECTS
    ThisCoast.GenerateTransects(10.,250.,500.)
    ThisCoast.WriteTransectsShp(str(SitePath / "Transects.shp"))
    ThisCoast.ExtractTransectTopographySwath(str(SitePath / DTM), 2.)
    
    #### get MHWS for each transect
    ThisCoast.SampleMHWSElevation(str(WorkingPath / "MHWS" / "scotland_mhws_elev.tif"))
    
    # SAVE ENTIRE COAST OBJECT
    print("Saving Coast Object as " + Filename2SaveCoast)
    with open(Filename2SaveCoast, 'wb') as PFile:
        pickle.dump(ThisCoast, PFile)
    
## ANALYSE TRANSECTS
ThisCoast.FindRockyCoast()
ThisCoast.AnalyseTransectMorphology()
ThisCoast.AnalyseBarrierWidths([4.,5.,6.])

## plot the results
ThisCoast.PlotTransects(str(PlotPath))

## write some stuff
ThisCoast.WriteCliffShp(str(SitePath / "Cliffs.shp"))
ThisCoast.WriteBarrierShp(str(SitePath / "Barriers.shp"))
ThisCoast.WriteTransectsShp(str(SitePath / "Transects.shp"))
ThisCoast.WriteCrestLinesShp(str(SitePath / "CrestLines.shp"))
ThisCoast.WriteCrestPointsShp(str(SitePath / "CrestPoints.shp"))
ThisCoast.WriteFrontPointsShp(str(SitePath / "FrontPoints.shp"))

ThisCoast.WriteBarriersTextFile(str(SitePath / "MontroseBarriers.csv"))
ThisCoast.WriteExtremeLevelsShp(str(SitePath / "Extreme.shp"))


# WRITE TRANSECTS TO CSV
ThisCoast.WriteTransectsCSV(Folder=str(TransectPath))

# TRANSECT CALLING