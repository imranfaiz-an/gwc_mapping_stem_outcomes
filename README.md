# 📊 GW Carver School & Neighborhood Analysis

This project examines the relationship between **school performance** and **neighborhood socioeconomic conditions** in Illinois by integrating state education data with U.S. Census indicators.

---

## 📑 Table of Contents

- [Datasets Used](#-datasets-used)
- [Conceptual Framework](#-conceptual-framework)
- [Variables of Interest](#-variables-of-interest)
- [Final Dataset](#-final-dataset)
- [Future Enhancements](#-future-enhancements)

---

## 📦 Datasets Used

### 1. Illinois State Board of Education (ISBE) School Report Card (2025)
- School-level academic and demographic indicators  
- Includes proficiency metrics for ELA, Math, and Science  

### 2. ISBE School Directory
- School and district identifiers  
- Includes **RCDTS codes** and ZIP codes  

### 3. U.S. Census Bureau — American Community Survey (ACS) 2023 (5-Year Estimates)
- ZIP code–level socioeconomic indicators  
- Includes unemployment and poverty rates  

---

## 🧠 Conceptual Framework

### Objective
Merge school-level academic performance data with neighborhood socioeconomic indicators.

### Key Linkages
- **RCDTS Code** → unique school identifier  
- **ZIP Code** → geographic link to census data  

### Challenges
- ISBE report card dataset contains school names but no ZIP codes.
- Required linking multiple datasets to assign geographic context.

### Approach

1. Use **RCDTS codes** to uniquely identify schools.
2. Merge School Directory with Report Card data to append ZIP codes.
3. Join ZIP codes with Census data for socioeconomic indicators.
4. Integrate spatial shapefiles (GeoPandas) for geographic mapping.

### Dataset Construction Workflow

| Step | Description | Output |
|------|-------------|--------|
| 1 | Merge ISBE Report + Census Data | Dataset 1 |
| 2 | Merge ISBE Report + School Directory | Dataset 2 |
| 3 | Merge Dataset 1 & 2 via ZIP + RCDTS | Final Dataset |

Only ZIP codes within the target area were retained.

---

## 📈 Variables of Interest

### Academic Outcomes

| Variable | Definition |
|----------|-----------|
| **ELA Proficiency** | % meeting or exceeding ELA standards |
| **Math Proficiency** | % meeting or exceeding math standards |
| **Science Proficiency** | % meeting or exceeding science standards |

### Socioeconomic Indicators

| Variable | Formula |
|----------|---------|
| **Unemployment Rate** | `DP03_0005E / DP03_0003E` |
| **Poverty Rate** | `DP03_0119PE` |

### School Resources

| Variable | Definition |
|----------|-----------|
| **Student–Teacher Ratio** | Enrollment ÷ Teacher headcount |

---

## 🗂 Final Dataset

📍 **Location**

```text
gw_carver/data_sources/output/gw_carver_school_data.csv
