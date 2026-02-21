# Data Structure and Methodology

## 1. Datasets Used

Our analysis integrates multiple publicly available datasets from state and federal sources to study the relationship between school performance and neighborhood characteristics in Illinois.

### Illinois State Board of Education (ISBE) School Report Card (2025)
Public dataset providing school-level academic and demographic indicators.  
**[Source](https://www.illinoisreportcard.com/)**

### ISBE School Directory
Contains comprehensive identifying information for schools and districts, including RCDTS codes and ZIP codes.  
**[Source](https://www.isbe.net/Pages/Data-Analysis-Directories.aspx)**

### U.S. Census Bureau — American Community Survey (ACS) 2023 (5-Year Estimates)
Provides ZIP code–level socioeconomic indicators, including unemployment and poverty rates.  
**[Source](https://www.census.gov/data.html)**

---

## 2. Conceptual Framework

The central objective was to merge school-level academic performance data with neighborhood socioeconomic indicators. This required linking ISBE schools containing ZIP codes and RCDTS codes to ZIP code–level census data and merging the ISBE School Report Card (2025), which is at the RCDTS level.

### Challenges and Approach

- The ISBE report card dataset includes only school names without ZIP codes, making it difficult to associate schools with geographic areas.  
- To address this:
  - We used the **RCDTS (Region-County-District-Type-School)** code, a unique school identifier, constructed as described in the ISBE Key to the Coding System.
  - We merged the School Directory and Report Card datasets to append ZIP codes to each school record.
  - Using GeoPandas and shapefiles from the City of Chicago Data Portal, we integrated spatial polygon data corresponding to ZIP code boundaries, enabling geographic mapping and visualization.

### Final Dataset Construction

- **ISBE Report:** Contained RCDTS codes and school-level performance indicators.  
- **Census Data:** Contained ZIP code–level socioeconomic indicators (e.g., unemployment, poverty).  
- **ISBE School Directory Data:** Contained RCDTS codes and school-level performance indicators.  

**Merging Steps**

1. **First Merge:** Combined the ISBE Report dataset with the Census dataset. *(Dataset 1)*  
2. **Second Merge:** Combined the ISBE Report dataset with the ISBE School Directory dataset. *(Dataset 2)*  
3. **Final Merge:** Combined Dataset 1 and Dataset 2 using ZIP code and RCDTS code matching.

Only ZIP codes relevant to the target area were retained.

The final dataset represents all schools within the selected ZIP codes, along with variables of interest.

---

## 3. Variables of Interest

### Academic Outcomes

| Source | Variable | Definition / Formula |
|--------|----------|----------------------|
| ISBE Report Card - ELA Math Science (sheet) | **Math Proficiency** | % of students meeting or exceeding math standards |
| ISBE Report Card - ELA Math Science2 (sheet) | **Science Proficiency** | % of students meeting or exceeding science standards |
| ISBE Report Card - ELA Math Science (sheet) | **ELA Proficiency** | % of students meeting or exceeding English Language Arts standards |

### Socioeconomic Indicators

| Source | Variable | Definition / Formula |
|--------|----------|----------------------|
| U.S. Census (ACS) - Selected Economic Characteristics, 2023–5 years | **Unemployment Rate** | `DP03_0005E / DP03_0003E` |
| U.S. Census (ACS) - Selected Economic Characteristics, 2023–5 years | **Poverty Rate** | `% of families below poverty line = DP03_0119PE` |

### School Resources

| Source | Variable | Definition / Formula |
|--------|----------|----------------------|
| ISBE Report Card - General (sheet) | **Student–Teacher Ratio** | Total student enrollment / total teacher headcount |

---

## 4. Final Dataset

The final dataset can be found in the GitHub repository:  
`gw_carver/data/output/20260109/merged_data.csv`

### Variables and Descriptions

| Variable Name | Description |
|--------------|-------------|
| `zip_code` | Relevant ZIP code for each neighborhood |
| `shape_area` | Area of the polygon object |
| `shape_len` | Length of the polygon boundary |
| `geometry` | Polygon objects for the ZIP code |
| `RCDTS_clean` | Unique ID for each school |
| `neighborhood` | Neighborhood name |
| `school_name` | School name |
| `city` | City |
| `pct_eng_prof` | % of students meeting or exceeding ELA standards |
| `pct_math_prof` | % of students meeting or exceeding math standards |
| `pct_science_prof` | % of students meeting or exceeding science standards |
| `num_enemployed_16_civilian_workforce` | Number of unemployed individuals 16+ in civilian workforce |
| `population_16_civilian_workforce` | Population 16+ in civilian workforce |
| `percent_below_poverty_level` | Percentage of families below the poverty level |
| `unemployed_percentage` | Percentage of unemployed individuals 16+ in civilian workforce |

---

## 5. Additional Variables for Future Inclusion

Future versions of the dataset can include a broader range of educational and demographic indicators from the ISBE report card, such as:

- Adjusted cohort graduation rate  
- Average class size  
- Average teacher salary  
- Dropout rate  
- High-poverty school designation  
- Homeless student counts  
- Migrant student counts  

### Potential Disaggregations

All variables can be disaggregated by:

- Gender  
- Race/ethnicity  
- Income group  
- Homelessness status  
- Migrant status  
- Grade level  

This granularity would enable deeper insights into equity and access across student populations and neighborhoods.

