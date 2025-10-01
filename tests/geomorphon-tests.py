###############################################
### Author: Spenser
### Date: Nov 17th 2025
### Description: Testing the geomorphon methods
###############################################

# %% Import Modules

# Path
import os

# Timing
import time
from pathlib import Path

# Geospatial
import geopandas as gp
import grass_session
import laspy

# Plotting
import matplotlib.pyplot as plt

# Numpy
import numpy as np
import polars as pl
from pyproj import CRS, Transformer

# Change to S3
lidar_dir = Path(r"C:\Users\seth1\source\git-lab\unmarked-graves-las")
lidar_path = lidar_dir.joinpath(
    r"USGS_LPC_FL_Peninsular_FDEM_2018_D19_DRRA_LID2019_218755_E.las"
)

# %% Loading the Data

# %% Grass Session

# Check the file metadata
