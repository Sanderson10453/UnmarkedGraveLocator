#########################################################
### Author: Spenser
### Date: 23 Nov 2025
### Description: Attempting to get Grass GIS to work
###                 as a standalone

#########################################################

#%% Import modules

#Path
from pathlib import Path
import sys
import os

#Geospatial
import geopandas as gp
import laspy
from pyproj import CRS, Transformer

#Numpy
import numpy as np
import polars as pl

#Timing
import time

#Plotting
import matplotlib.pyplot as plt
import seaborn as sns

#Import Paths 
from unmarkedpaths import UnMarkedFiles
las_path = Path(UnMarkedFiles.las_path)


#%% Setting up the Grass Params
from grasspaths import GrassConfigs

#Grabbing ESPG from laspy file
las_espg = CRS.from_wkt(str(laspy.read(las_path).header.parse_crs())).sub_crs_list[0].to_epsg()

#Appending python path
sys.path.append(GrassConfigs.GRASS_PY_PATH)
grassdata = "/xxx/xxxx/grassdata/"
location = "nc_spm_08_grass7"
mapset = "user1"

# Import GRASS Python bindings
import grass.script as gs

# full path to new project (formerly: location)
project_path = (Path.cwd().parents[1]).joinpath(r'grass-projects/unmarkedgraves-test')

gs.create_project(project_path
                  ,epsg= las_espg
                  ,overwrite = False)   #Will not overwrite current
