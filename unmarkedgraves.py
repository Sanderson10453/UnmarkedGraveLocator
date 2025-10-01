#%% Import Modules
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


#%% Define Class and methods
class GraveExploration(self):

    def scoring_index(self):
        """This will create the composite scores that are key to the RAG index"""

    def get_projected_shp(geopd_df, project_object = True):
        """Returns a CRS Projection from a file
        
        Parameters
        ----------
        filename : str, path object or file-like object
        The absolute path to the file 

        Examples
        --------
        >>> df = get_projection("nybb.shp")  # doctest: +SKIP

        """
        shp = geopd_df

        #Checking if projected or not
        if shp.crs.is_projected and project_object == False:
            pass

        elif shp.crs.is_projected and project_object==True:
            pass

        elif shp.crs.is_projected == False and project_object==True:
            ## Going to Reproj
            print("A heads-up, going to project this to Florida East ESPG") 
            
            #Projecting
            shp_proj = shp.to_crs(2236)

            return shp_proj
        
        elif shp.crs.is_projected == False and project_object==False:
            print('Please provide and espg')

    def historical_buffer(self, fname = Path, shapefile_writ_path = Path):
        
        ## Readshapefile
        shapefile_df = self.get_projected_shp(gp.read_file(fname))

        ## Create Buffer
        shapefile_df_buff = shapefile_df.buffer(1320)   #1/4 mile  buffer

        #Display 
        shapefile_df_buff.plot()

        #Writing 
        shapefile_df_buff.to_file(shapefile_writ_path, driver='ESRI Shapefile')