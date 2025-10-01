########################################################
### Author: Spenser
### Date: 23 Nov 2025
### Description: Using grass gis to create buffers around
###                FMSF historic sites

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

#Timing
import time


#Import Paths 
from unmarkedpaths import UnMarkedFiles
las_path = Path(UnMarkedFiles.las_path)

#%% Setting up the Grass Params
from grasspaths import GrassConfigs

def grass_params(gisdb, location, mapset):
    os.environ['GISDBASE'] = gisdb
    os.environ['LOCATION_NAME'] = location
    os.environ['PDAL'] = '/Documents/ConsultingWork/venvs/lidarvenv/lib/python3.13/site-packages'


#Grabbing ESPG from laspy file
las_espg = CRS.from_wkt(str(laspy.read(las_path).header.parse_crs())).sub_crs_list[0].to_epsg()

#Appending python path
sys.path.append(GrassConfigs.GRASS_PY_PATH)

## Import GRASS Python bindings
import grass.script as gs
import grass.jupyter as gj    #Try this, will allow for interactive maps

## Starting the session
session  = gj.init(Path(GrassConfigs.emmett_reed))

#%% Importing the FMSF data
fmsf_fname = GrassConfigs.fmsf_fname

#%% 
gs.run_command(
                'v.import'
                ,input = fmsf_fname
)


#%% Adding the buffer
#Gettng Vector Map Name
slash_idx = str(fmsf_fname).rfind('/')
vector_map_fname = str(fmsf_fname)[(slash_idx +1) :-4]

#Runing the command
gs.run_command(
                'v.buffer'
                ,input = vector_map_fname
                ,output = f'{vector_map_fname}_quart_mi_buffered'
                ,where = '1=1'
                # ,type = 'point'
                ,distance = '1320'  #1/4 mi
)

gs.run_command(
                'v.buffer'
                ,input = vector_map_fname
                ,output = f'{vector_map_fname}_half_mi_buffered'
                ,where = '1=1'
                # ,type = 'point'
                ,distance = '2640'  #1/2 mi
)