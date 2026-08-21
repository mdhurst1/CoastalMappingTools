"""
Coastal LiDAR Prioritisation - Low-Lying Coast
----------------------------------------------

Uses the OS Terrain 50 VRT to describe how low-lying each coastal cell is.

For every coastal cell we sample the valid Terrain 50 pixels falling within
the polygon and calculate the proportion below 5 m and 10 m OD. A few basic
elevation statistics are also retained because they are useful for checking
the results and may come in handy later.

Importantly, the fractions are based only on valid Terrain 50 cells. NoData
pixels are ignored rather than being treated as zero elevation.

MDH, August 2026
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask


# -----------------------------------------------------------------------------
# User settings
# -----------------------------------------------------------------------------

DATA_FOLDER = Path(r"C:\Users\mh322u\OneDrive - University of Glasgow\_Scotgov_Fellowship\04_Data")

# Coastal cells - use the coast-type enriched version produced in the
# previous step so that we keep building up one decision-support dataset.
COASTAL_CELLS_FILE = (DATA_FOLDER / "Outputs" / "CoastalCells_CoastType.shp")

# Virtual mosaic of OS Terrain 50 ASC tiles
TERRAIN_VRT = (DATA_FOLDER / "99_National_Data" / "OS_Terrain50" / "OS_Terrain50.vrt")

# Output shapefile
OUTPUT_FILE = (DATA_FOLDER / "Outputs" / "CoastalCells_CoastType_Terrain.shp")

# Elevation thresholds used to describe low-lying coast.
LOW_THRESHOLD_M = 5.0
SECOND_THRESHOLD_M = 10.0


# -----------------------------------------------------------------------------
# Calculate terrain statistics
# -----------------------------------------------------------------------------

def get_terrain_stats(geometry, src):
    """
    Calculate Terrain 50 statistics within one coastal cell.

    Only valid raster cells are used. If a coastal cell contains no valid
    Terrain 50 data, NaN values are returned so that the missing data remains
    obvious in the output.
    """

    try:
        terrain, _ = mask(
            src,
            [geometry],
            crop=True,
            filled=False,
            all_touched=False,
        )

    except ValueError:
        return {
            "n_pix": 0,
            "elev_min": np.nan,
            "elev_mean": np.nan,
            "elev_med": np.nan,
            "low5_frac": np.nan,
            "low10_frac": np.nan,
        }

    values = terrain[0].compressed()

    if values.size == 0:
        return {
            "n_pix": 0,
            "elev_min": np.nan,
            "elev_mean": np.nan,
            "elev_med": np.nan,
            "low5_frac": np.nan,
            "low10_frac": np.nan,
        }

    return {
        "n_pix": int(values.size),
        "elev_min": float(np.min(values)),
        "elev_mean": float(np.mean(values)),
        "elev_med": float(np.median(values)),
        "low5_frac": float(np.mean(values < LOW_THRESHOLD_M)),
        "low10_frac": float(np.mean(values < SECOND_THRESHOLD_M)),
    }


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

def main():
    """Calculate low-lying terrain metrics for each coastal cell."""

    print("Reading coastal cells...")
    cells = gpd.read_file(COASTAL_CELLS_FILE)

    print("Opening OS Terrain 50 VRT...")

    with rasterio.open(TERRAIN_VRT) as terrain:

        if terrain.crs is None:
            raise ValueError("Terrain VRT does not have a CRS.")

        print(f"Terrain CRS:        {terrain.crs}")
        print(f"Terrain resolution: {terrain.res}")

        original_crs = cells.crs

        if original_crs is None:
            raise ValueError("Coastal cells do not have a CRS.")

        if cells.crs != terrain.crs:
            print("Reprojecting coastal cells to match Terrain 50...")
            working_cells = cells.to_crs(terrain.crs)
        else:
            working_cells = cells.copy()

        results = []

        print(f"Processing {len(working_cells)} coastal cells...")

        for i, geometry in enumerate(working_cells.geometry, start=1):

            stats = get_terrain_stats(geometry, terrain)
            results.append(stats)

            if i % 100 == 0 or i == len(working_cells):
                print(f"  {i} / {len(working_cells)}")

    cells["n_pix"] = [r["n_pix"] for r in results]
    cells["elev_min"] = [r["elev_min"] for r in results]
    cells["elev_mean"] = [r["elev_mean"] for r in results]
    cells["elev_med"] = [r["elev_med"] for r in results]
    cells["low5_frac"] = [r["low5_frac"] for r in results]
    cells["low10_frac"] = [r["low10_frac"] for r in results]

    cells["dem_match"] = cells["n_pix"] > 0

    matched = int(cells["dem_match"].sum())
    unmatched = len(cells) - matched

    print()
    print("Coastal LiDAR Prioritisation: low-lying coast")
    print("---------------------------------------------")
    print(f"Coastal cells:             {len(cells)}")
    print(f"Cells with terrain data:   {matched}")
    print(f"Cells without terrain:     {unmatched}")

    if matched > 0:
        print(
            f"Median fraction below 5 m: "
            f"{cells.loc[cells['dem_match'], 'low5_frac'].median():.3f}"
        )
        print(
            f"Median fraction below 10 m: "
            f"{cells.loc[cells['dem_match'], 'low10_frac'].median():.3f}"
        )

    print()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing output to: {OUTPUT_FILE}")
    cells.to_file(OUTPUT_FILE)

    print("Done.")


if __name__ == "__main__":
    main()
