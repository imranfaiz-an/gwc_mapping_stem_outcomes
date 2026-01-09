import pandas
import re
import yaml
import typing
import pathlib

# Load the configuration file
def load_config(config_path: typing.Optional[pathlib.Path] = None) -> typing.Dict:
    """Load the configuration file. Default path is the config.yaml file in the code directory."""
    if config_path is None:
        config_path = pathlib.Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# # === ECONOMIC CHARACTERISTICS DATA ===
# Skip row 1 which contains descriptive labels (Geography, Estimate!!, etc.)
data_econ_source = pandas.read_csv(
    load_config()["paths"]["data_econ_characteristics"], low_memory=False, skiprows=[1]
)

# Zip codes of the neighborhoods we are interested in
ZIP_CODES = [60621, 60636, 60619, 60620, 60623, 60624, 60647, 60651]
ZIP_CODES_ADD = [60614, 60657, 60626, 60645, 60660, 60640, 60641, 60613, 60657]
ALL_ZIP_CODES = ZIP_CODES + ZIP_CODES_ADD

data_econ = (
    # Select the columns we need and rename them
    # GEO_ID: Unique identifier for the geographic area
    # NAME: Name of the geographic area
    # DP03_0005E: Number of unemployed 16 years and older in the civilian workforce
    # DP03_0003E: Population 16 years and older in the civilian workforce
    # DP03_0119PE: Percentage of families below the poverty level
    data_econ_source[['GEO_ID', 'NAME', "DP03_0005E", "DP03_0003E", "DP03_0119PE"]]
    .rename(columns={
        "GEO_ID": "geo_id",
        "NAME": "name",
        "DP03_0005E": "Number of unemployed 16 years and older in the civilian workforce",
        "DP03_0003E": "Population 16 years and older in the civilian workforce",
        "DP03_0119PE": "Percentage of families below the poverty level"
    })
    # Convert the columns to numeric
    .assign(
        num_unemployed_16_civilian_workforce=lambda x: pandas.to_numeric(
            x["Number of unemployed 16 years and older in the civilian workforce"], errors="coerce"
        ),
        population_16_civilian_workforce=lambda x: pandas.to_numeric(
            x["Population 16 years and older in the civilian workforce"], errors="coerce"
        ),
        percent_below_poverty_level=lambda x: pandas.to_numeric(
            x["Percentage of families below the poverty level"], errors="coerce"
        )
    )
    # Calculate unemployment percentage
    .assign(
        unemployment_percentage = lambda x: x["num_unemployed_16_civilian_workforce"] / x["population_16_civilian_workforce"] * 100
    )
    # Get the zip code from the geo_id column
    .assign(
        zip_code=lambda x: pandas.to_numeric(
            x["geo_id"].str.split("US").str[1], errors="coerce"
        ).astype("Int64")
    )
    # Drop the geo_id and name columns
    .drop(columns=["geo_id", "name"])
    # Reorder the columns to put the zip code first
    .pipe(lambda df: df[["zip_code"] + [col for col in df.columns if col != "zip_code"]])
    # Filter to only include the zip codes we need
    .loc[lambda df: df["zip_code"].isin(ALL_ZIP_CODES)]
    .reset_index(drop=True)
)
data_econ.to_csv(load_config()["paths"]["output_directory"] + "economic_characteristics.csv", index=False)



# # === ILLINOIS REPORT CARD DATA ===
# Read ELA and Math proficiency data from sheet "ELAMathScience"
math_prof = pandas.read_excel(
    load_config()["paths"]["data_report_card"],
    sheet_name="ELAMathScience"
)

# Filter for Chicago schools only
math_prof = (
    math_prof[
        (math_prof["City"] == "Chicago") & 
        (math_prof["Level"] == "School")
    ]
    [["RCDTS", "School Name", "City", "% ELA Proficiency", "% Math Proficiency"]]
)

# Read Science proficiency data from sheet "ELAMathScience (2)"
science_prof = pandas.read_excel(
    load_config()["paths"]["data_report_card"],
    sheet_name="ELAMathScience (2)"
)

# Filter for Chicago schools only
science_prof = (
    science_prof[
        (science_prof["City"] == "Chicago") & 
        (science_prof["Level"] == "School")
    ]
    [["RCDTS", "School Name", "City", "% Science Proficiency"]]
)

# Join math_prof and science_prof on RCDTS, School Name, and City
math_and_science_prof = math_prof.merge(
    science_prof,
    on=["RCDTS", "School Name", "City"],
    how="left"
)

math_and_science_prof.to_csv(load_config()["paths"]["output_directory"] + "report_card_proficiency_scores.csv", index=False)