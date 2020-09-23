"""
Driver for assessment of future shoreline change in Scotland
Bruun Rule approach

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

"""

import pickle, pathlib, sys
import geopandas as gp
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent
NationalDEMPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2Final/99_NationalData/OSTerrain5")
OutputPath = WorkingPath/"ShorelineRun_Inner"

# get all inner cells to loop through
InnerCells = gp.read_file(WorkingPath / "MHWS_Originals_Smartest" / "WS2_inner_needed_polygons_singles.shp")

# and historic MHWS datasets
MHWS_1890 = gp.read_file(WorkingPath / "MHWS_Originals_Smartest" / "Scotland_MHWS_1890_Final.shp")
MHWS_1970 = gp.read_file(WorkingPath / "MHWS_Originals_Smartest" / "Scotland_MHWS_1970_Final.shp")
MHWS_Soft = gp.read_file(WorkingPath / "MHWS_Originals_Smartest" / "MHWS_OS_smartest2020_WS2_inner.shp")
MHWS_Modern = gp.read_file(WorkingPath / "MHWS_Originals_Smartest" / "MHWS_OS_smartest2020_WS2_inner_dissolved.shp")
MHWS_LiDAR = gp.read_file(WorkingPath / "MHWS_Originals_Smartest" / "Scotland_MHWS_Modern_Lidar.shp")


# set the minimum length
MinLength = 100.

# set the transect spacing (in m)
TransectSpacing = 10.
SmoothingWindowSize = 21
NoSmooths = 50


def ClipLines2Poly(LinesGDF,PolyGDF):

    IntersectionGeometry = LinesGDF.intersection(PolyGDF)
    Clipped = LinesGDF.copy()
    Clipped["geometry"] = IntersectionGeometry
    return Clipped[~Clipped.geometry.is_empty]

for index, Row in InnerCells.iterrows():

    # Intersection to isolate bathy for each cell
    Old = ClipLines2Poly(MHWS_1890, Row.geometry)
    Inter = ClipLines2Poly(MHWS_1970, Row.geometry)
    Soft = ClipLines2Poly(MHWS_Soft, Row.geometry)
    Modern = ClipLines2Poly(MHWS_Modern, Row.geometry)
    LiDAR = ClipLines2Poly(MHWS_LiDAR, Row.geometry)
    
    # Save these to new files
    RowName = "Cell_" + Row.Cell_sub
    
    try:
        Old.to_file(WorkingPath / "MHWS_Originals_Smartest" / (Row.id + "Inner_MHWS_1890.shp"))
    except:
        print("Unable to write 1890s for " + Row.id)
    
    try:
        Inter.to_file(WorkingPath / "MHWS_Originals_Smartest" / (Row.id + "Inner_MHWS_1970.shp"))
    except:
        print("Unable to write 1970s for " + Row.id)
    
    try:    
        Soft.to_file(WorkingPath / "MHWS_Originals_Smartest" / (Row.id + "Inner_Modern_Soft.shp"))
    except:
        print("Unable to write soft for " + Row.id)
    
    try:
        Modern.to_file(WorkingPath / "MHWS_Originals_Smartest" / (Row.id + "Inner_Modern_Final.shp"))
    except:
        print("Unable to write modern for " + Row.id)
        
    try:
        LiDAR.to_file(WorkingPath / "MHWS_Originals_Smartest" / (Row.id + "Inner_Modern_LiDAR.shp"))
    except:
        print("Unable to write LiDAR for " + Row.id)
        

# loop through each cell
for index, Row in InnerCells.iterrows():

    # print cell to screen
    # CellSub = Row.Cell_sub
    print("\nRUNNING CELL", Row.id)
    RowName = "InnerCell_" + Row.id
    
    # # this checks to see whether coast object already exists
    Filename2SaveCoast = OutputPath / (RowName+"_Change.pydata")
    
    # get soft coast position as most recent
    ModernPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Final.shp")
    SoftPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft.shp")
    LiDARPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_LiDAR.shp")
    OldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp")
    QuiteOldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970.shp")
    
    if not ModernPath.is_file():
        print("No soft baseline")
        continue
    elif not SoftPath.is_file():
        print("No Soft")
        continue
        
    try:
        CellCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
        print("Loaded Coast Object ", Filename2SaveCoast)

    except:
        print("Creating New Coast Object")

        # SET UP THE COAST FROM -10m Contour
        CellCoast = Coast(str(ModernPath), MinLength=MinLength)
    
    if not CellCoast.BuiltTransects:
        
        # may need to think carefully about how much to smooth
        CellCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize,NoSmooths=NoSmooths)
        
        CellCoast.CheckOrientation(str(SoftPath),str(BathyPath))
        
        # write smoothed coast/bathy to file
        CellCoast.WriteCoastShp(str(OutputPath / (RowName + "_Smoothed_Baseline.shp")))

        CellCoast.GenerateTransects(TransectSpacing, 200, 200, CheckTopology=False)
        
        CellCoast.BuiltTransects = True
        
        # SAVE ENTIRE COAST OBJECT
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    if not CellCoast.GotHistoricShorelines:
        
        if not OldPath.is_file():
            print("No 1890s MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(OldPath),Reset=True)
        
        if not QuiteOldPath.is_file():
            print("No 1970s MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(QuiteOldPath))
        
        if not SoftPath.is_file():
            print("No soft MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(SoftPath))
            
        if not LiDARPath.is_file():
            print("No LiDAR MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(LiDARPath))
            
        #### get MHWS for each transect
        CellCoast.SampleMHWSElevation(str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif"))
    
        #### get historical rate of relative sea level change
        CellCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_NEngland_RSLR_Modern_BNG.tif"))
    
        ### get future relative sea level time series
        CellCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL"))
        
        CellCoast.GotHistoricShorelines = True
        
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    if not CellCoast.SampledDEMs:
    
        # Extend transects landward by a fixed distance and sample DEMs
        HinterlandDistance = 200
        CellCoast.ExtendTransects2Hinterland(HinterlandDistance)
        CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects.shp")))
        CellCoast.FindDEM(str(NationalDEMPath / "OSTerrain5_fullcoastindex.shp"))
        CellCoast.ExtractTransectTopography()
        
        CellCoast.SampledDEMs = True
        
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
            
    if not CellCoast.PredictedFutureShorelines:    
    
        ## predict future shorelines
        CellCoast.GetShorefaceSlopes(str(BathyPath))
        CellCoast.PredictFutureShorelines(SIMPLE FLAG HERE)
        CellCoast.PredictedFutureShorelines = True
    
        # write future shorelines
        CellCoast.WriteFutureShorelinesShp(str(OutputPath / (RowName + "_Future.shp")),Smooth=True)
        CellCoast.WriteFutureUncertaintyShp(str(OutputPath / (RowName + "_Uncertainty_2100.shp")))
        CellCoast.WriteFutureUncertaintyShp(str(OutputPath / (RowName + "_Uncertainty_2050.shp")),Year=2050)
        CellCoast.WriteErodedAreaShp(str(OutputPath / (RowName + "_FutureErosion.shp")))
    
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
        
    #CellCoast.WriteFutureShorelineSegmentsShp(str(WorkingPath / "CoastalCells" / (RowName + "_FutureSegments.shp")))
    

    

