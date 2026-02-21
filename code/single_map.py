import pandas as pd
import altair as alt
import geopandas as gpd
import json
from pathlib import Path
import re
import os


# 1) Load data
neighborhoods_geo = gpd.read_file(
    "data/shapefiles_geolocations/Neighborhoods_2012b_20251108/geo_export_d6da9fc2-1417-41bc-96a9-e15b09615172.shp"
)
school_data = pd.read_csv("data/output/clean_data.csv")

# 2) Harmonize names so "East Garfield Park" can match your shapefile
school_data["neighborhood"] = school_data["neighborhood"].replace(
    {"East Garfield Park": "Garfield Park"}
)

# 3) Rename to match shapefile join key
school_data = school_data.rename(columns={"neighborhood": "pri_neigh"})


# 4) Pick variables to map
vars_to_map = [
    "% ELA Proficiency",
    "% Math Proficiency",
    "% Science Proficiency",
    "unemployment_percentage",
    "percent_below_poverty_level",
]

def to_numeric(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
              .str.strip()
              .str.replace("%", "", regex=False)
              .str.replace(",", "", regex=False)
              .replace({"nan": pd.NA, "None": pd.NA, "N/A": pd.NA, "NA": pd.NA, "": pd.NA})
              .pipe(pd.to_numeric, errors="coerce")
    )

for col in vars_to_map:
    if col in school_data.columns:
        school_data[col] = to_numeric(school_data[col])

# 6) Aggregate SCHOOL rows -> ONE row per neighborhood
df_neigh = (
    school_data
    .groupby("pri_neigh", as_index=False)
    .agg(
        n_schools=("RCDTS", "nunique"),
        **{v: (v, "median") for v in vars_to_map}
    )
)

gdf_all = neighborhoods_geo.merge(df_neigh, on="pri_neigh", how="left")


LABELS = {
    "% ELA Proficiency": "ELA proficiency (%)",
    "% Math Proficiency": "Math proficiency (%)",
    "% Science Proficiency": "Science proficiency (%)",
    "unemployment_percentage": "Unemployment rate (%)",
    "percent_below_poverty_level": "Below poverty line (%)",
}

# ---- 1) long data ----
vars_present = [v for v in vars_to_map if v in df_neigh.columns]

df_long = (
    df_neigh
    .melt(
        id_vars=["pri_neigh", "n_schools"],
        value_vars=vars_present,
        var_name="metric",
        value_name="value"
    )
)

# pretty label column for tooltips + dropdown display
df_long["metric_label"] = df_long["metric"].map(LABELS).fillna(df_long["metric"])

# ---- 2) join to geometry ----
gdf_long = neighborhoods_geo.merge(df_long, on="pri_neigh", how="left")
geojson = json.loads(gdf_long.to_json())

# ---- 3) dropdown parameter (use label for readability) ----
metric_labels = sorted(df_long["metric_label"].dropna().unique().tolist())

metric_param = alt.param(
    name="metric_label",
    bind=alt.binding_select(options=metric_labels, name="Metric: "),
    value=metric_labels[0],
)

base = alt.Chart(alt.Data(values=geojson["features"])).mark_geoshape(
    stroke="white", strokeWidth=0.4
).project("mercator").properties(width=720, height=720)

# filter features to the selected metric
selected = f"datum.properties.metric_label == metric_label"

# background (light grey) for all neighborhoods
bg = base.encode(color=alt.value("#f0f0f0"))

# missing layer (darker grey) for selected metric where value is missing
missing = base.transform_filter(selected).transform_filter(
    "!isFinite(datum.properties.value)"
).encode(color=alt.value("#bdbdbd"))

# data layer for selected metric where value exists
data = base.transform_filter(selected).transform_filter(
    "isFinite(datum.properties.value)"
).encode(
    color=alt.Color("properties.value:Q", scale=alt.Scale(scheme="viridis"), title="Value"),
    tooltip=[
        alt.Tooltip("properties.pri_neigh:N", title="Neighborhood"),
        alt.Tooltip("properties.n_schools:Q", title="Schools"),
        alt.Tooltip("properties.metric_label:N", title="Metric"),
        alt.Tooltip("properties.value:Q", title="Value", format=".2f"),
    ],
)

chart = (bg + missing + data).add_params(metric_param).properties(
    title="Chicago neighborhood choropleth (choose metric)"
)

# save
chart.save("../outputs/maps/choropleth_dropdown.html")

