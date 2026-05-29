##import libraries
import numpy as np
import pandas as pd
import geopandas as gpd
import os

##set current working directory to location of Python script file
os.chdir(os.path.dirname(os.path.abspath(__file__)))

##location of CSUoccurrences csv file
csuFile = "./data/CSUoccurrences.csv"
csuData = pd.read_csv(csuFile, encoding = 'latin-1',
                      low_memory = False,
                      na_values = [""],
                      dtype = {'identificationQualifier': str,
                               'references': str})
csuData = csuData.reset_index(drop = True)

##location of okCounties csv file
countiesFile = "./data/okCounties.geojson"
countyData = gpd.read_file(countiesFile)

##location of okTrackingList csv file
trackFile = "./data/okStateTracking.csv"
trackData = pd.read_csv(trackFile)

##check to see if any specimens contain null geographic coordinates
print(csuData[['decimalLatitude',
               'decimalLongitude']].isna().sum())
print("\n")
##TO-DO: centroid assignment for records with null coordinates
##requires spatial join with countyData geoJSON
##no null coordinates in current dataset - will implement if needed

##create geographicPrecision field and populate based on conditions
conditions = [
    (csuData['georeferenceVerificationStatus'] == True),
    (csuData['georeferenceVerificationStatus'] == False),
    (csuData['georeferenceVerificationStatus'].isna())
]

choices = ['True', 'False', 'Assigned']
csuData['geographicPrecision'] = np.select(conditions,
                                           choices,
                                           default = "Unknown")

print(csuData['geographicPrecision'].value_counts())
print("\n")

##assign csuOccurrences to geodataframe
csuGeoData = gpd.GeoDataFrame(
    csuData,
    geometry = gpd.points_from_xy(csuData.decimalLongitude,
                                  csuData.decimalLatitude),
    crs = "EPSG:4326"
)

##perform spatial join between csuOccurrences and OKcounties to
##ensure geographic precision
joinedPointsWithCounty = gpd.sjoin(csuGeoData, countyData,
                                   how = "left",
                                   predicate = "within")

##create match column that formats county name between two datasets
joinedPointsWithCounty["countyMatch"] = (
    joinedPointsWithCounty["county"].str.strip().str.lower() ==
    joinedPointsWithCounty["NAME"].str.strip().str.lower()
)

notInOK = joinedPointsWithCounty[joinedPointsWithCounty["NAME"].isna()]
misMatched = joinedPointsWithCounty[(~joinedPointsWithCounty["countyMatch"]) &
                                    (joinedPointsWithCounty["NAME"].notna())
]

print(f"Total points analyzed: {len(joinedPointsWithCounty)}")
print(f"Points listed in wrong county: {len(misMatched)}")
print(f"Points listed outside of Oklahoma: {len(notInOK)}")
print("\n")
print(notInOK[['genus', 'specificEpithet', 'county', 'decimalLatitude', 'decimalLongitude']].head(10))
print(csuData[csuData['decimalLatitude'].isna()].shape)

##export mismatched entries
exportMismatches = misMatched[["id", "county", "stateProvince", "NAME",
                               "decimalLongitude", "decimalLatitude"]]
mismatchFile = "./data/countyMismatches.csv"
exportMismatches.to_csv(mismatchFile, index = False)
print(f"Exporting mismatched specimen entries to: '{mismatchFile}...'")

##export entries not in Oklahoma
exportNotInOK = notInOK[["id", "county", "stateProvince", "NAME",
                               "decimalLongitude", "decimalLatitude"]]
notInOkFile = "./data/entriesNotInOK.csv"
exportNotInOK.to_csv(notInOkFile, index = False)
print(f"Exporting specimen entries outside of Oklahoma to: '{notInOkFile}...'")

print("\n")
print(joinedPointsWithCounty["countyMatch"].value_counts(dropna = False))

##extract notInOk entries from CSUoccurrences and proceed to tracking list join
csuData = csuData[~csuData["id"].isin(notInOK["id"])]

csuData["genusSpecies"] = (
    csuData["genus"].str.strip().str.capitalize() + " " +
    csuData["specificEpithet"].str.strip().str.lower() +
    np.where(
        csuData["verbatimTaxonRank"].notna(),
        " " + csuData["verbatimTaxonRank"].str.replace("subsp.", "ssp.") + " " +
        csuData["infraspecificEpithet"].str.strip(),
        ""
    )
)
print("\n")
print(trackData[trackData["Scientific Name"].isin(csuData["genusSpecies"])].shape)
print(csuData[csuData["genusSpecies"].isin(trackData["Scientific Name"])]["genusSpecies"].count())
print("\n")
print(csuData[csuData['decimalLatitude'].round(6) == 35.551495][['county', 'decimalLatitude', 'decimalLongitude']].head(5))
print("\n")



##filteredData = csuData[csuData['family'] != "Orchidaceae"]
##removedCount = len(csuData) - len(filteredData)

##print(csuData.shape)
##print(filteredData.shape)
##print(f"Number of records removed: {removedCount}")
