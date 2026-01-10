import pandas as pd
from pathlib import Path

# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

report_card_path = (
    BASE_DIR
    / "data"
    / "raw_data"
    / "2025-Report-Card-Public-Data-Set.xlsx"
)

directory_path = (
    BASE_DIR
    / "data"
    / "raw_data"
    / "dir_ed_entities.xls"
)

# ------------------------------------------------------------------
# Load report card data
# ------------------------------------------------------------------
subset_data = pd.read_excel(report_card_path, sheet_name="General")

filtered_data = subset_data[
    (subset_data["District"] == "Chicago Public Schools District 299")
    & (
        (subset_data["School Type"] == "Elementary School")
        | (subset_data["School Type"] == "Middle/Junior High School")
    )
].copy()

# Clean RCDTS
filtered_data["RCDTS_clean"] = (
    filtered_data["RCDTS"]
    .astype(str)
    .str.replace("-", "", regex=False)
)

# ------------------------------------------------------------------
# Load directory data
# ------------------------------------------------------------------
directory_df = pd.read_excel(directory_path, sheet_name="1 Public Dist & Sch")

vars_to_keep = [
    "CountyName",
    "Region-2\nCounty-3\nDistrict-4",
    "Type",
    "School",
    "FacilityName",
    "City",
    "Zip",
]

subset_dir_df = directory_df[vars_to_keep].copy()

subset_dir_df = subset_dir_df.rename(
    columns={"Region-2\nCounty-3\nDistrict-4": "RCD"}
)

# Ensure string type before concatenation
for col in ["RCD", "Type", "School"]:
    subset_dir_df[col] = subset_dir_df[col].astype(str)

subset_dir_df["RCDTS_clean"] = (
    subset_dir_df["RCD"]
    + subset_dir_df["Type"]
    + subset_dir_df["School"]
)

subset_dir_df["zip_clean"] = (
    subset_dir_df["Zip"]
    .astype(str)
    .str.extract(r"^\s*(\d{5})")
)

# ------------------------------------------------------------------
# Zip filtering
# ------------------------------------------------------------------
relevant_zips = [
    "60621", "60636", "60619", "60620", "60623", "60624", "60647", "60651",
    "60614", "60657", "60626", "60645", "60660", "60640", "60641", "60613",
]

subset_dir_df = subset_dir_df[
    subset_dir_df["zip_clean"].isin(relevant_zips)
][["RCDTS_clean", "zip_clean"]].copy()

# ------------------------------------------------------------------
# Merge
# ------------------------------------------------------------------
merged_df = filtered_data.merge(
    subset_dir_df,
    on="RCDTS_clean",
    how="inner",
)

# ------------------------------------------------------------------
# Save Output
# ------------------------------------------------------------------
output_path = BASE_DIR / "data" / "output" / "20260109" / "merged_output.csv"
merged_df.to_csv(output_path, index=False)