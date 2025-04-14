#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  7 13:28:43 2025

Script to read and interpolate Future Relative Sea-Level Rise (RSLR) rasters
from points provided by MetOffice Climate Data Portal

https://climatedataportal.metoffice.gov.uk/datasets/TheMetOffice::exploratory-extended-time-mean-sea-level-projections-to-2300-cm/about

@author: cmacdonell
"""

import os, sys
import pathlib
import geopandas as gp
import numpy as np
from datetime import datetime
from scipy.spatial import cKDTree
import rasterio
from rasterio.transform import from_origin

### SETUP SCRIPT AND INPUT DATA FILES ###

baseFolder = pathlib.Path("/media/14TB_RAID_Array/User_Homes/Craig_MacDonell/CoastalMappingTools/data")
ptsFolder = pathlib.Path(baseFolder / "Future_RSLR_Pts")
rastFolder = pathlib.Path(baseFolder / "Future_RSLR_Rasters")

rslrPts = gp.read_file(ptsFolder / "UKCP18_Time-mean_Sea_Level_Projections_to_2300(cm).shp")

### INTERPOLATION FUNCTION ###

def idw_interpolation(points_gdf, attribute, grid_x, grid_y, power=2, k=12):
    """
    Performs IDW interpolation for a given attribute.

    Parameters:
    - points_gdf: GeoDataFrame with point geometries.
    - attribute: Column name for the variable to interpolate.
    - grid_x, grid_y: Meshgrid arrays defining the interpolation grid.
    - power: Power parameter for IDW (higher values give more weight to nearby points).
    - k: Number of nearest neighbors to consider.

    Returns:
    - Interpolated values on the defined grid.
    """
    # Extract point coordinates and values
    xy = np.vstack([points_gdf.geometry.x, points_gdf.geometry.y]).T
    values = (points_gdf[attribute].values / 100) # convert from cm to m

    # Build spatial KD-tree
    tree = cKDTree(xy)

    # Query nearest neighbors for grid points
    grid_points = np.vstack([grid_x.ravel(), grid_y.ravel()]).T
    distances, indices = tree.query(grid_points, k=k)  # Nearest k points

    # Compute IDW weights
    weights = 1 / np.power(distances, power, where=distances != 0)
    weights[distances == 0] = 1  # Avoid division by zero

    # Compute interpolated values
    interpolated_values = np.sum(weights * values[indices], axis=1) / np.sum(weights, axis=1)

    return interpolated_values.reshape(grid_x.shape)

### SAVE RASTER FUNCTION ###

def save_as_raster(output_path, interpolated_grid, grid_x, grid_y, cellsize,crs):
    """
    Saves an interpolated grid as a GeoTIFF raster.

    Parameters:
    - output_path: File path for the output .tif file.
    - interpolated_grid: 2D NumPy array with interpolated values.
    - grid_x, grid_y: Meshgrid arrays defining the interpolation grid.
    - crs: Coordinate Reference System (from gdf.crs).
    """

    # Define raster transformation (top-left origin)
    transform = from_origin(grid_x.min(), grid_y.max(), cellsize, cellsize)

    # Save raster using rasterio
    with rasterio.open(
        output_path, 'w', 
        driver='GTiff', 
        height=interpolated_grid.shape[0],
        width=interpolated_grid.shape[1],
        count=1, 
        dtype=interpolated_grid.dtype, 
        crs=crs, 
        transform=transform
    ) as dst:
        dst.write(interpolated_grid, 1)

    #print(f"Raster saved: {output_path}")

### PERFORM INTERPOLATION & RASTER WRITING ###

decades = np.arange(2010, 2300 + 1, 10) # based on attributes
dates = [datetime(decade, 1, 1).strftime("%Y-%m-%d") for decade in decades]

scenarios = rslrPts["RCP_Percen"].unique()
# Attributes to interpolate
fields = rslrPts.columns[3:-2]

# Extract CRS
crs = rslrPts.crs  # Keep the original CRS

# Define grid resolution based on point density or manually set
cell_size = 10000  # Set desired cell size in CRS units (e.g., meters)

# Get extent (bounds) from the points
minx, miny, maxx, maxy = rslrPts.total_bounds

# Define grid using cell size
x_coords = np.arange(minx - cell_size, maxx + cell_size, cell_size)
y_coords = np.arange(miny - cell_size, maxy + cell_size, cell_size)
grid_x, grid_y = np.meshgrid(x_coords, y_coords)

for scenario in scenarios:
    print("Scenario:",scenario)
    subset_pts = rslrPts[rslrPts["RCP_Percen"] == scenario]
    decadeCounter = 0
    
    rcpLabel = scenario.split('_')[0][:-1].upper()
    percLabel = scenario.split('_')[-1] + 'th'
    
    scenarioPath = pathlib.Path(rastFolder / rcpLabel)
    if not os.path.exists(scenarioPath):
        os.makedirs(scenarioPath)
    
    for field in fields:
        decadeYYYY = decades[decadeCounter]
        
        interpolated_grid = idw_interpolation(subset_pts, field, grid_x, grid_y, power=1, k=12)
        
        # Example: Store results or visualize
        #print(f"Scenario {scenario}, Attribute {field} ({decadeYYYY}) - Interpolation Complete")
        
        # Define raster output path
        output_path = pathlib.Path(scenarioPath / f"{rcpLabel}_{percLabel}_{decadeYYYY}_filled.tif")
        decadeCounter += 1

        # Save as GeoTIFF
        #save_as_raster(output_path, interpolated_grid, grid_x, grid_y, cell_size,crs)
        
    #sys.exit('One scenario complete')