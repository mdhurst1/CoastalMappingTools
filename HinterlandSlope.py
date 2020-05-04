"""
Driver for assessment of future shoreline change in Scotland
Bruun Rule approach

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

"""

import pickle, pathlib
import geopandas as gp
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent
NationalDEMPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2Final/99_NationalData/OSTerrain5")
OutputPath = WorkingPath/"FinalNationalRun"

RowName = "Cell_2a"

# this checks to see whether coast object already exists
Filename2SaveCoast = OutputPath / (RowName+"_Change.pydata")

try:
    CellCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object ", Filename2SaveCoast)

except:
    print("Fail")

for Transect in CellCoast.CoastLines[0].Transects:
    if (Transect.HinterlandSlope):
        if (Transect.HinterlandSlope < Transect.ShorefaceSlope):
            print(Transect.ID)
            print(Transect.ShorefaceSlope, Transect.HinterlandSlope)