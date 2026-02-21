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

zip_neighbor_dict = {
    "60621": "Englewood",
    "60636": "Englewood",
    "60619": "Chatham",
    "60620": "Chatham",
    "60623": "North Lawndale",
    "60624": "East Garfield Park",
    "60647": "Humboldt Park",
    "60651": "Humboldt Park", 
    "60614": "Lincoln Park",
    "60657": "Lincoln Park",
    "60626": "Rogers Park",
    "60645": "Rogers Park",
    "60660": "Edgewater",
    "60640": "Edgewater",
    "60641": "Portage Park",
    "60613": "Lake View"
}

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
    # Add neighborhood mapping based on zip code
    .assign(neighborhood = lambda x: x["zip_code"].astype(int).astype(str).map(zip_neighbor_dict).fillna("Unknown"))
    .assign(year_of_economic_data = "2023")
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

math_and_science_prof["RCDTS"] = math_and_science_prof["RCDTS"].astype(str).str.replace("-", "", regex=False).str.replace(r'[a-zA-Z]', "", regex=True)
math_and_science_prof.to_csv(load_config()["paths"]["output_directory"] + "report_card_proficiency_scores.csv", index=False)



# RTDTS TO ZIP CODES 
school_data = pandas.read_excel(
    load_config()["paths"]["schools"],
    sheet_name="1 Public Dist & Sch"
)
school_data = school_data[["CountyName", "Region-2\nCounty-3\nDistrict-4", "Type", "School", "FacilityName", "City", "Zip"]]
school_data = school_data.rename(columns={
    "CountyName": "county",
    "Region-2\nCounty-3\nDistrict-4": "rcd",
    "Type": "type",
    "School": "school",
    "FacilityName": "facility_name",
    "City": "city",
    "Zip": "zip"
})
school_data[["rcd", "type", "school"]] = school_data[["rcd", "type", "school"]].astype(str)
school_data["RCDTS"] = school_data["rcd"] + school_data["type"] + school_data["school"]
school_data["RCDTS"] = school_data["RCDTS"].astype(str).str.replace("-", "", regex=False)
school_data["zip_code"] = school_data["zip"].astype(str).str.extract(r"^\s*(\d{5})").astype(int)
school_data = school_data[["RCDTS", "zip_code", "county"]].drop_duplicates()

school_data.to_csv(load_config()["paths"]["output_directory"] + "school_metadata.csv", index=False)


# Merge all datasets
data_df = math_and_science_prof.merge(school_data, on = "RCDTS", how = "left")
data_df = data_df.merge(data_econ, on = "zip_code", how = "left")
data_df = data_df[data_df["zip_code"].isin(ALL_ZIP_CODES)]
data_df["zip_code"] = data_df["zip_code"].astype(int).astype(str)
data_df.to_csv(load_config()["paths"]["output_directory"] + "merged_data.csv", index = False)


data_df.head()