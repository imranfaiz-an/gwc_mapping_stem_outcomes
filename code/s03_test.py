import pathlib
import typing

import pandas as pd
import yaml


def load_config(config_path: typing.Optional[pathlib.Path] = None) -> typing.Dict:
    """
    Load the shared YAML configuration file.

    We reuse the same config pattern as in `s01_gen_econ_performance.py` so that the
    path to `data_econ_characteristics.csv` stays in one central place.
    """
    if config_path is None:
        config_path = pathlib.Path(__file__).parent / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main() -> None:
    """
    Compute unemployment and poverty rates for:
    1. All of Chicago (ZIP codes 60601–60661 plus 60664, 60666, 60680, 60681,
       60690, 60691, 60701, 60706, 60707, 60803, 60804, 60805, 60827)
    2. The U.S. overall (aggregated across all ZCTAs in the ACS DP03 file)

    Logic is inspired by `s01_gen_econ_performance.py`:
    - Load the raw ACS DP03 file (`data_econ_characteristics.csv`).
    - Use the same three variables as in lines 53–59 of that script:
        * `DP03_0005E`: number of unemployed 16+ in the civilian workforce
        * `DP03_0003E`: population 16+ in the civilian workforce
        * `DP03_0119PE`: % of families below poverty level
    - For unemployment: Convert estimates to numeric and compute:
        unemployment_rate = (sum unemployed) / (sum civilian workforce) * 100.
    - For poverty: `DP03_0119PE` is already a percentage per ZCTA. We calculate
      a weighted average, weighted by total population 16+ (`DP03_0001E`) to get
      an overall poverty rate that accounts for ZCTA population sizes.
    - For Chicago, filter ACS ZCTAs to the explicit Chicago ZIP code set above
      and aggregate the same way.
    """

    config = load_config()

    # Absolute path so the script is robust to where it is executed from.
    project_root = pathlib.Path(__file__).resolve().parent.parent
    econ_path = project_root / config["paths"]["data_econ_characteristics"]

    # Load ACS DP03 data (skip descriptive label row, keep DP03_* codes).
    econ_raw = pd.read_csv(econ_path, low_memory=False, skiprows=[1])

    # Keep only the needed columns and rename them, mirroring s01.
    # Also include DP03_0001E (total population 16+) for weighting poverty rates.
    econ_small = (
        econ_raw[["GEO_ID", "NAME", "DP03_0001E", "DP03_0005E", "DP03_0003E", "DP03_0119PE"]]
        .rename(
            columns={
                "GEO_ID": "geo_id",
                "NAME": "name",
                "DP03_0001E": "Population 16 years and over",
                "DP03_0005E": "Number of unemployed 16 years and older in the civilian workforce",
                "DP03_0003E": "Population 16 years and older in the civilian workforce",
                "DP03_0119PE": "Percentage of families below the poverty level",
            }
        )
    )

    # Convert ACS estimates to numeric; '(X)' and similar become NaN.
    econ_small["population_16_plus"] = pd.to_numeric(
        econ_small["Population 16 years and over"],
        errors="coerce",
    )
    econ_small["num_unemployed_16_civilian_workforce"] = pd.to_numeric(
        econ_small["Number of unemployed 16 years and older in the civilian workforce"],
        errors="coerce",
    )
    econ_small["population_16_civilian_workforce"] = pd.to_numeric(
        econ_small["Population 16 years and older in the civilian workforce"],
        errors="coerce",
    )
    econ_small["pct_families_below_poverty"] = pd.to_numeric(
        econ_small["Percentage of families below the poverty level"],
        errors="coerce",
    )

    # Derive 5‑digit ZIP (ZCTA) from `geo_id`, same pattern as in s01.
    econ_small["zip_code"] = pd.to_numeric(
        econ_small["geo_id"].str.split("US").str[1],
        errors="coerce",
    ).astype("Int64")

    # Drop rows where we cannot compute an unemployment rate.
    valid_mask = (
        econ_small["num_unemployed_16_civilian_workforce"].notna()
        & econ_small["population_16_civilian_workforce"].notna()
        & (econ_small["population_16_civilian_workforce"] > 0)
    )
    econ_valid = econ_small.loc[valid_mask].copy()

    # For poverty calculations, we need valid poverty percentages and population weights.
    # Filter to rows with valid poverty data and positive population.
    poverty_valid_mask = (
        econ_valid["pct_families_below_poverty"].notna()
        & econ_valid["population_16_plus"].notna()
        & (econ_valid["population_16_plus"] > 0)
    )
    econ_poverty_valid = econ_valid.loc[poverty_valid_mask].copy()

    # U.S. unemployment rate: aggregate over all valid ZCTAs.
    us_unemployed = econ_valid["num_unemployed_16_civilian_workforce"].sum()
    us_workforce = econ_valid["population_16_civilian_workforce"].sum()
    us_unemployment_rate = us_unemployed / us_workforce * 100

    # U.S. poverty rate: weighted average of ZCTA poverty percentages,
    # weighted by population 16+ to account for ZCTA size differences.
    us_poverty_rate = (
        (econ_poverty_valid["pct_families_below_poverty"] * econ_poverty_valid["population_16_plus"]).sum()
        / econ_poverty_valid["population_16_plus"].sum()
    )

    # Chicago ZIP codes: 60601–60661 plus specified extras.
    chicago_zip_codes = list(range(60601, 60662)) + [
        60664,
        60666,
        60680,
        60681,
        60690,
        60691,
        60701,
        60706,
        60707,
        60803,
        60804,
        60805,
        60827,
    ]

    # Chicago unemployment rate: aggregate over those ZIPs.
    chicago_mask = econ_valid["zip_code"].isin(chicago_zip_codes)
    chicago_df = econ_valid.loc[chicago_mask].copy()

    chicago_unemployed = chicago_df["num_unemployed_16_civilian_workforce"].sum()
    chicago_workforce = chicago_df["population_16_civilian_workforce"].sum()
    chicago_unemployment_rate = chicago_unemployed / chicago_workforce * 100

    # Chicago poverty rate: weighted average of ZCTA poverty percentages,
    # weighted by population 16+ to account for ZCTA size differences.
    chicago_poverty_mask = econ_poverty_valid["zip_code"].isin(chicago_zip_codes)
    chicago_poverty_df = econ_poverty_valid.loc[chicago_poverty_mask].copy()

    chicago_poverty_rate = (
        (chicago_poverty_df["pct_families_below_poverty"] * chicago_poverty_df["population_16_plus"]).sum()
        / chicago_poverty_df["population_16_plus"].sum()
    )

    # Print the summary statistics.
    print(
        "Unemployment rate (U.S. overall, ZCTA‑weighted): "
        f"{us_unemployment_rate:.2f}%"
    )
    print(
        "Unemployment rate (Chicago, ZIPs 60601–60661 plus extras): "
        f"{chicago_unemployment_rate:.2f}%"
    )
    print(
        "Poverty rate (U.S. overall, ZCTA‑weighted): "
        f"{us_poverty_rate:.2f}%"
    )
    print(
        "Poverty rate (Chicago, ZIPs 60601–60661 plus extras): "
        f"{chicago_poverty_rate:.2f}%"
    )


if __name__ == "__main__":
    main()

