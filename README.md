# UCO Herbarium ETL Pipeline

**Created by:** Marc Wright  
**Created on:** 06.01.2026  
**Client:** Dr. Messick, University of Central Oklahoma Herbarium


> ####################################################################################
> ####################################################################################
>
> NOTE:
> 
> The UCO herbarium specimen occurrence data (`CSUoccurrences.csv`) 
> is not included in this repository. This dataset is the property of the University 
> of Central Oklahoma Herbarium and must be obtained directly from the 
> [TORCH Portal](https://portal.torcherbaria.org/) or by contacting Dr. Messick 
> at the UCO Department of Biology. All other reference data files required to run 
> the pipeline are included in the `data/` folder.
>
> ####################################################################################
> ####################################################################################

---

## Overview

This pipeline processes herbarium specimen occurrence data downloaded from the [TORCH Portal](https://portal.torcherbaria.org/) in Darwin Core CSV format. It performs coordinate validation, county-level geographic accuracy checks, taxonomic enrichment against the Oklahoma State Tracking List, redaction of sensitive species records, and county-level aggregation before producing a cleaned specimen dataset and a county summary shapefile ready for geospatial analysis and ArcGIS Online publication.

---

## Requirements

- ArcGIS Pro (arcgispro-py3 conda environment)
- Python 3.x with the following libraries:
  - `pandas`
  - `geopandas`
  - `numpy`
  - `os` (standard library)

---

## Folder Structure

```
UCO_Herbarium_ETL_Pipeline/
│
├── data/
│   ├── CSUoccurrences.csv            # Raw specimen data from TORCH portal (replace each run)
│   ├── okCounties.geojson            # Oklahoma county polygons (authoritative source)
│   ├── okStateTracking.csv           # Oklahoma State Tracking List
│   ├── cleanedCSUoccurrences.csv     # Pipeline output — specimen dataset (created each run)
│   └── countySHP/
│       └── countyDataOutput.shp      # Pipeline output — county summary (created each run)
│
├── logs/
│   ├── countyMismatches.csv          # Records where coordinates don't match listed county
│   ├── entriesNotInOK.csv            # Records with coordinates outside Oklahoma
│   ├── trackingListMatches.csv       # Records successfully matched to tracking list
│   ├── excludedSensitiveSpecimens.csv  # Records redacted from public-facing deliverables
│   └── unreferenceableSpecimens.csv  # Records with no coordinates and no county (conditional)
│
├── UCO_Herbarium_ETL_Pipeline.py
└── README.md
```

---

## Data Sources

| File | Source | Notes |
|------|--------|-------|
| `CSUoccurrences.csv` | TORCH Portal — UCO collection export | Replace with new download each run |
| `okCounties.geojson` | US Census Bureau TIGER/Line | 77 Oklahoma counties, EPSG:4326 |
| `okStateTracking.csv` | Oklahoma Department of Wildlife Conservation | State/Global/Federal rankings |

---

## How to Run

1. Download a fresh occurrence export from the TORCH Portal in Darwin Core CSV format
2. Replace `./data/CSUoccurrences.csv` with the new file — keep the filename the same
3. Open ArcGIS Pro and launch the arcgispro-py3 Python environment
4. Run `UCO_Herbarium_ETL_Pipeline.py`
5. Review log files in `./logs/` for any data quality issues
6. The cleaned specimen dataset will be written to `./data/cleanedCSUoccurrences.csv`
7. The county summary shapefile will be written to `./data/countySHP/countyDataOutput.shp`

---

## Pipeline Blocks

### Block 1 — Centroid Assignment
Records with null coordinates but a valid county name are assigned the authoritative centroid of their listed county, calculated from `okCounties.geojson` using EPSG:5070 (NAD83 Conus Albers Equal Area) for geometric accuracy. Centroid values are stored in `calcLat` and `calcLon` fields; original coordinates are preserved in `decimalLatitude` and `decimalLongitude`. Any entries with no county name and null coordinates are removed from the dataset and exported to `./logs/unreferenceableSpecimens.csv`.

### Block 2 — Geographic Precision Field
A `geographicPrecision` field is created with any of three values:
- `PRECISE` — coordinates verified by georeferencer; have 'TRUE' value in 'georeferencedVerificationStatus' field
- `ASSIGNED CENTROID` — coordinates not provided; county centroid assigned by pipeline
- `PRECISION UNVERIFIED` — coordinates exist but 'georeferencedVerificationStatus' field was null or contained 'FALSE' valuez

### Block 3 — Spatial Join and County Validation
All records are spatially joined against Oklahoma county polygons. Records whose coordinates don't fall within their listed county are flagged and exported to `./logs/countyMismatches.csv` for manual review. Records falling outside Oklahoma entirely are removed from the dataset and exported to `./logs/entriesNotInOK.csv`. County information is permanently joined to the dataset, including `countyNameFromJoin` and `countyFIPS`; these values are used in downstream aggregation.

### Block 4 — Oklahoma State Tracking List Join
Each record is enriched with columns from the Oklahoma State Tracking List (`State Rank`, `Global Rank`, `Federal Status`) via a composite taxonomic key built from genus, specific epithet, and infraspecific rank. The tracking list is available at [https://obis.ou.edu/tracking-list](https://obis.ou.edu/tracking-list). An `onTrackingList` boolean field is added to flag successful matches.

### Block 5 — Sensitive Species Redaction
Records belonging to excluded families or species are removed from the public-facing dataset and logged to `./logs/excludedSensitiveSpecimens.csv`. The default exclusion list is:

- **Family:** Orchidaceae (all orchid species)
- **Species:** *Echinocactus texensis* (Horse Crippler Cactus)

To add additional excluded species or families, edit the lists near the top of the script:

```python
excludedSpecies = [
    "Echinocactus texensis",
    "Genus species"        # add here
]

excludedFamilies = [
    "Orchidaceae",
    "FamilyName"           # add here
]
```

### Block 6 — County-Level Aggregation
Block 6 consumes the final redacted specimen dataset produced in Block 5 and aggregates specimen counts and Oklahoma state ranking counts to the county level. Aggregation is performed entirely via pandas `value_counts()` and `groupby/unstack` — no additional spatial join is required after Block 3. The output is a shapefile with one row per Oklahoma county containing the following derived fields:

| Field | Description |
|-------|-------------|
| `specCnt` | Total number of non-sensitive specimens recorded in that county |
| `trackCnt` | Number of specimens with a successful Oklahoma Tracking List match |
| `rankS1` | Count of S1-ranked specimens per county (critically imperiled) |
| `rankS2` | Count of S2-ranked specimens per county (imperiled) |
| `rankS3` | Count of S3-ranked specimens per county (vulnerable) |
| `rankSH` | Count of SH-ranked specimens per county (possibly extirpated) |

Counties with zero specimens receive `0` in all count fields. The `./data/countySHP/` directory is excluded from version control via `.gitignore`; a `.gitkeep` file preserves the folder structure in the repository.

---

## Output

| File | Description |
|------|-------------|
| `./data/cleanedCSUoccurrences.csv` | Final cleaned specimen dataset for geospatial analysis and AGOL publication |
| `./data/countySHP/countyDataOutput.shp` | County summary shapefile with aggregated specimen and ranking counts |
| `./logs/countyMismatches.csv` | Records flagged for manual coordinate review |
| `./logs/entriesNotInOK.csv` | Records removed — coordinates outside Oklahoma |
| `./logs/trackingListMatches.csv` | Records matched to Oklahoma State Tracking List |
| `./logs/excludedSensitiveSpecimens.csv` | Records redacted from public-facing deliverables |
| `./logs/unreferenceableSpecimens.csv` | Records removed — no coordinates and no county name (conditional) |

---

## Notes

- The pipeline performs a full overwrite on each run — no incremental comparison
- County name normalization is applied to handle case inconsistencies in source data
- Coordinate validation uses a spatial within predicate against authoritative county polygons
- Mismatched county records are flagged for client review but retained in the dataset
- CRS for spatial operations: EPSG:4326 (WGS84); centroid calculation uses EPSG:5070 (NAD83 Conus Albers)
- County shapefile is output in EPSG:4326 for direct compatibility with ArcGIS Online