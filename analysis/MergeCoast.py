"""
Driver for assessment of foreshore width in Scotland
For finding beaches mostl likely to be visited post-Covid

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

"""

import pickle, pathlib, sys
import geopandas as gp
from CMT import Coast

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent
NationalDEMPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2Final/99_NationalData/OSTerrain5")
OutputPath = WorkingPath/"CovidBeaches"
    
# get soft coast position as most recent
MHWSPath = WorkingPath / "MHWS_Lines" / ("mhws_sept19_simple.shp")
    
# Set up the coast
CellCoast = Coast(str(ModernPath))
    
    if not CellCoast.BuiltTransects:
        
        # may need to think carefully about how much to smooth
        CellCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize)
        
        # write smoothed coast/bathy to file
        CellCoast.WriteCoastShp(str(OutputPath / (RowName + "_Smoothed_Coast.shp")))

        CellCoast.GenerateTransects(TransectSpacing=TransectSpacing, CheckTopology=False)
        
        CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects_Raw.shp")))
        
        CellCoast.BuiltTransects = True
        
        # SAVE ENTIRE COAST OBJECT
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    if not CellCoast.GotHistoricShorelines:
        
        if not OldPath.is_file():
            print("No 1890s MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(OldPath))
        
        if not QuiteOldPath.is_file():
            print("No 1970s MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(QuiteOldPath))
        
        if not SoftPath.is_file():
            print("No soft MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(SoftPath))
            
        CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects_Sampled.shp")))
    
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
        CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_ExtendedTransects.shp")))
        CellCoast.FindDEM(str(NationalDEMPath / "OSTerrain5_fullcoastindex.shp"))
        CellCoast.ExtractTransectTopography()
        
        CellCoast.SampledDEMs = True
        
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    if not CellCoast.PredictedFutureShorelines:    
    
        ## predict future shorelines
        #CellCoast.SampleRockHeadPosition(str(WorkingPath / "UPSM" / "upsm_ncca.tif"))
        CellCoast.PredictFutureShorelines()
        
        CellCoast.PredictedFutureShorelines = True
    
        # write future shorelines
        CellCoast.WriteFutureShorelinesShp(str(OutputPath / (RowName + "_Future.shp")),Smooth=True)
        CellCoast.WriteFutureUncertaintyShp(str(OutputPath / (RowName + "_Uncertainty_2100.shp")))
        CellCoast.WriteFutureUncertaintyShp(str(OutputPath / (RowName + "_Uncertainty_2050.shp")),Year=2050)
        CellCoast.WriteErodedAreaShp(str(WorkingPath / "CoastalCells" / (RowName + "_FutureErosion.shp")))
    
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
        
    

    #CellCoast.WriteFutureShorelineSegmentsShp(str(WorkingPath / "CoastalCells" / (RowName + "_FutureSegments.shp")))
    

    

