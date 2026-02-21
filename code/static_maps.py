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

# 1) Pretty labels (change these to whatever you like)
LABELS = {
    "% ELA Proficiency": "English language proficiency (%)",
    "% Math Proficiency": "Math proficiency (%)",
    "% Science Proficiency": "Science proficiency (%)",
    "unemployment_percentage": "Unemployment rate (%)",
    "percent_below_poverty_level": "Below poverty line (%)",
}

# 2) Optional: tell which variables should be displayed as percents
PCT_VARS = {
    "% ELA Proficiency",
    "% Math Proficiency",
    "% Science Proficiency",
    "unemployment_percentage",
    "percent_below_poverty_level",
}

def make_title(col: str) -> str:
    return f"{LABELS.get(col, col)} by Neighborhood (Chicago)"

def make_tooltip(col: str):
    # Format: show 1 decimal place for percent-like variables, else 2 decimals
    fmt = ".1f" if col in PCT_VARS else ".2f"
    return [
        alt.Tooltip("properties.pri_neigh:N", title="Neighborhood"),
        alt.Tooltip("properties.n_schools:Q", title="Schools"),
        alt.Tooltip(f"properties.{col}:Q", title=LABELS.get(col, col), format=fmt),
    ]


def choropleth_three_layers(gdf_map, value_col, title=None, scheme="viridis"):
    geojson = json.loads(gdf_map.to_json())
    t = title or make_title(value_col)

    base_all = alt.Chart(alt.Data(values=geojson["features"])).mark_geoshape(
        stroke="white", strokeWidth=0.4, fill="#f0f0f0"
    )

    missing = (
        alt.Chart(alt.Data(values=geojson["features"]))
        .transform_filter(f"!isFinite(datum.properties['{value_col}'])")
        .mark_geoshape(stroke="white", strokeWidth=0.4, fill="#bdbdbd")
    )

    data = (
        alt.Chart(alt.Data(values=geojson["features"]))
        .transform_filter(f"isFinite(datum.properties['{value_col}'])")
        .mark_geoshape(stroke="white", strokeWidth=0.4)
        .encode(
            color=alt.Color(f"properties.{value_col}:Q",
                            scale=alt.Scale(scheme=scheme),
                            title=LABELS.get(value_col, value_col)),  # legend title
            tooltip=make_tooltip(value_col),
        )
    )

    return (base_all + missing + data).project(type="mercator").properties(
        width=720, height=720, title=t
    )


    return (base_all + missing + data).project(type="mercator").properties(width=720, height=720, title=t)

# --- output folder ---
out_dir = Path("../outputs/maps")
out_dir.mkdir(parents=True, exist_ok=True)

def slugify(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[^\w\s-]", "", s)      # remove % and punctuation
    s = re.sub(r"[\s_-]+", "_", s)      # spaces -> _
    return s.lower()

charts = {}

for col in vars_to_map:
    if col not in gdf_all.columns:
        print(f"Skipping (not found): {col}")
        continue

    chart = choropleth_three_layers(
        gdf_map=gdf_all,
        value_col=col,
        title=f"{col} by Neighborhood (Chicago)",
        scheme="viridis",
    )

    # store in dict if you want to reuse later
    charts[col] = chart

    # --- save as HTML (recommended) ---
    fname = out_dir / f"choropleth_{slugify(col)}.html"
    chart.save(fname)
    print(f"Saved: {fname}")

# --- optional: save a single "gallery" HTML that embeds all charts ---
gallery = alt.vconcat(*[charts[c] for c in charts.keys()]).resolve_scale(color="independent")
gallery.save(out_dir / "all_choropleths_gallery.html")
print("Saved gallery:", out_dir / "all_choropleths_gallery.html")