# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 10:17:56 2019

@author: mh322u
"""

# import Coastal Morphology functions
from archive.CoastalMorphology import *
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
    CoastTransectsShp = MHWS_Folder + "MHWS_2018_Smooth_transects.shp"
    
    # declare the DTM
    DTM = DTM_Folder+"StAn_2018_DTM.tif"
    
    # merge the coastline line segments shapefile to produce a single line segment
    if not Path(MergedCoastLineShp).is_file():
        MergeCoastline(CoastLineShp, MergedCoastLineShp)
    
    # launch smoothing of coastline
    WindowSize = 1001 # St Andrews
    if not Path(SmoothCoastLineShp).is_file():
        SmoothCoastline(CoastLineShp,SmoothCoastLineShp,WindowSize)
    
    # generate coastal normals
    Spacing = 50.
    Dist2Sea = 50.
    Dist2Land = 200.
    if not Path(CoastTransectsShp).is_file():
        NoTransects = GenerateCoastalNormals(SmoothCoastLineShp,Spacing,Dist2Land,Dist2Sea)
    
    # extract swath profiles
    SwathDist = 1. # 1/2 width of swath profile in map units (probably metres)
    LastSwath = ResultsFolder + "SwathProfs/" + "Swath_"+str(NoTransects-1)+".csv"
    if not Path(LastSwath).is_file():
        ExtractSwathProfiles(Folder,CoastTransectsShp,DTM,SwathDist)
    
    # analyse swath profiles to create transect profiles
    LastProf = ResultsFolder + "Profiles/" + "Profile_"+str(NoTransects-1)+".csv"
    if not Path(LastProf).is_file():
        TransectProfilesIDW(Folder,CoastTransectsShp,DTM,SwathDist)
    
    # plot the resulting profiles
    LastProf = ResultsFolder + "Profiles/" + "Profile_"+str(NoTransects-1)+".png"
    if not Path(LastProf).is_file():
        PlotProfiles(Folder,CoastTransectsShp)
    
    # analyse barrier morphology
    FindBarrierPosition(ResultsFolder,CoastTransectsShp)