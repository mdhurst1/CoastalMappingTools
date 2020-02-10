# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 11:25:01 2019

@author: mh322u
"""

import pickle
import pathlib
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent

# define file names for analysis
Site = "Tiree"
SitePath = pathlib.Path(WorkingPath / Site)
PlotPath = pathlib.Path(SitePath / "Plots")
TransectsPath = pathlib.Path(SitePath / "Transects")

LineShp = "Tiree_Modern_SinglePart.shp"
DTM = "Tiree_2006_DTM.tif"

# make folder for plots and transects if it doesnt already exist
p = pathlib.Path(PlotPath)
p.mkdir(parents=True, exist_ok=True)
p = pathlib.Path(TransectsPath)
p.mkdir(parents=True, exist_ok=True)

# set up a file name to save the coast object
Filename2SaveCoast = Site + ".pydata"

# this checks to see whether coast object already exists
try:
    ThisCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object " + Filename2SaveCoast)

except:
    print("Creating New Coast Object")
    
    # SET UP THE COAST
    ThisCoast = Coast(str(SitePath / LineShp))
    
    # SIMPLIFY COASTLINE
    ThisCoast.ReverseCoastLines()
    ThisCoast.SmoothCoastLines(WindowSize=101, NoSmooths=3)
    
    # WRITE COASTLINE TO SHAPEFILE
    ThisCoast.WriteCoastShp(str(SitePath / (Site+"_SmoothedCoast.shp")))
    
    # GENERATE TRANSECTS
    ThisCoast.GenerateTransectsNormals(10.,200.,500., CheckTopology=False)
    ThisCoast.WriteTransectsShp(str(SitePath / "Transects.shp"))
    ThisCoast.ExtractTransectTopography(str(SitePath / DTM))
    
    # SAMPLE MHWS
    ThisCoast.SampleMHWSElevation(str(Folder / "MHWS" / "scotland_mhws_elev.tif"))

    # SAVE ENTIRE COAST OBJECT
    print("Saving Coast Object as " + Filename2SaveCoast)
    with open(str(SiteFolder / Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(ThisCoast, PFile)
        
    # WRITE TRANSECTS TO CSV
    ThisCoast.WriteTransectsCSV(Folder=str(TransectsFolder))

## ANALYSE TRANSECTS
#ThisCoast.FindRockyCoast()
#ThisCoast.AnalyseTransectMorphology()
#ThisCoast.AnalyseBarrierWidths([4.,5.,6.])

# SAVE
#print("Saving Coast Object as " + Filename2SaveCoast)   
#with open(Filename2SaveCoast, 'wb') as PFile:
#        pickle.dump(ThisCoast, PFile)

    
## plot the results
#ThisCoast.PlotTransects(PlotFolder)

## write some stuff
#ThisCoast.WriteCliffShp(SiteFolder+"Cliffs.shp")
#ThisCoast.WriteBarrierShp(SiteFolder+"Barriers.shp")
#ThisCoast.WriteTransectsShp(SiteFolder+"Transects.shp")
#ThisCoast.WriteCrestLinesShp(SiteFolder+"CrestLines.shp")
#ThisCoast.WriteCrestPointsShp(SiteFolder+"CrestPoints.shp")
#ThisCoast.WriteFrontPointsShp(SiteFolder+"FrontPoints.shp")
#ThisCoast.WriteExtremeLevelsShp(SiteFolder+"Extreme.shp")
