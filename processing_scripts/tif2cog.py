# import modules
from pathlib import Path
import subprocess

# --------------------------------------------------------------------------
# Convert GeoTIFFs to Cloud Optimized GeoTIFFs
# --------------------------------------------------------------------------

def convert_to_cog(input_file, output_file):
    """Convert a GeoTIFF to a Cloud Optimized GeoTIFF."""

    command = [
        "gdal_translate",
        str(input_file),
        str(output_file),

        "-of", "COG",
        "-co", "COMPRESS=DEFLATE",
        "-co", "PREDICTOR=YES",
        "-co", "BIGTIFF=IF_SAFER",
    ]

    print(f"Converting: {input_file.name}")

    subprocess.run(command, check=True)

def main():

    # define folders
    INPUT_DIR = Path(r"C:\Users\mh322u\OneDrive - University of Glasgow\_Scotgov_Fellowship\04_Data\LiDAR\NO\DTM")
    OUTPUT_DIR = INPUT_DIR / "COG"
    OVERWRITE = False

    # chedck folder exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # create list of input files from folder
    input_files = sorted(list(INPUT_DIR.glob("*.tif")) + list(INPUT_DIR.glob("*.tiff")))

    # checkl there are files
    if not input_files:
        raise FileNotFoundError(f"No TIFF files found in {INPUT_DIR}")

    # print how many files ot work on
    print(f"Found {len(input_files)} TIFF files.")

    # loop through files to convert
    for i, input_file in enumerate(input_files,start=1):

        # name the output file
        output_file = (OUTPUT_DIR / input_file.name)

        print(f"[{i}/{len(input_files)}] {input_file.name}")

        if (output_file.exists() and not OVERWRITE):
            print("  Skipping: COG already exists.")
            continue

        # launch the conversion
        convert_to_cog(input_file, output_file)

    print("\nFinished.")

if __name__ == "__main__":
    main()