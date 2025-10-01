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

## Setting the region
extent = gs.read_command(
    "r.in.pdal"
    ,flags ='sg'
    ,input = las_path
    ,overwrite = True
    ,output = vector_map_fname[-15:]
)

#Create Extent
extent_dict = {}
extent_split = extent.split()
for ext_str in extent_split:
    k,v = ext_str.split('=')
    extent_dict[k] = float(v)


gs.run_command(
    'g.region'
    ,n= extent_dict['n']
    ,s=extent_dict['s']
    ,w=extent_dict['w']
    ,e=extent_dict['e']
    ,t=extent_dict['t']
    ,b=extent_dict['b']
)

#%% Testing Importing the Cloud Data 
# gs.read_command(
#     'r.in.usgs'
#     ,flags = 'i'
#     ,product = 'lidar'
#     # ,input_srs = 'ESPG:'
#     ,output_name = 'USGS_EmmettReed_Lidar'
# )

#%% Running Import PDAL Lidar Cloud
gs.run_command(
    "r.in.pdal"
    ,input = las_path
    ,method = 'min'
    ,overwrite = True
    ,resolution = 2
    ,output = f'{vector_map_fname[-15:]}_pdal_min'   #The results of the min seem better

)
#%% Running Import Lidar Cloud

## Reading the las
gs.run_command(
    "r.in.pdal"
    ,input = las_path
    ,method = 'min'
    ,overwrite = True
    ,resolution = 2
    ,output = f'{vector_map_fname[-15:]}_min'   #The results of the min seem better

)

gs.run_command(
    "r.in.pdal"
    ,input = las_path
    ,overwrite = True
    ,resolution = 2
    ,output = f'{vector_map_fname[-15:]}_avg'

)



#%% Creating Mask

gs.run_command(
    'g.region'
    ,n=GrassConfigs.emmett_reed_n
    ,s=GrassConfigs.emmett_reed_s
    ,w=GrassConfigs.emmett_reed_w
    ,e=GrassConfigs.emmett_reed_e
)


# Creating a vector from the region - this will become the mask
gs.run_command(
    'v.in.region'
    ,output = 'emmett_reed_aoe'
    ,overwrite = True
)

# Masking
gs.run_command(
    'r.mask'
    ,vector = 'emmett_reed_aoe'
)

#%% Denoising
# gs.run_command(
#     'r.denoise'
#     ,input=f'{vector_map_fname[-15:]}_min'
#     ,output = f'{vector_map_fname[-15:]}_min_denoise'
#     ,threshold = 0.93
#     ,epsg = las_espg
# )

gs.run_command(
    'r.neighbors'
    ,input=f'{vector_map_fname[-15:]}_min'
    ,output = f'{vector_map_fname[-15:]}_min_neighbor_gaus'
    ,method = 'average'
    ,size = 5
    ,weighting_function = 'gaussian'
    ,weighting_factor = 1
)
#%% Following B Harmon Methods
# Creating Landforms    https://gis.stackexchange.com/questions/421141/extracting-peaks-and-cols-from-a-dtm-raster-and-convert-them-into-point-shapefil
gs.run_command(
    'r.param.scale'
    # ,input = f'{vector_map_fname[-15:]}_min'
    ,input = f'{vector_map_fname[-15:]}_min_neighbor_gaus'
    ,output = f'{vector_map_fname[-15:]}_topo'
    ,size = 21 
    # ,method = 'elev'
    ,method = 'feature'
    ,overwrite = True  
)

# gs.run_command(
#     'r.geomorphon'
#     # ,elevation = f'{vector_map_fname[-15:]}_min'
#     ,elevation = f'{vector_map_fname[-15:]}_min_neighbor_gaus'
#     ,forms = f'{vector_map_fname[-15:]}_geomorp'
#     ,search = 5   #Smaller because flat
#     ,skip = 0
#     ,flat = 1
#     ,overwrite = True  
# )


#%% To do to filter map
gs.run_command(
    'r.param.scale'
    # ,input = f'{vector_map_fname[-15:]}_min'
    ,input = f'{vector_map_fname[-15:]}_min_neighbor_gaus'
    ,output = f'{vector_map_fname[-15:]}_profc'
    ,size = 5 
    ,method = 'profc'
    ,overwrite = True  
)

gs.run_command(
    'r.param.scale'
    # ,input = f'{vector_map_fname[-15:]}_min'
    ,input = f'{vector_map_fname[-15:]}_min_neighbor_gaus'
    ,output = f'{vector_map_fname[-15:]}_planc'
    ,size = 5 
    ,method = 'planc'
    ,overwrite = True  
)

gs.run_command(
    'r.param.scale'
    # ,input = f'{vector_map_fname[-15:]}_min'
    ,input = f'{vector_map_fname[-15:]}_min_neighbor_gaus'
    ,output = f'{vector_map_fname[-15:]}_slope'
    ,size = 5 
    ,method = 'slope'
    ,overwrite = True  
)

gs.run_command(
        'r.mapcalc',
          expression = f'pit_basin_filter = ({vector_map_fname[-15:]}_profc < 0.0) & ({vector_map_fname[-15:]}_planc > 0.0) & ({vector_map_fname[-15:]}_slope < 0.5)'
)
# Explanation of the values:
# profc_map < 0.0: Concave profile (accumulation)
# planc_map > 0.0: Convergent plan (collection)
# slope_map < 0.5: Very low slope (flat bottom/pooling)


#%% Funcs

def comp_extent(xmin,xmax,ymin, ymax):
    """
    This function will set the computing region for our map. You can grab latitude and longitude
    using Google maps. Right click the 4 corners of the area you want, and get the coordinates from there

    Parameters
    ---
    x_min: The smallest longitude/x coordinate for your area you want to read lidar data for. 
            Note: Should be negative if the site is in the Western hemisphere
    x_max: The largest longitude/x coordinate for your area you want to read lidar data for.
            Note: Should be negative if the site is in the Western hemisphere
    y_min: The smallest latitude/y coordinate for your area you want to read lidar data for.
    y_max: The largest latitude/y coordinate for your area you want to read lidar data for.
    """
    #Creating empty list
    missing_args = []
    
    #Checking to see which args, if any are missing
    for arg in [xmin, xmax, ymin, ymax]:
        if arg is None:
            missing_args.append(arg)

    #If nothing is missing, we're all good
    if len(missing_args) == 0:
        comp_region = [xmin, xmax, ymin, ymax]
    else:
        print(f"You're missing the following dimensions {missing_args}. \n We will use the entire raster extent")

