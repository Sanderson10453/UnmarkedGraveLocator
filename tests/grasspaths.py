####################################
### Author: Spenser
### Date: 23  Nov 2025
### Description: Grass GIS setup
#####################################

import os 
import subprocess
import sys
from pathlib import Path

# Getting grass python
class GrassConfigs:
    if os.name == 'posix':
        GRASS_PY_PATH = subprocess.check_output(["grass", "--config", "python_path"], text=True).strip()
    elif os.name =='nt':
        grass_cmd = [r'C:\\Program Files\\GRASS GIS 8.4\\grass84.bat', "--config", "python_path"] 
        GRASS_PY_PATH = subprocess.check_output(["grass", "--config", "python_path"], text=True, shell=True).strip()
    else: 
            GRASS_PY_PATH = None
    
    
    ##Adding USB Path for fmsf
    if os.name == 'posix':
        import getpass
        
        fmsf_fname = Path(f'/media/{getpass.getuser()}/Samsung USB/lidar/Duval/Duval_Sites.shp')
        # fmsf_fname = Path(r'/media/{getpass.getuser()}/Samsung USB/lidar/Duval/Duval_Cemeteries.shp')
    elif os.name == 'nt':
         fmsf_fname = ""
    
    #
    emmett_reed = Path(__file__).parents[3].joinpath('grass-projects/unmarkedgraves-test/unmarked-graves-jax-test/emmett-reed')


    # These are in decimal degrees; need to figure out how to switch to proj coords
    emmett_reed_N = '30.345979861389505'
    emmett_reed_S = '30.34302248426919'
    emmett_reed_E = '-81.66937185766479'
    emmett_reed_W = '-81.67129568821811'

    emmett_reed_n = 2187500
    emmett_reed_s = 2185000
    emmett_reed_e = 445000
    emmett_reed_w = 441729

    # def grass_env_act():
    #     activate_txt = "lidar-act"
    #     subprocess.call(activate_txt)
    

