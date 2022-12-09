#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 19 15:46:28 2022

@author: mhurst
"""

import pickle, pathlib
import geopandas as gp
from Coast import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Customise figure font style
# Set up fonts for plots
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['arial']
rcParams['font.size'] = 12
rcParams['text.usetex'] = True

# define file names for analysis
WorkingPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/Cullipool/")
DC2Path = WorkingPath.parent / ("WS2_National_Scale_Change/")
DEMPath = WorkingPath / ("UAV_Survey_19_4_22/Luing/1_dsm/Luing2_19th_April22_dsm.tif")
NewSurface = WorkingPath / "New_Surface" / "proposed_surface.tif"
ProjectName = "Cullipool"

# load a transect
Filename = WorkingPath / "Geometry" / (ProjectName+"_Geometry.pydata")
Cst = pickle.load( open( Filename, "rb" ) )

# set a line and a transect if needed
LineID = "0"
TransectID = "36"

# get line
Lns = Cst.CoastLines
Ln = [Ln for Ln in Lns if Ln.ID == LineID][0]

# get transect
Trs = Ln.Transects
Tr = [Tr for Tr in Trs if Tr.ID == TransectID][0]

# sample the revised DTM
Tr.SampleDEM(NewSurface)

# create figure
fig = plt.figure(1,figsize=(6,3))
ax = fig.add_subplot(111)
        
#replot
Mask = (Tr.Elevation > -10)
DistanceMask = Tr.Distance[Mask]
ElevMask = Tr.Elevation[Mask]
plt.plot(DistanceMask, ElevMask, 'k-', label="Current Topography")

Mask2 = (Tr.Elevation2 > -10)
NDistance = Tr.Distance2[Mask2].tolist()
NElev = Tr.Elevation2[Mask2].tolist()
NDistance.insert(0, DistanceMask[0])
NElev.insert(0, ElevMask[0])

plt.plot(NDistance,NElev,'k--',label="Proposed Surface")

plt.xlabel("Distance (m)")
plt.ylabel("Elevation (m)")

plt.legend(loc=4)

plt.title("Transect " + TransectID)
plt.tight_layout()
plt.savefig(str(WorkingPath)+"Transect"+ str(TransectID)+".png", dpi=300)
plt.show()