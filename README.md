# UCO Herbarium ETL Pipeline

**Created by:** Marc Wright  
**Created on:** 06.01.2026  
**Client:** Dr. Messick, University of Central Oklahoma Herbarium


> ###################################################################################################
> ###################################################################################################
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
> ###################################################################################################
> ###################################################################################################

---

## Overview

This pipeline processes herbarium specimen occurrence data downloaded from the [TORCH Portal](https://portal.torcherbaria.org/) in Darwin Core CSV format. It performs coordinate validation, county-level geographic accuracy checks, taxonomic enrichment against the Oklahoma State Tracking List, and redaction of sensitive species records before producing a cleaned dataset ready for geospatial analysis and ArcGIS Online publication.

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
│   ├── CSUoccurrences.csv        # Raw specimen data from TORCH portal (replace on each run)
│   ├── okCounties.geojson        # Oklahoma county polygons (authoritative source)
│   └── okStateTracking.csv       # Oklahoma State Tracking List
│
├── logs/
│   ├── countyMismatches.csv      # Records where coordinates don't match listed county
│   ├── entriesNotInOK.csv        # Records with coordinates outside Oklahoma
│   ├── trackingListMatches.csv   # Records successfully matched to tracking list
│   └── excludedSensitiveSpecies.csv  # Records redacted from public-facing deliverables
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
6. The cleaned output will be written to `./data/cleanedCSUoccurrences.csv`

---

## Pipeline Blocks

### Block 1 — Centroid Assignment
Records with null coordinates but a valid county name are assigned the authoritative centroid of their listed county, calculated from `okCounties.geojson` using EPSG:5070 (NAD83 Conus Albers Equal Area) for geometric accuracy. Centroid values are stored in `calcLat` and `calcLon` fields; original coordinates are preserved in `decimalLatitude` and `decimalLongitude`. 
Any entries with no county name and null coordinates are removed from dataset and exported to './logs/unreferenceableSpecimens.csv'

### Block 2 — Geographic Precision Field
A `geographicPrecision` field is created with three values:
- `PRECISE` — coordinates verified by georeferencer
- `COUNTY CENTROID` — coordinates assigned but not verified; mostly county centroid coordinates
- `ASSIGNED CENTROID` — coordinates not provided; county centroid assigned by pipeline

### Block 3 — Spatial Join and County Validation
All records are spatially joined against Oklahoma county polygons. Records whose coordinates don't fall within their listed county are flagged and exported to `./logs/countyMismatches.csv` for manual review. Records falling outside Oklahoma entirely are removed from the dataset and exported to `./logs/entriesNotInOK.csv`.
County information is permanently joined to dataset, including countyNameFromJoin and the countyFIPS code; these values will be used in the geospatial analysis.

### Block 4 — Table join with OK state vegetative tracking list [available at https://obis.ou.edu/tracking-list]
The pipeline also enriches each record with columns from the Oklahoma State Tracking List (`State Rank`, `Global Rank`, `Federal Status`) via a composite taxonomic key built from genus, specific epithet, and infraspecific rank.

### Block 5 — Sensitive Species Redaction
Records belonging to excluded families or species are removed from the public-facing dataset and logged to `./logs/excludedSensitiveSpecies.csv`. The default exclusion list is:

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

---

## Output

| File | Description |
|------|-------------|
| `./data/cleanedCSUoccurrences.csv` | Final cleaned dataset for geospatial analysis and AGOL publication |
| `./logs/countyMismatches.csv` | Records flagged for manual coordinate review |
| `./logs/entriesNotInOK.csv` | Records removed — coordinates outside Oklahoma |
| `./logs/trackingListMatches.csv` | Records matched to Oklahoma State Tracking List |
| `./logs/excludedSensitiveSpecies.csv` | Records redacted from public-facing deliverables |

---

## Notes

- The pipeline performs a full overwrite on each run — no incremental comparison
- County name normalization is applied to handle case inconsistencies in source data
- Coordinate validation uses a spatial within predicate against authoritative county polygons
- Mismatched county records are flagged for client review but retained in the dataset
- CRS for spatial operations: EPSG:4326 (WGS84); centroid calculation uses EPSG:5070 (NAD83 Conus Albers)
