#########################################################
### Author: Spenser
### Date: 24 Dec 2025
### Description: Test case of the pipeline using Emmett Reed 

#########################################################

#%% 

#Path
from pathlib import Path
import sys
import os
import subprocess

#Geospatial 
import geopandas as gp
import laspy
from pyproj import CRS, Transformer
import pdal

#Numpy
import numpy as np

#Timing
import time

# For cli
import argparse

# Import the Model
try:
    from unmarked_graves_pipeline import UnmarkedGraves
except ImportError:
    sys.path.append(Path(__file__).resolve().parents[1])
    from unmarked_graves_pipeline import UnmarkedGraves

#%% 
print((Path(__file__).parents[0].joinpath(r'USGS_LPC_FL_Peninsular_FDEM_2018_D19_DRRA_LID2019_218756_E.las')))
#%% Running as Grass Jupyter
ug = UnmarkedGraves()

# Setup Env
# ug.setup_grass_env(lidar_fname=(Path(__file__).parents[0].joinpath(r'USGS_LPC_FL_Peninsular_FDEM_2018_D19_DRRA_LID2019_218756_E.las')))

