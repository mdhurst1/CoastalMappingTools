"""
Coastal LiDAR Prioritisation - Erosion Metrics
----------------------------------------------

Adds a simple summary of historical shoreline change to each coastal cell
using the Dynamic Coast transect dataset.

For each coastal cell we calculate:

    n_trans    total number of transects assigned to the cell
    n_eros     number of transects with a negative historical rate
    eros_frac  proportion of transects that are eroding
    eros_med   median rate of the eroding transects only
    eros_p10   10th percentile rate of the eroding transects only

The negative sign on erosion rates is deliberately retained. This keeps the
derived fields faithful to the original shoreline-change data and avoids
mixing raw observations with the eventual prioritisation score.

Cells with transects but no eroding transects are given eros_frac = 0, while
eros_med and eros_p10 remain NaN because there is no eroding population from
which to calculate those statistics.

MDH, August 2026
"""

# import modlues
from pathlib import Path
import geopandas as gpd
import numpy as np


# -----------------------------------------------------------------------------
# User settings
# -----------------------------------------------------------------------------

DATA_FOLDER = Path(r"C:\Users\mh322u\OneDrive - University of Glasgow\_Scotgov_Fellowship\04_Data")

# Coastal cells - use the latest enriched version so we keep building up the
# decision-support dataset as we go.
COASTAL_CELLS_FILE = (DATA_FOLDER / "Outputs" / "CoastalCells_CoastType_Terrain.shp")

# Dynamic Coast transects
TRANSECTS_FILE = (DATA_FOLDER / "DC2" / "DC2_RCP8_Transects.shp")

# Output
OUTPUT_FILE = (DATA_FOLDER / "Outputs" / "CoastalCells_CoastType_Terrain_Erosion.shp")

# Field names
SEGMENT_ID_FIELD = "SegmentID"
RATE_FIELD = "Hist_Rate"

# Maximum distance used when assigning transects to coastal cells.
#
# Most transects should intersect or lie very close to a coastal cell. This
# tolerance is mainly a QA safeguard to stop a stray transect being assigned
# somewhere silly.
MAX_ASSIGNMENT_DISTANCE_M = 0


# -----------------------------------------------------------------------------
# Basic checks
# -----------------------------------------------------------------------------

def check_inputs(cells, transects):
    """Make sure the expected fields and coordinate systems are present."""

    if SEGMENT_ID_FIELD not in cells.columns:
        raise ValueError(
            f"Coastal cells are missing required field: {SEGMENT_ID_FIELD}"
        )

    if RATE_FIELD not in transects.columns:
        raise ValueError(
            f"Transects are missing required field: {RATE_FIELD}"
        )

    if cells.crs is None:
        raise ValueError("Coastal cells do not have a CRS.")

    if transects.crs is None:
        raise ValueError("Transects do not have a CRS.")

    if not cells.crs.is_projected:
        raise ValueError(
            "Coastal cells should use a projected CRS so nearest distances "
            "are measured in sensible units."
        )

    if cells[SEGMENT_ID_FIELD].duplicated().any():
        raise ValueError(
            f"{SEGMENT_ID_FIELD} should uniquely identify each coastal cell."
        )


# -----------------------------------------------------------------------------
# Transect assignment
# -----------------------------------------------------------------------------

def assign_transects_to_cells(cells, transects):
    """
    Assign each transect to its nearest coastal cell.

    In many cases the transect will physically intersect the coastal cell and
    the distance will therefore be zero. Using nearest assignment keeps the
    workflow robust where the geometry is a little untidy around cell edges.
    """

    if transects.crs != cells.crs:
        transects = transects.to_crs(cells.crs)

    joined = gpd.sjoin_nearest(
        transects,
        cells[[SEGMENT_ID_FIELD, "geometry"]],
        how="left",
        distance_col="cell_dist",
    )

    # Keep a simple QA flag rather than silently accepting everything.
    joined["assign_ok"] = (
        joined["cell_dist"] <= MAX_ASSIGNMENT_DISTANCE_M
    )

    return joined


# -----------------------------------------------------------------------------
# Erosion summary
# -----------------------------------------------------------------------------

def summarise_erosion(cells, joined):
    """
    Calculate erosion metrics for each coastal cell.

    Only transects with a valid historical rate and an accepted spatial
    assignment are used.
    """

    valid = joined[
        joined["assign_ok"]
        & joined[SEGMENT_ID_FIELD].notna()
        & joined[RATE_FIELD].notna()
    ].copy()

    # Total transect count per cell
    n_trans = (
        valid.groupby(SEGMENT_ID_FIELD)
        .size()
        .rename("n_trans")
    )

    # Pull out just the eroding transects.
    #
    # Historical rates are signed, so negative values indicate erosion.
    eroding = valid[valid[RATE_FIELD] < 0].copy()

    n_eros = (
        eroding.groupby(SEGMENT_ID_FIELD)
        .size()
        .rename("n_eros")
    )

    eros_med = (
        eroding.groupby(SEGMENT_ID_FIELD)[RATE_FIELD]
        .median()
        .rename("eros_med")
    )

    eros_p10 = (
        eroding.groupby(SEGMENT_ID_FIELD)[RATE_FIELD]
        .quantile(0.10)
        .rename("eros_p10")
    )

    # Build one summary table.
    summary = n_trans.to_frame()

    summary = summary.join(n_eros, how="left")
    summary = summary.join(eros_med, how="left")
    summary = summary.join(eros_p10, how="left")

    # Cells with transects but no eroding transects should have zero eroding
    # transects and therefore an erosion fraction of zero.
    summary["n_eros"] = summary["n_eros"].fillna(0).astype(int)

    summary["eros_frac"] = (
        summary["n_eros"] / summary["n_trans"]
    )

    # Join erosion information back onto the coastal cells.
    output = cells.merge(
        summary.reset_index(),
        on=SEGMENT_ID_FIELD,
        how="left",
    )

    # Cells with no assigned transects are left as NaN for the erosion metrics,
    # but a QA flag makes them easy to spot.
    output["eros_match"] = output["n_trans"].notna()

    return output


# -----------------------------------------------------------------------------
# QA summary
# -----------------------------------------------------------------------------

def print_qa_summary(cells, joined, output):
    """Print a few useful checks before writing the result."""

    n_joined = len(joined)
    n_good = int(joined["assign_ok"].sum())
    n_bad = int((~joined["assign_ok"]).sum())

    matched = int(output["eros_match"].sum())
    unmatched = len(cells) - matched

    print()
    print("Coastal LiDAR Prioritisation: erosion metrics")
    print("--------------------------------------------")
    print(f"Coastal cells:                  {len(cells)}")
    print(f"Transect assignments:           {n_joined}")
    print(f"Assignments accepted:           {n_good}")
    print(f"Assignments rejected:           {n_bad}")
    print(f"Cells with transect data:       {matched}")
    print(f"Cells without transect data:    {unmatched}")

    if n_good > 0:
        good_distances = joined.loc[
            joined["assign_ok"],
            "cell_dist",
        ]

        print(
            f"Median assignment distance:     "
            f"{good_distances.median():.3f} m"
        )

        print(
            f"Maximum accepted distance:      "
            f"{good_distances.max():.3f} m"
        )

    if matched > 0:
        matched_cells = output[output["eros_match"]]

        print(
            f"Median eroding fraction:        "
            f"{matched_cells['eros_frac'].median():.3f}"
        )

        eroding_cells = matched_cells[
            matched_cells["n_eros"] > 0
        ]

        if len(eroding_cells) > 0:
            print(
                f"Median erosion rate:            "
                f"{eroding_cells['eros_med'].median():.3f} m/yr"
            )

    print()


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

def main():
    """Calculate erosion metrics for each coastal cell."""

    print("Reading coastal cells...")
    cells = gpd.read_file(COASTAL_CELLS_FILE)

    print("Reading Dynamic Coast transects...")
    transects = gpd.read_file(TRANSECTS_FILE)

    check_inputs(cells, transects)

    print("Assigning transects to coastal cells...")
    joined = assign_transects_to_cells(cells, transects)

    print("Calculating erosion metrics...")
    output = summarise_erosion(cells, joined)

    print_qa_summary(cells, joined, output)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing output to: {OUTPUT_FILE}")
    output.to_file(OUTPUT_FILE)

    print("Done.")


if __name__ == "__main__":
    main()
