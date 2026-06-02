###################################################################################################
####
####UCO Herbarium ETL Pipeline
####created by: Marc Wright
####created on: 06.01.2026
####
###################################################################################################

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


###################################################################################################
####
####Block #1: Centroid assignment for records with null coordinates
####
###################################################################################################

##print statement informing user that centroid calculation is taking place on entries
##with null coordinates and that results will be printed to console
print("\n")
print("Calculating county centroids for records with null coordinate values...")
print("\n")

##normalize county names in both datasets to ensure they match
csuData["cleanName"] = csuData["county"].str.strip().str.title()
countyData["cleanName"] = countyData["NAME"].str.strip().str.title()

##project into EPSG: 5070 to calculate accurate centroids
countyData["county_lat"] = countyData.geometry.to_crs(epsg = 5070).centroid.to_crs(epsg = 4326).y
countyData["county_lon"] = countyData.geometry.to_crs(epsg = 5070).centroid.to_crs(epsg = 4326).x

##create new columns in df for calculated Lat / Long 
##and copy original coordindates
csuData["calcLat"] = csuData["decimalLatitude"]
csuData["calcLon"] = csuData["decimalLongitude"]

##create a mask for rows where calcLat / calcLon are null
latMask = csuData["calcLat"].isnull()
lonMask = csuData["calcLon"].isnull()

##for rows where calcLat / calcLon are null, 
##fill in the values from the gdf using the cleanName as the key
lookupLat = countyData.set_index("cleanName")["county_lat"]
lookupLon = countyData.set_index("cleanName")["county_lon"]

##use .loc to fill in the missing coordinate values in df
csuData.loc[latMask, "calcLat"] = csuData.loc[latMask, "cleanName"].map(lookupLat)
csuData.loc[lonMask, "calcLon"] = csuData.loc[lonMask, "cleanName"].map(lookupLon)

##test print statement to verify that records with null coordinates have been filled
print("Number of null values in calcLat and calcLon after centroid calculation:")
print(csuData[["calcLat", "calcLon"]].isna().sum())
print("\n")


###################################################################################################
####
####Block #2: Geographic precision column creation 
####
###################################################################################################

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

##print test statement to sum number of records in each category of geographicPrecision
print("Number of records in each category of geographicPrecision:")
print("""NOTE: 'Assigned' indicates records where county centroid was calculated
      and assigned due to no value given in the georeferenceVerificationStatus field; 
      coordinate accuracy could not be verified for these records.""")
print("\n")
print(csuData['geographicPrecision'].value_counts())
print("\n")


###################################################################################################
####
####Block #3: Spatial join to check for geographic accuracy between county and coordinates
####
###################################################################################################

##assign csuOccurrences to geodataframe
csuGeoData = gpd.GeoDataFrame(
    csuData,
    geometry = gpd.points_from_xy(csuData.calcLon,
                                  csuData.calcLat),
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

##print statements to summarize the results of the spatial join and accuracy check
print("Summary of spatial join and geographic accuracy check:")
print("\n")
print(f"Total points analyzed: {len(joinedPointsWithCounty)}")
print(f"Points listed in wrong county: {len(misMatched)}")
print(f"Points listed outside of Oklahoma: {len(notInOK)}")
print("Removing records listed outside of Oklahoma from dataset...")
print("\n")


##export mismatched entries w/ print statement showing location of export file
exportMismatches = misMatched[["id", "county", "stateProvince", "NAME",
                               "decimalLongitude", "decimalLatitude"]]
mismatchFile = "./data/countyMismatches.csv"
exportMismatches.to_csv(mismatchFile, index = False)
print(f"Exporting mismatched specimen entries to: '{mismatchFile}...'")

##export entries not in Oklahoma w/ print statement showing location of export file
exportNotInOK = notInOK[["id", "county", "stateProvince", "NAME",
                               "decimalLongitude", "decimalLatitude"]]
notInOkFile = "./data/entriesNotInOK.csv"
exportNotInOK.to_csv(notInOkFile, index = False)
print(f"Exporting specimen entries outside of Oklahoma to: '{notInOkFile}...'")
print("\n")

##remove notInOk entries from CSUoccurrences and proceed to tracking list join w/ print 
##statement informing user of removal
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

##merge tracking list with csuData to add tracking status information w/ print statements to confirm merge 
##and # of successful matches with tracking list
matchCount = csuData[csuData['genusSpecies'].isin(trackData['Scientific Name'])]['genusSpecies'].count()
csuData = csuData.merge(trackData[["Scientific Name", "State Rank", "Global Rank", "Federal Status"]], 
                        left_on="genusSpecies", right_on="Scientific Name", how = "left")
print("Merging OK tracking list with CSUoccurrences dataset to add ranking information...")
print(f"Number of records in CSUoccurrences after merge: {len(csuData)}")
print(f"Number of successful joins with tracking list: {matchCount}")
print("\n")


###################################################################################################
####
####Block #4: Redaction of sensitive species records and export of cleaned dataset
####
###################################################################################################

##filteredData = csuData[csuData['family'] != "Orchidaceae"]
##removedCount = len(csuData) - len(filteredData)

##print(csuData.shape)
##print(filteredData.shape)
##print(f"Number of records removed: {removedCount}")
