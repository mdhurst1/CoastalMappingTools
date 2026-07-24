
#import modules
import geopandas as gpd
from pathlib import Path

InputFile = r"C:\Users\mh322u\OneDrive - University of Glasgow\Python\CoastalMappingTools\example_data\Montrose\VEdge_Lines\Montrose_VEdge_combined.shp"
gdf = gpd.read_file(InputFile)

if gdf.crs is None:
    gdf = gdf.set_crs("EPSG:27700")

gdf.to_file(InputFile)