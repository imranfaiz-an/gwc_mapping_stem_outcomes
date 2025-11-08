import pandas
import re
import yaml
import typing
import pathlib

#Load the configuration file
def load_config(config_path: typing.Optional[pathlib.Path] = None) -> typing.Dict:
    """Load the configuration file."""
    if config_path is None:
        config_path = pathlib.Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# Economic characteristics data (unemployment, poverty level) from the census data, 2023
data_econ_source = pandas.read_csv(
    load_config()["paths"]["data_econ_characteristics"], low_memory=False
)

ZIP_CODES = [60621, 60636, 60619, 60620, 60623, 60624, 60647, 60651]

data_econ = (
    data_econ_source[['GEO_ID', 'NAME', "DP03_0005E", "DP03_0003E", "DP03_0119PE"]]
    .rename(columns={
        "GEO_ID": "geo_id",
        "NAME": "name",
        "DP03_0005E": "num_unemployed_16_civilian_workforce",
        "DP03_0003E": "population_16_civilian_workforce",
        "DP03_0119PE": "percent_below_poverty_level"
    })
    .assign(
        num_unemployed_16_civilian_workforce=lambda x: pandas.to_numeric(
            x["num_unemployed_16_civilian_workforce"], errors="coerce"
        ),
        population_16_civilian_workforce=lambda x: pandas.to_numeric(
            x["population_16_civilian_workforce"], errors="coerce"
        ),
        percent_below_poverty_level=lambda x: pandas.to_numeric(
            x["percent_below_poverty_level"], errors="coerce"
        ),
        unemployment_percentage = lambda x: x["num_unemployed_16_civilian_workforce"] / x["population_16_civilian_workforce"] * 100
    )
    .assign(
        zip_code=lambda x: pandas.to_numeric(
            x["geo_id"].str.split("US").str[1], errors="coerce"
        ).astype("Int64")
    )
    .drop(columns=["geo_id", "name"])
    .pipe(lambda df: df[["zip_code"] + [col for col in df.columns if col != "zip_code"]])
    .pipe(lambda df: df.iloc[1:])
    .loc[lambda df: df["zip_code"].isin(ZIP_CODES)]
    .reset_index(drop=True)
)

# Save the cleaned data to a CSV file
output_dir = pathlib.Path(load_config()["paths"]["output_directory"])
output_dir.mkdir(parents=True, exist_ok=True)
data_econ.to_csv(output_dir / "economic_characteristics_clean.csv", index=False)

print(data_econ)
