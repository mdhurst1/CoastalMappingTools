# -*- coding: utf-8 -*-
"""
Driver for assessment of future shoreline change in Montrose
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
Filename2SaveCoast = WorkingPath / "MontroseChange.pydata"


# # this checks to see whether coast object already exists
try:
    MontroseCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object ", Filename2SaveCoast)

except:

    print("Creating New Coast Object")

    # SET UP THE COAST FROM -10m Contour
    MontroseCoast = Coast(str(WorkingPath / "Bathymetry" / "MTBathy_Montrose_Clip_Contour_BNG.shp"))
    MontroseCoast.GenerateTransectsFromContours(str(WorkingPath / "MHWS_Lines" / "OS_Montrose_MHWS.shp"),50.)
    
    # SAVE ENTIRE COAST OBJECT
    print("Saving Coast Object as ", Filename2SaveCoast)
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(MontroseCoast, PFile)

MontroseCoast.WriteTransectsShp(str(WorkingPath / "Montrose_Transects.shp"))

# find historic shoreline positions
# MontroseCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Montrose_MHWS_1890_FINAL.shp"))
# MontroseCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Montrose_MHWS_1970_FINAL.shp"))

# extract depth contours
# MontroseCoast.ExtractContours(str(WorkingPath / "Bathymetry" / "MTBathy_Scotland_Contour.shp"))

# build transects from contours
# Distance2Land = 100.
# Distance2Sea = 1000.
# MontroseCoast.RebuildTransectsFromContours(Distance2Land,Distance2Sea)
# MontroseCoast.WriteTransectsShp(str(WorkingPath / "Transects.shp"))

# SAVE ENTIRE COAST OBJECT
# print("Saving Coast Object as ", Filename2SaveCoast)
# with open(str(Filename2SaveCoast), 'wb') as PFile:
#    pickle.dump(MontroseCoast, PFile)

# SIMPLIFY COASTLINE?
# MontroseCoast.SmoothCoastLines()
# MontroseCoast.WriteCoastShp(str(WorkingPath / "Coast.shp"))

# MontroseCoast.MergeCoastLines()
# MontroseCoast.WritePointsShp(str(WorkingPath / "MontrosePoints.Shp"))

# find historic shoreline positions
#MontroseCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Montrose_MHWS_1890_FINAL.shp"))
#MontroseCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Montrose_MHWS_1970_FINAL.shp"))

#print("Saving Coast Object as ", Filename2SaveCoast)
#with open(str(Filename2SaveCoast), 'wb') as PFile:
#    pickle.dump(MontroseCoast, PFile)

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
