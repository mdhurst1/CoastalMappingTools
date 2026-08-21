"""
Coastal LiDAR Prioritisation - First Pass Priority Index
--------------------------------------------------------

Takes the enriched coastal-cell dataset and turns the available evidence into
a simple 0-1 LiDAR acquisition priority score.

For now there are five factors:

    1. Time since LiDAR was last acquired
    2. Coast type
    3. Presence of assets
    4. Low-lying coastal topography
    5. Coastal erosion

Each factor is first converted to its own score between 0 and 1. The factor
scores are then combined using equal weights, so with five factors each one
contributes 20% of the final priority index.

The important thing at this stage is to keep the individual scores in the
output. That way we can see exactly why a cell has received a particular
priority and fiddle with the assumptions later without losing the underlying
evidence.

MDH, August 2026
"""

# impor modules
from pathlib import Path
from datetime import datetime
import geopandas as gpd
import numpy as np


# -----------------------------------------------------------------------------
# User settings
# -----------------------------------------------------------------------------

DATA_FOLDER = Path(r"C:\Users\mh322u\OneDrive - University of Glasgow\_Scotgov_Fellowship\04_Data")
INPUT_FILE = (DATA_FOLDER / "Outputs" / "CoastalCells_CoastType_Terrain_Erosion.shp")
OUTPUT_FILE = (DATA_FOLDER / "Outputs"/ "SG_LiDAR_Priority.shp")


# Current year used to calculate time since the latest LiDAR survey.
CURRENT_YEAR = datetime.now().year

# -------------------------------------------------------------------------
# Source field names
# -------------------------------------------------------------------------
#
# Change the first two if the names in the original coastal-cell shapefile are
# different. The remaining fields are the ones produced by the enrichment
# scripts we have already made.

LIDAR_YEAR_FIELD = "Max_LiD_Yr"
ASSETS_FIELD = "Assets"

SOFT_FRAC_FIELD = "soft_frac"
ART_FRAC_FIELD = "art_frac"

LOW5_FRAC_FIELD = "low5_frac"

EROS_FRAC_FIELD = "eros_frac"
EROS_MED_FIELD = "eros_med"
EROS_P10_FIELD = "eros_p10"
N_TRANS_FIELD = "n_trans"


# -----------------------------------------------------------------------------
# Scoring assumptions
# -----------------------------------------------------------------------------

# LiDAR
#
# Five years without a survey gives the maximum age score. Anything older than
# this remains at 1 rather than allowing the score to wander above our 0-1
# scoring range.
LIDAR_FULL_SCORE_YEARS = 5.0

# Coast type
#
# Soft coast gets the full coast-type score, artificial coast gets half, and
# hard coast contributes nothing. Hard coast therefore drops naturally out of
# the equation:
#
#     S_coast = f_soft + 0.5 f_artificial
#
ARTIFICIAL_COAST_SCORE = 0.5

# Erosion
#
# eros_frac is already on a 0-1 scale. The two rate measures are not, so they
# need a reference rate at which they receive a full score.
#
# These are deliberately obvious first-pass assumptions rather than magic
# numbers buried in the calculation. They can be changed once we have mapped
# the results and seen how the index behaves.
# keep these positive to avoid negative score indexing
MEDIAN_EROSION_FULL_SCORE = 1.0   # m/yr
P10_EROSION_FULL_SCORE = 2.0      # m/yr

# Relative contribution of the three bits of the erosion score.
EROSION_EXTENT_WEIGHT = 0.5
EROSION_MEDIAN_WEIGHT = 0.3
EROSION_P10_WEIGHT = 0.2


# -----------------------------------------------------------------------------
# Basic checks
# -----------------------------------------------------------------------------

def check_fields(cells):
    """Make sure all the bits needed for the first-pass score are present."""

    required_fields = [
        LIDAR_YEAR_FIELD,
        ASSETS_FIELD,
        SOFT_FRAC_FIELD,
        ART_FRAC_FIELD,
        LOW5_FRAC_FIELD,
        EROS_FRAC_FIELD,
        EROS_MED_FIELD,
        EROS_P10_FIELD,
        N_TRANS_FIELD,
    ]

    missing = [field for field in required_fields if field not in cells.columns]

    if missing:
        raise ValueError(
            "The following required fields are missing from the input file: "
            + ", ".join(missing)
        )


# -----------------------------------------------------------------------------
# Individual criterion scores
# -----------------------------------------------------------------------------

def score_lidar_age(cells):
    """
    Score time since the latest LiDAR survey.

    A survey this year scores 0, while a survey five or more years ago scores 1.
    Missing survey years are treated as maximum priority on the assumption that
    they represent cells for which no previous LiDAR survey is known.
    """

    years_since = CURRENT_YEAR - cells[LIDAR_YEAR_FIELD]

    # A future year would otherwise give a negative score, so keep everything
    # within a sensible range.
    years_since = years_since.clip(lower=0)

    cells["lidar_age"] = years_since

    cells["s_lidar"] = (
        years_since / LIDAR_FULL_SCORE_YEARS
    ).clip(lower=0, upper=1)

    # If we genuinely have no record of LiDAR, treat that as fully due.
    cells.loc[cells[LIDAR_YEAR_FIELD].isna(), "s_lidar"] = 1.0

    return cells


def score_assets(cells):
    """
    Score whether assets are present.

    Source field contains Y/N values, which are converted to a binary
    prioritisation score.
    """

    cells["s_assets"] = (
        cells[ASSETS_FIELD]
        .astype(str)
        .str.strip()
        .str.upper()
        .map({
            "Y": 1.0,
            "N": 0.0,
        })
    )

    return cells


def score_coast_type(cells):
    """
    Score coastal character.

    Soft coast gets a score of 1, artificial coast 0.5 and hard coast 0. Hard
    does not need its own term because the coast-type fractions already sum to
    one.
    """

    cells["s_coast"] = (
        cells[SOFT_FRAC_FIELD]
        + ARTIFICIAL_COAST_SCORE * cells[ART_FRAC_FIELD]
    ).clip(lower=0, upper=1)

    return cells


def score_lowlying(cells):
    """
    Score low-lying coastal topography.

    low5_frac is already the fraction of valid Terrain 50 cells below 5 m OD,
    so it arrives conveniently on exactly the 0-1 scale we need.
    """

    cells["s_low"] = cells[LOW5_FRAC_FIELD].clip(lower=0, upper=1)

    return cells


def score_erosion(cells):
    """
    Score coastal erosion using extent, typical rate and a more extreme rate.

    The rate fields retain the original negative erosion convention, so their
    magnitudes are used here when turning them into positive 0-1 priority
    scores.
    """

    # How widespread is erosion?
    extent_score = cells[EROS_FRAC_FIELD].clip(lower=0, upper=1)

    # How quickly is the typical eroding frontage retreating?
    median_score = (
        cells[EROS_MED_FIELD].abs() / MEDIAN_EROSION_FULL_SCORE
    ).clip(lower=0, upper=1)

    # How rapidly are the more strongly eroding transects retreating?
    p10_score = (
        cells[EROS_P10_FIELD].abs() / P10_EROSION_FULL_SCORE
    ).clip(lower=0, upper=1)

    # If transects are present but none are eroding, eros_med and eros_p10 are
    # NaN by design. In that case the erosion score should simply be zero.
    no_erosion = (
        cells[N_TRANS_FIELD].notna()
        & (cells[EROS_FRAC_FIELD] == 0)
    )

    median_score.loc[no_erosion] = 0.0
    p10_score.loc[no_erosion] = 0.0

    cells["s_eros"] = (
        EROSION_EXTENT_WEIGHT * extent_score
        + EROSION_MEDIAN_WEIGHT * median_score
        + EROSION_P10_WEIGHT * p10_score
    )

    return cells


# -----------------------------------------------------------------------------
# Overall priority index
# -----------------------------------------------------------------------------

def calculate_priority(cells):
    """
    Combine the individual criterion scores.

    All factors are equally weighted for the first pass. Using the mean rather
    than hard-coding five lots of 0.2 means another factor can be added later
    without rewriting the equation.

    A final priority is only calculated where all component scores are present.
    Missing data therefore stays visible rather than quietly being treated as
    zero priority.
    """

    score_fields = [
        "s_lidar",
        "s_coast",
        "s_assets",
        "s_low",
        "s_eros",
    ]

    n_factors = len(score_fields)
    weight = 1.0 / n_factors

    print(f"Using {n_factors} equally weighted factors")
    print(f"Weight per factor: {weight:.3f}")

    cells["n_score"] = cells[score_fields].notna().sum(axis=1)

    # skipna=False is intentional. If a factor is missing, the final index is
    # also missing and can be investigated rather than silently ignored.
    cells["priority"] = cells[score_fields].mean(
        axis=1,
        skipna=True,
    )

    cells["score_ok"] = cells["n_score"] == n_factors

    return cells


# -----------------------------------------------------------------------------
# Quick QA
# -----------------------------------------------------------------------------

def print_summary(cells):
    """Print a quick look at how the first-pass index has behaved."""

    valid = cells[cells["score_ok"]]

    print()
    print("Coastal LiDAR Prioritisation: first-pass index")
    print("----------------------------------------------")
    print(f"Coastal cells:              {len(cells)}")
    print(f"Cells with complete score:  {len(valid)}")
    print(f"Cells with missing data:    {len(cells) - len(valid)}")

    if len(valid) > 0:
        print(f"Minimum priority:           {valid['priority'].min():.3f}")
        print(f"Median priority:            {valid['priority'].median():.3f}")
        print(f"Maximum priority:           {valid['priority'].max():.3f}")

    print()


# -----------------------------------------------------------------------------
# Main workflow
# -----------------------------------------------------------------------------

def main():
    """Build the first-pass coastal LiDAR priority index."""

    print("Reading enriched coastal cells...")
    cells = gpd.read_file(INPUT_FILE)

    check_fields(cells)

    print("Scoring LiDAR age...")
    cells = score_lidar_age(cells)

    print("Scoring assets...")
    cells = score_assets(cells)

    print("Scoring coast type...")
    cells = score_coast_type(cells)

    print("Scoring low-lying topography...")
    cells = score_lowlying(cells)

    print("Scoring erosion...")
    cells = score_erosion(cells)

    print("Calculating overall priority...")
    cells = calculate_priority(cells)

    print_summary(cells)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing output to: {OUTPUT_FILE}")
    cells.to_file(OUTPUT_FILE)

    print("Done.")


if __name__ == "__main__":
    main()
