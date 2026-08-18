from pathlib import Path

from cogeo_mosaic.mosaic import MosaicJSON

# path to the folder containing the COGs
COG_DIR = Path(r"C:\Users\mh322u\OneDrive - University of Glasgow\_Scotgov_Fellowship\04_Data\LiDAR\NO\DTM\COG")
OUTPUT_FILE = COG_DIR / "Montrose_DEM_Mosaic.json"

# get a list of files
cog_files = sorted(list(COG_DIR.glob("*.tif")) + list(COG_DIR.glob("*.tiff")))

# check there are files
if not cog_files:
    raise FileNotFoundError(f"No COGs found in {COG_DIR}")

#print to screen how many files were found
print(f"Found {len(cog_files)} COGs")

# Convert local Windows paths to file:// URLs
# URLs exposed by RangeHTTPServer
cog_urls = [f"http://127.0.0.1:9000/{cog.name}" for cog in cog_files]
print("Building MosaicJSON...")

# perform the mosaic creation
mosaic = MosaicJSON.from_urls(cog_urls)

# setup the output file
OUTPUT_FILE.write_text(mosaic.model_dump_json(indent=2), encoding="utf-8",)

print(f"\nWritten:")
print(OUTPUT_FILE)