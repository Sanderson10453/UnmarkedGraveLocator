#%% Import modules

#Path
from pathlib import Path
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



#%% Funcs
class ProjectParams:
    lidar_dir = Path(r"C:\Users\seth1\source\git-lab\unmarked-graves-las")
    lidar_path = lidar_dir.joinpath(r"USGS_LPC_FL_Peninsular_FDEM_2018_D19_DRRA_LID2019_218755_E.las")

    def __init__(self, fdir, **kwargs):
        self.fdir = fdir
        self.options = kwargs

class UnmarkedGraves:
    def read_lidar(self):
        dd = 'dd'



        return dd

    def get_las_crs(self, las_df) -> CRS:
        '''Description: This method gets the CRS from the las file for future use.
           Inputs: A las dataset
            Outputs: The CRS as an int '''
        las_crs = CRS.from_wkt(str(las_df.header.parse_crs())).sub_crs_list[0].to_epsg()

        return las_crs

    @property
    def las_bounds(self, las_df):
        '''Description: Grabbing the dimensions of the lidar file in case no bounds are given'''
        minx, miny, maxx, maxy = las_df.total_bounds
        return minx, miny, maxx, maxy

    def proj_las(self, las_df, input_crs, ouput_crs, minx, maxx, miny, maxy) -> np.array:
        '''Description: This method'''

        #Attributes

        start = time.time()
        #Checking Coordinate System
        if input_crs == ouput_crs:
            pass
        else:
            transformer = Transformer.from_crs(input_crs, ouput_crs, always_xy=True)

            # Get the x, y, and z coordinates
            las_x = las_df.x.copy()
            las_y = las_df.y.copy()
            las_z = las_df.z.copy()

            #Chunking
            chunk_size = 100000
            for i in range(0,len(las_df), chunk_size):

                chunk_x = las_df.x[i:i + chunk_size]
                chunk_y = las_df.y[i:i + chunk_size]
                chunk_z = las_df.z[i:i + chunk_size]

                #Projecting
                projected_x, projected_y, projected_z = transformer.transform(chunk_x, chunk_y, chunk_z)

                las_x[i:i + chunk_size] = projected_x
                las_y[i:i + chunk_size] = projected_y
                las_z[i:i + chunk_size] = projected_z

            #Replacing vals
            las_df.x = las_x.astype(np.float64)
            las_df.y = las_y.astype(np.float64)
            las_df.z = las_z.astype(np.float64)


        ##Bools for Values
        x_valid = (las_df.x >= minx) & (las_df.x <= maxx)
        y_valid = (las_df.y >= miny) & (las_df.y <= maxy)

        #combined Bools
        valid_points = x_valid & y_valid

        ## Clipping and Converting to Numpy Array
        las_array = np.vstack((las_x,
                            las_y,
                            las_z)
                            ,dtype='float64').transpose()

        #Clipping
        las_array_clipped = las_array[valid_points]
        end = time.time()
        print(f'Elapsed Time {end-start}')

        return las_array_clipped

    def write_las(self,write_path):
