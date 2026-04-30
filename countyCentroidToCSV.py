import geopandas as gpd
import pandas as pd

okCounties = "C:/Users/MWright/Desktop/PythonScripts/pythonLearn/data/okCounties.geojson"

countyData = gpd.read_file(okCounties)
countyProject = countyData.to_crs("EPSG:2267")
centroidData = countyProject.geometry.centroid
wgsCentroidData = centroidData.to_crs("EPSG:4326")

countyData["lon"] = wgsCentroidData.x
countyData["lat"] = wgsCentroidData.y

export_DF = countyData[["NAME", "lat", "lon"]]
export_DF = export_DF.round({"lat": 6, "lon": 6})
export_DF.to_csv("./data/okCounties.csv", index = False)

print(export_DF)
