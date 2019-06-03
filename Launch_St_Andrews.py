# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 10:17:56 2019

@author: mh322u
"""

# import Coastal Morphology functions
from CoastalMorphology import *
from pathlib import Path

if __name__ == "__main__":
    
    # declare folder name for storing results
    Folder = "D:/NCCA2/StAndrews/"
    MHWS_Folder = Folder+"MHWS/"
    DTM_Folder = Folder+"DTM/"
    ResultsFolder = Folder+"CoastalMorphology/"
    
    #if os.path.exists(Folder) is False:
    #    os.mkdir(Folder)
        
    # declare some file names for representing the coast
    CoastLineShp = MHWS_Folder + "MHWS_2018_Dissolve.shp"
    MergedCoastLineShp = MHWS_Folder + "MHWS_2018_Merged.shp"
    SmoothCoastLineShp = MHWS_Folder + "MHWS_2018_Smooth.shp"
    CoastTransectsShp = MHWS_Folder + "MHWS_Smooth_transects.shp"
    
    # declare the DTM
    DTM = DTM_Folder+"StAn_2018_DTM.tif"
    
    # merge the coastline line segments shapefile to produce a single line segment
    if Path(MergedCoastLineShp).is_file() is False:
        MergeCoastline(Folder, CoastLineShp, MergedCoastLineShp)
    
    # launch smoothing of coastline
    WindowSize = 1001 # St Andrews
    if Path(SmoothCoastLineShp).is_file() is False:
        SmoothCoastline(CoastLineShp,SmoothCoastLineShp,WindowSize)
    
    # generate coastal normals
    Spacing = 50.
    Dist2Sea = 50.
    Dist2Land = 200.
    if Path(CoastTransectsShp).is_file() is False:
        NoTransects = GenerateCoastalNormals(SmoothCoastLineShp,Spacing,Dist2Land,Dist2Sea)
    
    # extract swath profiles
    SwathDist = 1. # 1/2 width of swath profile in map units (probably metres)
    LastSwath = ResultsFolder + "SwathProfs/" + "Swath_"+str(NoTransects-1)+".csv"
    if Path(LastSwath).is_file() is False:
        ExtractSwathProfiles(Folder,CoastTransectsShp,DTM,SwathDist)
    
    # analyse swath profiles to create transect profiles
    HERE
    TransectProfilesIDW(Folder,CoastTransectsShp,DTM,SwathDist)
    
    # plot the resulting profiles
    #PlotProfiles(Folder,CoastTransectsShp)
    
    # analyse barrier morphology
    FindBarrierPosition(Folder,CoastTransectsShp)