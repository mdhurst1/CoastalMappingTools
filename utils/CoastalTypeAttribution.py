"""
Coastal LiDAR Prioritisation - Coast Type Attribution
-----------------------------------------------------

Assigns attributed MHWS line segments to their nearest coastal cell and then
summarises the amount of Hard, Soft and Artificial coastline associated with
each cell.

The coastal cells were built with MHWS forming their seaward edge, which makes
a normal line/polygon intersection a bit awkward. Rather than fighting that,
this works the other way round: each MHWS line segment is assigned to its
nearest coastal cell and its length is used to describe the coastline in that
cell.

MDH, August 2026
"""

from pathlib import Path
import geopandas as gpd


# -----------------------------------------------------------------------------
# User settings
# -----------------------------------------------------------------------------

DATA_FOLDER = Path(
    r"C:\Users\mh322u\OneDrive - University of Glasgow\_Scotgov_Fellowship\04_Data"
)

MHWS_FILE = (
    DATA_FOLDER
    / "01 MHWS 2024 inc CT"
    / "OS_MHWS_2024_CT_all_Final.shp"
)

COASTAL_CELLS_FILE = (
    DATA_FOLDER
    / "02 CZC LiDAR Index"
    / "SG_LiDAR_Collected.shp"
)

OUTPUT_FILE = (
    DATA_FOLDER
    / "Outputs"
    / "CoastalCells_CoastType.shp"
)

# Attribute names in the source data
SEGMENT_ID_FIELD = "SegmentID"
COAST_TYPE_FIELD = "CT_2024"

# Coast type codes used in the MHWS shapefile
COAST_TYPES = ["H", "S", "A"]

# Anything further away than this is probably not the line we are looking for.
# Most assignments should actually be at, or very close to, zero metres.
MAX_ASSIGNMENT_DISTANCE_M = 500.0


# -----------------------------------------------------------------------------
# Check that the two input datasets contain what we expect
# -----------------------------------------------------------------------------

def check_inputs(cells, mhws):
    """A few quick checks before getting stuck into the spatial work."""

    if SEGMENT_ID_FIELD not in cells.columns:
        raise ValueError(
            f"Coastal cells are missing required field: {SEGMENT_ID_FIELD}"
        )

    if COAST_TYPE_FIELD not in mhws.columns:
        raise ValueError(
            f"MHWS lines are missing required field: {COAST_TYPE_FIELD}"
        )

    if cells.crs is None or mhws.crs is None:
        raise ValueError("Both input shapefiles need a CRS.")

    if not cells.crs.is_projected:
        raise ValueError(
            "Coastal cells need a projected CRS so distances and lengths "
            "are measured in metres."
        )

    if cells[SEGMENT_ID_FIELD].duplicated().any():
        raise ValueError(
            f"{SEGMENT_ID_FIELD} should uniquely identify each coastal cell."
        )


# -----------------------------------------------------------------------------
# Assign each MHWS segment to its nearest coastal cell
# -----------------------------------------------------------------------------

def assign_mhws_to_cells(cells, mhws):
    """Assign every MHWS line segment to its nearest coastal cell."""

    # Put the linework into the same CRS as the coastal cells before doing any
    # measuring. In practice these should probably already match, but no harm
    # in making sure.
    if mhws.crs != cells.crs:
        mhws = mhws.to_crs(cells.crs)

    mhws = mhws.copy()
    mhws["mhws_len"] = mhws.geometry.length

    # Find the nearest polygon for each MHWS line segment. Because the cells
    # were built against MHWS, most distances should be zero or thereabouts.
    joined = gpd.sjoin_nearest(
        mhws,
        cells[[SEGMENT_ID_FIELD, "geometry"]],
        how="left",
        distance_col="cell_dist",
    )

    # Keep a simple QA flag so anything oddly far away is not silently used.
    joined["assign_ok"] = joined["cell_dist"] <= MAX_ASSIGNMENT_DISTANCE_M

    return joined


# -----------------------------------------------------------------------------
# Summarise coast type for each coastal cell
# -----------------------------------------------------------------------------

def summarise_coast_type(cells, joined):
    """Calculate Hard, Soft and Artificial coastline fractions for each cell."""

    valid = joined[
        joined["assign_ok"]
        & joined[SEGMENT_ID_FIELD].notna()
        & joined[COAST_TYPE_FIELD].isin(COAST_TYPES)
    ].copy()

    # Sum MHWS line length by coastal cell and coast type.
    summary = (
        valid.groupby([SEGMENT_ID_FIELD, COAST_TYPE_FIELD])["mhws_len"]
        .sum()
        .unstack(fill_value=0.0)
    )

    # Make sure all three coast types exist as columns even if one is absent
    # from the data altogether.
    for coast_type in COAST_TYPES:
        if coast_type not in summary.columns:
            summary[coast_type] = 0.0

    # Short field names are deliberate here because shapefiles only allow
    # ten-character attribute names.
    summary = summary.rename(
        columns={
            "H": "hard_len",
            "S": "soft_len",
            "A": "art_len",
        }
    )

    length_fields = ["hard_len", "soft_len", "art_len"]
    summary["coast_len"] = summary[length_fields].sum(axis=1)

    # Keep the raw lengths and calculate fractions as well. The fractions are
    # likely to be more useful later when we start building the actual priority
    # score, while coast_len will also come in handy for £/km costing.
    summary["hard_frac"] = summary["hard_len"] / summary["coast_len"]
    summary["soft_frac"] = summary["soft_len"] / summary["coast_len"]
    summary["art_frac"] = summary["art_len"] / summary["coast_len"]

    # Dominant coast type is useful for quick mapping, even though the fractions
    # are the better values to use in the decision model.
    summary["dom_type"] = (
        summary[["hard_frac", "soft_frac", "art_frac"]]
        .idxmax(axis=1)
        .map(
            {
                "hard_frac": "H",
                "soft_frac": "S",
                "art_frac": "A",
            }
        )
    )

    # Join everything back onto the original coastal cells.
    output = cells.merge(
        summary.reset_index(),
        on=SEGMENT_ID_FIELD,
        how="left",
    )

    # Leave unmatched cells as NaN rather than pretending they have zero coast.
    output["ct_match"] = output["coast_len"].notna().astype(int)

    return output


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

def main():
    """Run the coast type attribution."""

    print("Reading coastal cells...")
    cells = gpd.read_file(COASTAL_CELLS_FILE)

    print("Reading attributed MHWS linework...")
    mhws = gpd.read_file(MHWS_FILE)

    check_inputs(cells, mhws)

    print("Assigning MHWS segments to nearest coastal cells...")
    joined = assign_mhws_to_cells(cells, mhws)

    print("Summarising coast type...")
    output = summarise_coast_type(cells, joined)

    # A few useful numbers before writing the result.
    print()
    print(f"Coastal cells:              {len(cells)}")
    print(f"MHWS line assignments:      {len(joined)}")
    print(f"Assignments accepted:       {int(joined['assign_ok'].sum())}")
    print(f"Assignments rejected:       {int((~joined['assign_ok']).sum())}")
    print(f"Cells with coast type:      {int(output['ct_match'].sum())}")
    print(f"Cells without coast type:   {int((output['ct_match'] == 0).sum())}")
    print()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing: {OUTPUT_FILE}")
    output.to_file(OUTPUT_FILE)

    print("Done.")


if __name__ == "__main__":
    main()