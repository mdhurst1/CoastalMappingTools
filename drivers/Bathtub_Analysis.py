"""
Driver for analysing water levels relative to future sea level and tidal range and storm surge in Scotland
Bathtub approach

Developing the approach here was supported by use of ChatGPT to work out procedure and syntax

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

CRSES Project 2025

"""

# add modules
import os, sys
import pickle, pathlib
import rasterio
from rasterio.merge import merge
from rasterio.warp import reproject, Resampling
from datetime import datetime
import matplotlib.pyplot as plt
#%matplotlib qt5

# add src path to find custom modules
sys.path.append("../src/")

#import custom modules
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/CMT_CRSES")
NationalDEMPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2Final/99_NationalData/OSTerrain5")

# set sea level scenario
# set up scenarios
Scenarios = [8]
Percentiles = [95]

# Decades for writing
Year = 2300

# set up output folders
GeometryPath = WorkingPath/("Geometry")

# Cell list
CellList = ["1a"] # ,"1b","1c","1d","2a"]

print("\nBATHTUB FLOODING ANALYSIS")

# loop through each cell
for CellSub in CellList:
    # print cell to screen
    print("\n\tRUNNING CELL", CellSub)
    RowName = "Cell_"+CellSub
    
    Filename2SaveCoast = GeometryPath / (RowName+"_OpenGeometry.pydata")
    
    for Scenario, Percentile in zip(Scenarios, Percentiles): # main loop starting
        print("\n\t Scenario:",str(Scenario))
        print("\n\t Percentile:",str(Percentile))
        print("\n")
        
        OutputPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_Flooding")
        
        if not OutputPath.exists():
            OutputPath.mkdir(parents=True, exist_ok=True)
            
        """
        PolygonsPath = OutputPath/("Flood_Polygons")
        
        if not PolygonsPath.exists():
            PolygonsPath.mkdir(parents=True, exist_ok=True)
        """

        # # this checks to see whether coast object already exists
        Filename2SaveAll = OutputPath / (RowName+"_OpenChange.pydata")
    
        if Filename2SaveCoast.exists():
            CellCoast = pickle.load(open(Filename2SaveCoast, "rb" ))
            print("Loaded Coast Object ", Filename2SaveCoast)
        else:
            print("No Coastal Object Found, run main CMT analysis first) # if saved geometry not exist")
            sys.exit()
        
        # load Sea level raster
        FutureRSLFile = str(WorkingPath / "Future_RSL" / ("RCP"+str(Scenario)))+ "/RCP" + str(Scenario) + "_" + str(Percentile) + "th_" + str(Year) + "_filled.tif"
        FutureRSLRaster = rasterio.open(FutureRSLFile)
        RSLProfile = FutureRSLRaster.profile

        # load high tide raster
        MHWSFile = str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif")
        MHWSRaster = rasterio.open(MHWSFile)
        MHWSProfile = MHWSRaster.profile           

        # get list of DEMs
        DEMList = CellCoast.UniqueDEMList
        
        FloodList = []
        ExtentList = []
        
        for DEMFile in DEMList:
            
            print(DEMFile)
            Filename = DEMFile.split("/")[-1].rstrip(".tif")
            
            # load DEM
            DEM_Dataset = rasterio.open(DEMFile)
            DEM = DEM_Dataset.read(1, masked=True)
            DEMProfile = DEM_Dataset.profile
            
            # resample RSL and MHWS onto DEM grid
            Resampled_RSL = np.empty((DEM_Dataset.height,DEM_Dataset.width),dtype=FutureRSLRaster.meta["dtype"])
            reproject(source=rasterio.band(FutureRSLRaster,1), destination = Resampled_RSL, 
                      src_transform=FutureRSLRaster.transform, src_crs=FutureRSLRaster.crs, src_nodata=FutureRSLRaster.nodata,
                      dst_transform=DEM_Dataset.transform, dst_crs=DEM_Dataset.crs, dst_nodata=DEM_Dataset.nodata, resampling=Resampling.bilinear)
            
            # Save to new GeoTIFF
            with rasterio.open(str(OutputPath) + "/RSLtest1.tif", "w", **DEMProfile) as dst:
                dst.write(Resampled_RSL, 1)

            Resampled_MHWS = np.empty((DEM_Dataset.height,DEM_Dataset.width),dtype=MHWSRaster.meta["dtype"])
            reproject(source=rasterio.band(MHWSRaster,1), destination = Resampled_MHWS, 
                      src_transform=MHWSRaster.transform, src_crs=MHWSRaster.crs, src_nodata=MHWSRaster.nodata,
                      dst_transform=DEM_Dataset.transform, dst_crs=DEM_Dataset.crs, dst_nodata=DEM_Dataset.nodata, resampling=Resampling.bilinear)

            # Save to new GeoTIFF
            with rasterio.open(str(OutputPath) + "/MHWStest1.tif", "w", **DEMProfile) as dst:
                dst.write(Resampled_MHWS, 1)

            # setup nodata masks
            RSLMask = np.isnan(Resampled_RSL) if np.issubdtype(Resampled_RSL.dtype, np.floating) else (Resampled_RSL == FutureRSLRaster.nodata)
            MHWSMask = np.isnan(Resampled_MHWS) if np.issubdtype(Resampled_MHWS.dtype, np.floating) else (Resampled_MHWS == MHWSRaster.nodata)
            
            # DEM mask minumum value
            DEMMask = np.isclose(DEM, np.nanmin(DEM), atol=1e-6) if np.issubdtype(DEM.dtype, np.floating) else (DEM == np.nanmin(DEM))            

            # calculate extreme waterlevels 
            ExtremeWaterLevels = np.ma.array(Resampled_RSL + Resampled_MHWS, mask = RSLMask | MHWSMask)

            # calculate flood depth
            FloodDepth = np.ma.array(ExtremeWaterLevels - DEM, mask=(ExtremeWaterLevels.mask | DEMMask))
            FloodDepth = np.ma.filled(np.maximum(FloodDepth,0), np.nan)

            # calculate flood extent
            FloodMask = (~np.isnan(FloodDepth)) & (FloodDepth > 0)
            FloodExtent = np.where(FloodDepth > 0, 1, 0).astype(np.uint8)

            # save to new raster
            FloodProfile = DEMProfile.copy()
            FloodProfile.update(dtype = np.float32, nodata = np.nan)
            ExtentProfile = DEMProfile.copy()
            ExtentProfile.update(dtype = np.uint8, nodata = np.nan)

            # Save to new GeoTIFF
            FloodFile = str(OutputPath) + "/" + Filename + "_FloodDepth.tif"
            FloodList.append(FloodFile)
            with rasterio.open(FloodFile, "w", **FloodProfile) as dst:
                dst.write(FloodDepth, 1)
            
            ExtentFile = str(OutputPath) + "/" + Filename + "_FloodExtent.tif"
            ExtentList.append(ExtentFile)
            with rasterio.open(ExtentFile, "w", **FloodProfile) as dst:
                dst.write(FloodExtent, 1)

        # merge files
        srcs = [rasterio.open(fp) for fp in FloodList]
    
        # Build mosaic (returns array shaped (bands, H, W))
        FloodMosaic, out_transform = merge(srcs, method='max', nodata=np.nan, dtype=np.float32, resampling=Resampling.bilinear)

        meta = srcs[0].meta.copy()
        meta.update(
            driver="GTiff",
            height=FloodMosaic.shape[1],
            width=FloodMosaic.shape[2],
            transform=out_transform,
            count=1,
            dtype=np.float32 or meta["dtype"],
            nodata=np.nan,
            compress="deflate",
            predictor=3,
            tiled=True,
            blockxsize=256,
            blockysize=256,
        )
        
        FloodFile = str(OutputPath) + "/" + "FloodDepth_Merged.tif"
        with rasterio.open(FloodFile, "w", **meta) as dst:
            dst.write(FloodMosaic[0], 1)

        for s in srcs:
            s.close()

    