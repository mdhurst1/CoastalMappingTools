# -*- coding: utf-8 -*-
"""
Driver for assessment of future shoreline change in Scotland
Bruun Rule approach

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

"""

import sys, pickle, pathlib, shapefile
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent

# Folder = r"../"
# Site = "StAndrews_1m_2018"
# SiteFolder = Folder+Site+"\\"
# PlotFolder = SiteFolder+"Plots\\" 
# LineShp = "MHWS_2018_Smooth.shp"
# DTM = "StAn_2018_DTM_1m.tif"
# WindowSize = 2001

# # Montrose Mean High Water Springs
# MHWS = 2.5

# set up a file name to save the coast object
Filename2SaveCoast = WorkingPath / "ScottishCoast.pydata"


# # this checks to see whether coast object already exists
try:
    ScotlandCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object ", Filename2SaveCoast)

except:

    print("Creating New Coast Object")

    # SET UP THE COAST
    ScotlandCoast = Coast(str(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_Modern_FINAL.shp"))
    print(ScotlandCoast)

    # GENERATE TRANSECTS
    ScotlandCoast.GenerateNormals(10.,20.,20.)

    # SAVE ENTIRE COAST OBJECT
    print("Saving Coast Object as ", Filename2SaveCoast)
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(ScotlandCoast, PFile)

# SIMPLIFY COASTLINE?
# ScotlandCoast.MergeCoastLines()
# ScotlandCoast.WritePointsShp(str(WorkingPath / "ScotlandPoints.Shp"))

# find historic shoreline positions
ScotlandCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_1890_FINAL.shp"))
ScotlandCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_1970_FINAL.shp"))

print("Saving Coast Object as ", Filename2SaveCoast)
with open(str(Filename2SaveCoast), 'wb') as PFile:
    pickle.dump(ScotlandCoast, PFile)

# generate new transects based on historic shoreline positions?

# find -10m contour on each transect

#ThisCoast.SmoothCoastLines(WindowSize=WindowSize)
#     ThisCoast.ReconfigureCoastLines("E")
    
#     # WRITE COASTLINE TO SHAPEFILE
#     #ThisCoast.WriteCoastShp(SiteFolder+"Coast.shp")
    
#     # GENERATE TRANSECTS
#     ThisCoast.GenerateNormals(10.,100.,200.)
#     ThisCoast.WriteTransectsShp(SiteFolder+"Transects.shp")
#     ThisCoast.ExtractTransectTopography(SiteFolder+DTM)   
    
#     # SAVE ENTIRE COAST OBJECT
#     print("Saving Coast Object as " + Filename2SaveCoast)
#     with open(Filename2SaveCoast, 'wb') as PFile:
#         pickle.dump(ThisCoast, PFile)

# ## ANALYSE TRANSECTS
# #ThisCoast.FindRockyCoast()
# #ThisCoast.SetMHWS(MHWS)
# #ThisCoast.AnalyseTransectMorphology()
# #ThisCoast.AnalyseBarrierWidths([4.,5.,6.])

# # SAVE ENTIRE COAST OBJECT
# #print("Saving Coast Object as " + Filename2SaveCoast)
# #with open(Filename2SaveCoast, 'wb') as PFile:
# #    pickle.dump(ThisCoast, PFile)

# # write transects
    
# # plot the results
# ThisCoast.PlotTransects(PlotFolder)

# # write some stuff
# #ThisCoast.WriteCoastShp(SiteFolder+"Coast.shp")
# #ThisCoast.WriteTransectsShp(SiteFolder+"Transects.shp")
# #ThisCoast.WriteCliffShp(SiteFolder+"Cliffs.shp")
# #ThisCoast.WriteBarrierShp(SiteFolder+"Barriers.shp")
# #ThisCoast.WriteCrestLinesShp(SiteFolder+"CrestLines.shp")
# #ThisCoast.WriteCrestPointsShp(SiteFolder+"CrestPoints.shp")
# #ThisCoast.WriteFrontPointsShp(SiteFolder+"FrontPoints.shp")
# #ThisCoast.WriteExtremeLevelsShp(SiteFolder+"Extreme.shp")
