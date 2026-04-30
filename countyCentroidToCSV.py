import geopandas as gpd
import pandas as pd

##location of the Oklahoma Counties geojson file
okCounties = "./data/okCounties.geojson"

countyData = gpd.read_file(okCounties)

##project points from WGS1984 to NAD83 / Oklahoma North (ftUS)
countyProject = countyData.to_crs("EPSG:2267")

##calculate centroid for each county
centroidData = countyProject.geometry.centroid

##project points from NAD83 back to WGS1984
wgsCentroidData = centroidData.to_crs("EPSG:4326")

##extract latitude and longitude and insert into the countyData dataframe
countyData["lon"] = wgsCentroidData.x
countyData["lat"] = wgsCentroidData.y

##export only name, lat, and longitude fields from dataframe and
##round to six digits
export_DF = countyData[["NAME", "lat", "lon"]]
export_DF = export_DF.round({"lat": 6, "lon": 6})

##write to csv
export_DF.to_csv("./data/okCounties.csv", index = False)

print(export_DF)
