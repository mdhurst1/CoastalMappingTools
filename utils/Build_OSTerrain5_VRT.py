# --------------------------------------------------------------------------
# Build OS Terrain VRT
#
# Finds all ASC tiles beneath the Terrain folder and builds a virtual mosaic.
# Using an input file list avoids Windows getting upset when several thousand
# filenames are passed to gdalbuildvrt in one enormous command.
#
# MDH, August 2026
# --------------------------------------------------------------------------

# import modules
from pathlib import Path
import subprocess

# setup path
TERRAIN_PATH = Path(r"C:\Users\mh322u\OneDrive - University of Glasgow\_Scotgov_Fellowship\04_Data\99_National_Data\OS_Terrain_50")

# setup files
output_vrt = TERRAIN_PATH / "OS_Terrain50.vrt"
file_list = TERRAIN_PATH / "OS_Terrain50_files.txt"

# get all asc files and write to file list
asc_files = list(TERRAIN_PATH.rglob("*.asc"))
# write one raster filename per line
with open(file_list, "w", encoding="utf-8") as f:
    for filename in asc_files:
        f.write(str(filename) + "\n")

# setup the command string
command = ["gdalbuildvrt", "-input_file_list", str(file_list), str(output_vrt)]
subprocess.run(command, check=True)

print(f"Created VRT: {output_vrt}")