# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 11:25:01 2019

@author: mh322u
"""

import sys
import pickle
import pathlib
from Coast import *
sys.setrecursionlimit(10000)
#print(sys.getrecursionlimit)

# define file names for analysis
Folder = "C:\\Users\\mh322u\\OneDrive - University of Glasgow\\Projects\\DynamicCoast2\\WP1_TopographicAnalysis\\"
Site = "BayOfSkail"
SiteFolder = Folder+Site+"\\"
PlotFolder = SiteFolder+"Plots\\" 
LineShp = "Skail_CoastTrend.shp"
DTM = "Skail_DTM_25cm.tif"
WindowSize = 2001

# make folder for plots if it doesnt already exist
p = pathlib.Path(PlotFolder)
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
    
    # SIMPLIFY COASTLINE
    ThisCoast.MergeCoastLines()
    ThisCoast.SmoothCoastLines(WindowSize=WindowSize)
    ThisCoast.ReconfigureCoastLines("W")
    
    # WRITE COASTLINE TO SHAPEFILE
    ThisCoast.WriteCoastShp(SiteFolder+"Coast.shp")
    
    # GENERATE TRANSECTS
    ThisCoast.GenerateNormals(10.,100.,200.)
    ThisCoast.WriteTransectsShp(SiteFolder+"Transects.shp")
    ThisCoast.ExtractTransectTopography(SiteFolder+DTM)   
    
    # SAVE ENTIRE COAST OBJECT
    print("Saving Coast Object as " + Filename2SaveCoast)
    with open(Filename2SaveCoast, 'wb') as PFile:
        pickle.dump(ThisCoast, PFile)
        
## ANALYSE TRANSECTS
ThisCoast.AnalyseTransectMorphology()
ThisCoast.AnalyseBarrierWidths([4.,5.,6.])

# SAVE ENTIRE COAST OBJECT
print("Saving Coast Object as " + Filename2SaveCoast)
with open(Filename2SaveCoast, 'wb') as PFile:
    pickle.dump(ThisCoast, PFile)

# write transects

    
# plot the results
#ThisCoast.PlotTransects(PlotFolder)

# write some stuff
#ThisCoast.WriteBarrierShp(SiteFolder+"Barriers.shp")
#ThisCoast.WriteTransectsShp(SiteFolder+"Transects.shp")
#ThisCoast.WriteCrestLinesShp(SiteFolder+"CrestLines.shp")
#ThisCoast.WriteCrestPointsShp(SiteFolder+"CrestPoints.shp")
#ThisCoast.WriteFrontPointsShp(SiteFolder+"FrontPoints.shp")
#ThisCoast.WriteExtremeLevelsShp(SiteFolder+"Extreme.shp")

#ThisCoast.PlotTransects(PlotFolder)
#ThisCoast.WriteBarrierShp(SiteFolder+"Barriers.shp")

# barrier width at 5 m water
#ThisCoast.ExtractBarrierWidth(5.)