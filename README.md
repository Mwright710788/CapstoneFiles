# UCO Herbarium ETL Pipeline

A Python-based ETL pipeline built to clean, classify, and preprocess 
~11,000 herbarium specimen records from the University of Central 
Oklahoma Herbarium, preparing the dataset for publication to ArcGIS Online in support of a StoryMap deliverable.

## Project Overview

Raw specimen data requires significant preprocessing before it can be 
published as a web layer. This pipeline handles taxonomic field 
cleansing, georeferencing validation, coordinate recalculation to county centroids, QA boundary checks against Oklahoma county boundaries, and lastly executes a left table join with an Oklahoma Tracking List to give state and global threat rankings, where appropriate.

## Tech Stack

- Python (Pandas, GeoPandas)
- ArcGIS Pro
- ArcGIS Online / ArcGIS API for Python
- QGIS
- draw.io (architecture documentation)

## Pipeline Architecture

See `docs/wrightCapstoneFlowchart.drawio` for the full ETL architecture diagram.

## Status

Active development — capstone project for MS in GIS Administration, 
University of West Florida.
