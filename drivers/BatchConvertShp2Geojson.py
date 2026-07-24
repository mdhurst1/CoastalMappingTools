"""
File to convert shp file to geojson
"""

# import modules
import geopandas as gpd
from pathlib import Path

def BatchConvertShp2Geojson(InputFolder, OuputFolder):

    # check output folder exists
    OutputFolder.mkdir(parents=True, exist_ok=True)

    # loop through all shp in folder
    for Shapefile in InputFolder.rglob("*.shp"):

        # rename with new extension
        Outputfile = OutputFolder / f"{Shapefile.stem}.geojson"

        # read shapefile to geodataframe
        GDF = gpd.read_file(Shapefile)

        if gdf.crs is None:
            print(f"Skipping {Shapefile.name}: no CRS defined")
            continue

        GDF = GDF.to_crs("EPSG:4326")
        GDF.to_file(OutputFile, driver="GeoJSON")

if __name__ == "__main__"

    # setup folders
    InputFolder = Path(r"C:\Users\mh322u\OneDrive - University of Glasgow\Python\CoastalMappingTools\example_data\Montrose")
    OutputFolder = Path(r"C:\Users\mh322u\OneDrive - University of Glasgow\Code\CoastalMappingViewer\public\data")

    # run
    BatchConvertShp2Geojson(InputFolder, OutputFolder)
