######################################################
# Author: Spenser
# Date: 22nd Nov 2025
# Description: This is the test to solidify the
#              elevation from lidar cloud data
######################################################


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

#Timing
import time


#Import Paths 
from unmarkedpaths import UnMarkedFiles
las_path = Path(UnMarkedFiles.las_path)


#%% Setting up the Grass Params
from grasspaths import GrassConfigs

#Grabbing ESPG from laspy file
las_espg = CRS.from_wkt(str(laspy.read(las_path).header.parse_crs())).sub_crs_list[0].to_epsg()

#Appending python path
sys.path.append(GrassConfigs.GRASS_PY_PATH)

## Import GRASS Python bindings
import grass.script as gs
import grass.jupyter as gj    #Try this, will allow for interactive maps

# full path to new project (formerly: location)
# project_path = (Path(__file__).parents[1]).joinpath(r'grass-projects/unmarkedgraves-test').absolute()
project_path = GrassConfigs.emmett_reed

## Checking if Project & Mapset has been created
if os.path.exists(GrassConfigs.emmett_reed):
    print('Project Exists')

else:
    try:
        gs.create_project(project_path
                        ,epsg= las_espg
                        ,overwrite = True)   #Will not overwrite current

    except PermissionError as e:
        print('Running in Grass, cant make dir')

#Checking the session is running
# session = gj.init(project_path)  
session  = gj.init(Path(GrassConfigs.emmett_reed))

las_test_output = Path(__file__).joinpath('test-output')


#%% 
#Gettng Vector Map Name
slash_idx = str(las_path).rfind('/')
vector_map_fname = str(las_path)[(slash_idx +1) :-4]

#%% Creating List of Maps
map_dict = gs.parse_command(
                    'g.list'
                    ,type = 'all'
                        )
# Creating list of names
map_ls = [k for k in map_dict.keys()]
print(map_ls)
#%% Elevation Testing

# Check if file exists
if f'{vector_map_fname[-15:]}_min' in map_ls : 
    print('Elevation Layer Exists')
else:
## Reading the las
    gs.run_command(
        "r.in.pdal"
        ,input = las_path
        ,method = 'min'
        ,overwrite = True
        ,resolution = 2
        ,output = f'{vector_map_fname[-15:]}_min'   #The results of the min seem better

    )

#%% Writing Neighborhood Models to Compare Elev

## Minimum Output
gs.run_command(
    'r.neighbors'
    ,input=f'{vector_map_fname[-15:]}_min'
    ,output = f'{vector_map_fname[-15:]}_min_neighbor'
    ,method = 'min'
    ,size = 7
)

#%% Comparing Between Original DEM 
# Calculation
gs.run_command(
    'r.mapcalc'
    ,expression = f"diff = {vector_map_fname[-15:]}_min - {vector_map_fname[-15:]}_min_neighbor"
            )

