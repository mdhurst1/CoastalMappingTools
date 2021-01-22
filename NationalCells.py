# -*- coding: utf-8 -*-
"""
Organise coastal datasets for national change assessment based on coasta cells

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

Jan 2020

"""

import pathlib
import geopandas as gp

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent

### FUNCTIONALITY HERE TO SAMPLE FROM NATIONAL DATASETS BASED ON COASTAL CELLS ###
# open shapefile of coastal cells
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

# open shapefiles of -10m contour
BathyLines = gp.read_file(WorkingPath / "Bathymetry" / "Scotland_10m_Bathy_Contour_Simple.shp")

# open shpaefiles of MLWS
MLWS_Modern = gp.read_file(WorkingPath / "MLWS_Lines" / "OSMM_MLWS_2020.shp")

# and historic MHWS datasets
MHWS_1890 = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_1890_FINAL.shp")
MHWS_Inner_1890 = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_1890_FINAL_Inner.shp")
MHWS_1970 = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_1970_Final.shp")
MHWS_Inner_1970 = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_1970_Final_Inner.shp")
MHWS_Soft = gp.read_file(WorkingPath / "MHWS_Lines" / "MHWS_OS_smarter2020_soft.shp")
MHWS_Soft_Inner = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_Inner_Baseline_NoSaltmarsh.shp")
MHWS_OpenBaseline = gp.read_file(WorkingPath / "MHWS_Lines" / "MHWS_OS_smarter_dissolve.shp")
MHWS_InnerBaseline = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_Inner_Baseline_NoSaltmarsh_Dissolved.shp")
MHWS_LiDAR = gp.read_file(WorkingPath / "MHWS_Lines" / "DC2_Scotland_MHWS_Modern.shp")

def ClipLines2Poly(LinesGDF,PolyGDF):

    IntersectionGeometry = LinesGDF.intersection(PolyGDF)
    Clipped = LinesGDF.copy()
    Clipped["geometry"] = IntersectionGeometry
    return Clipped[~Clipped.geometry.is_empty]


for index, Row in Cells.iterrows():

    
    # Intersection to isolate bathy for each cell
    BathyClipped = ClipLines2Poly(BathyLines, Row.geometry)
    MLWSClipped = ClipLines2Poly(MLWS_Modern, Row.geometry)
    Old = ClipLines2Poly(MHWS_1890,Row.geometry)
    Old_Inner = ClipLines2Poly(MHWS_Inner_1890,Row.geometry)
    Inter = ClipLines2Poly(MHWS_1970,Row.geometry)
    Old_Inter = ClipLines2Poly(MHWS_Inner_1970,Row.geometry)
    Soft = ClipLines2Poly(MHWS_Soft,Row.geometry)
    Soft_Inner = ClipLines2Poly(MHWS_Soft_Inner, Row.geometry)
    Modern = ClipLines2Poly(MHWS_OpenBaseline,Row.geometry)
    LiDAR = ClipLines2Poly(MHWS_LiDAR, Row.geometry)
    Inner = ClipLines2Poly(MHWS_InnerBaseline, Row.geometry)
    
    # Save these to new files
    RowName = "Cell_" + Row.Cell_sub
    
    print(RowName)
    
    try:
        BathyClipped.to_file(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp"))
    except:
        print("Unable to write bathy for " + Row.Cell_sub)
    
    try:
        MLWSClipped.to_file(WorkingPath / "MLWS_Lines" / (RowName + "_MLWS.shp"))
    except:
        print("Unable to write MLWS for " + Row.Cell_sub)
        
    try:
        Old.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp"))
    except:
        print("Unable to write 1890s for " + Row.Cell_sub)
    
    try:
        Inter.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970.shp"))
    except:
        print("Unable to write 1970s for " + Row.Cell_sub)
        
    try:
        Old_Inner.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890_Inner.shp"))
    except:
        print("Unable to write inner 1890s for " + Row.Cell_sub)
    
    try:
        Old_Inter.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970_Inner.shp"))
    except:
        print("Unable to write inner 1970s for " + Row.Cell_sub)
    
    try:    
        Soft.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft.shp"))
    except:
        print("Unable to write soft for " + Row.Cell_sub)
        
    try:    
        Soft_Inner.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft_Inner.shp"))
    except:
        print("Unable to write soft inner for " + Row.Cell_sub)
    
    try:
        Modern.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_Open_Baseline.shp"))
    except:
        print("Unable to write modern for " + Row.Cell_sub)
        
    try:
        LiDAR.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_Modern_LiDAR.shp"))
    except:
        print("Unable to write LiDAR for " + Row.Cell_sub)
        
    try:
        Inner.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_Inner_Baseline.shp"))
    except:
        print("Unable to write Inner Baseline for " + Row.Cell_sub)