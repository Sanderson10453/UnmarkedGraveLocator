#########################################################
### Author: Spenser
### Date: 17 Dec 2025
### Description: Attempting to get Grass GIS to work
###                 as a standalone

#########################################################


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


# Getting grass python
class GrassConfigs:
    
    # If Linux
    if os.name == 'posix':
        GRASS_PY_PATH = subprocess.check_output(["grass", "--config", "python_path"], text=True).strip()

    # If Windows
    elif os.name =='nt':
        grass_cmd = [r'C:\\Program Files\\GRASS GIS 8.4\\grass84.bat', "--config", "python_path"] 
        GRASS_PY_PATH = subprocess.check_output(grass_cmd, text=True, shell=True).strip()
    
    #Add Mac
    else: 
            GRASS_PY_PATH = None


class UnmarkedGraves(GrassConfigs):
    """
    This class contains all the methods, and essentially the pipeline, to help highlight areas 
        where there may be unmarked graves. To start, when instantiation the class - add your lidar (.las) as a parameter.
       This will allow all the methods to be able to access this same file     
    
    """
    def __init__(self):
        
        ## Declaring Attributes
        self.fname = None
        self.project_path = None
        self.lidar_file = None

        # Ensuring Grass is Initialized
        self._grass_initialized = False


    def setup_grass_env(self
                        ,proj_path : str|Path
                        ,lidar_fname : str|Path):
        """
        This method will start the grass script environment and check if the specified project/location exist.
        
        :param proj_path: Description
        :type proj_path: str | Path
        :return: Description
        :rtype: Any
        """
        if self._grass_initialized:
            return
        

        # full path to new project (formerly: location)
        if isinstance(proj_path, Path):  
            project_path = proj_path
        elif proj_path is str:
            project_path = Path(proj_path)

        # LiDAR File Construction
        if isinstance(lidar_fname, Path):  
            lidar_f = lidar_fname
        elif lidar_fname is str:
            lidar_f = Path(lidar_fname)

        # Updating Attributes
        self.project_path = project_path
        self.lidar_file = lidar_f
        self.dbase = self.project_path.parent
        
        # Appending python path
        sys.path.append(GrassConfigs.GRASS_PY_PATH)



        ## Import GRASS Python bindings
        import grass.script as gs
        import grass.jupyter as gj    #Try this, will allow for interactive maps

        # Ensuring other Modules have access 
        self.gs = gs
        self.gj = gj 

        # Grabbing ESPG from laspy file
        self.las_espg = CRS.from_wkt(str(laspy.read(self.lidar_file).header.parse_crs())).sub_crs_list[0].to_epsg()

        ## Checking if Project & Mapset has been created
        if not self.project_path.exists():

            # Checking if the database exists - if not, create location and project
            # If Linux
            if os.name == 'posix':
                # Creating Database and Perm. location
                subprocess.Popen(["grass", "-c", f"epsg:{self.las_espg}", "-e", f"{self.project_path}"])

                # Creating the Project
                subprocess.Popen(["grass", "-c", f"epsg:{self.las_espg}", "-e", f"{self.project_path.joinpath('unmarked-graves')}"])

            # If Windows
            elif os.name =='nt':
                 # Creating Database and Perm. location
                grass_perm = [r'C:\\Program Files\\GRASS GIS 8.4\\grass84.bat'
                            , "-c" ,f"epsg:{self.las_espg}", "-e", f"{self.project_path}"] 
                subprocess.Popen(grass_perm, shell=True)

                # Creating the Project
                grass_proj = [r'C:\\Program Files\\GRASS GIS 8.4\\grass84.bat'
                            , "-c" , "-e", f"{self.project_path.joinpath('unmarked-graves')}"] 
                subprocess.Popen(grass_perm, shell=True)

            #Checking the session is running
            gj.init(Path(self.project_path.joinpath('unmarked-graves')))
            self._grass_initialized = True
            
        else: 
            #Checking the session is running
            gj.init(Path(self.project_path))
            self._grass_initialized = True

    def list_maps(self):

        ## Parsing
        map_dict = self.gs.parse_command('g.list', type='all')
        map_ls = [map for map in map_dict.keys()]
        return map_ls

    def historical_sites_check(self
                               ,historical_file: str|Path
                               ,overwrite = False):
        """
        This method will be the pipeline component for the first component of our RAG model - whether there is a historic site
            within a set distance of the site. Sites within a quarter mile of a church will be most rewarded, while sites
            that are within a half mile will still receive some points.

            To do so, it does the following steps:
            1. Uses the Florida Master Site Files (unless another file is provided) church and cultural sites
            2. Draws a circular buffer around the sites
            3. Then later checks if our points of interest are within these buffers.

        Input
        ----------
        The Florida Master Site file data is inputted, unless another file is provided.
        
        Parameters:
        ---------
            historical file: String/Path to a shapefile that contains historical sites. If let blank, it will use the FMSF
                            data by default. 
            
            Overwrite: By default this method will not overwrite the already existing buffers; however, if set to True,
                        it will overwrite the buffers. This is not suggested unless you are planning on using a new file.
        
        """  

        ## Attributes
        existance = True   # Assuming vector map does not exist
        
        ## Importing the FMSF

        #Creating a proper path from param
        if historical_file is None:
            fmsf = Path(f'{Path(__file__).cwd().joinpath(r'Duval_Sites.shp')}').resolve()    # Post the FMSF in gitlab
        
        if isinstance(historical_file, Path):
            fmsf = historical_file

        elif isinstance(historical_file, str):
            fmsf = Path(historical_file)

        if overwrite == False:
            'check if buffer exists'

            # If it exists and overwrite is False, then skip running this
            existance = False   

        if existance == False or overwrite == True:
            #Importing
            self.gs.run_command(
                    'v.import'
                    ,input = fmsf
                            )

            ## Adding the Buffer
            #Gettng Vector Map Name
            self.vector_map_fname = fmsf.stem

            #Runing the command
            self.gs.run_command(
                            'v.buffer'
                            ,input = self.vector_map_fname
                            ,output = f'{self.vector_map_fname}_quart_mi_buffered'
                            ,where = '1=1'
                            # ,type = 'point'
                            ,distance = '1320'  #1/4 mi
            )

            self.gs.run_command(
                            'v.buffer'
                            ,input = self.vector_map_fname
                            ,output = f'{self.vector_map_fname}_half_mi_buffered'
                            ,where = '1=1'
                            # ,type = 'point'
                            ,distance = '2640'  #1/2 mi
            )


            print(f'Historical Site Buffer is complete. Find it in Grass GIS under file name \n {self.vector_map_fname}_*_buffered ')
        

    def elevation_check(self
                        ,denoise = True
                        ,low_memory = True
                        ,overwrite = False):        
        """
        This method will be the pipeline component for the next component of our RAG model - does an area have lower elevation than the areas 
            around it?

        Input
        ----------
            lidar_file        
        
        Parameters:
        ---------            
            denoise: True, will use the neighbors to normalize the lidar data
            overwrite: Default - False; if true, will overwrite previous elevation layers of the same name

        Notes:
            On approaches -
            1. Use r.stats/quantiles to create quantiles
                - Filter cells that fall below this value?
            2. Check if there's a way to use r.volume to calculate average elev by clumps?
        
        """

        # LiDAR File Attribute
        # self.lidar_file = lidar_file

        # File Name without Ext
        self.clean_fname = self.lidar_file.stem
        self.clean_path = self.lidar_file.stem
        self.clean_parent = self.lidar_file.parent


        ## Creating list of maps in mapset
        map_ls = self.list_maps()

        ## Elevation Testing

        # Check if file exists
        if f'{self.clean_fname[-15:]}_mean' in map_ls : 
            print('Elevation Layer Exists')
        else:
            ## Reading the las
            self.gs.run_command(
                "r.in.pdal"
                ,input = self.lidar_file
                ,method = 'mean'
                ,overwrite = True
                ,resolution = 1
                ,output = f'{self.clean_fname[-15:]}_mean'  

            )

        ## Writing Neighborhood Models to Compare Elev

        ## Minimum Output
        self.gs.run_command(
            'r.neighbors'
            ,input=f'{self.clean_fname[-15:]}_mean'
            ,output = f'{self.clean_fname[-15:]}_mean_neighbor'
            ,method = 'average'
            ,size = 15
            ,weighting_function = 'gaussian'
            ,weighting_factor = 1
            ,overwrite = True
        )

        ## Comparing Between Original DEM 
        # Calculation
        self.gs.run_command(
            'r.mapcalc'
            ,expression = f"diff = {self.clean_fname[-15:]}_mean - {self.clean_fname[-15:]}_mean_neighbor"
            ,overwrite = True
                    )
        
        ## Checking out Interesting Differences
        # What's noise vs real?
        self.gs.run_command(
            'r.mapcalc'
            ,expression = "diff_deeper = if(diff >= 0.15 && diff <= 0.8, 1, null())"
            ,overwrite = True
                    )
        # If there's a bunch of cells that are low, it's probably true
        self.gs.run_command(
            'r.neighbors'
            ,input = 'diff_deeper'
            ,output = 'diff_cnt'
            ,method = 'count'
            ,size = 3
            ,overwrite = True
                )

        # Final Areas that are lower than neighbors, accounting for noise
        self.gs.run_command(
            'r.mapcalc'
            ,expression = "diff_fin = if(diff_cnt >= 5, diff, null())"
           ,overwrite = True
        )

        # Widening these final areas
        self.gs.run_command(
                    'r.neighbors'
                    ,input= 'diff_fin'
                    ,output = 'diff_fin_wide'
                    ,method = 'minimum'
                    ,size = 5
                    ,overwrite = True
            )

        ## Removing layers if low memory
        if low_memory == True:
            self.gs.run_command(
                'g.remove'
                ,type = 'raster'
                ,name = f'{self.clean_fname[-15:]}_mean_neighbor'
            )

            self.gs.run_command(
                'g.remove'
                ,type = 'raster'
                ,pattern = '*_tmp'
            )
    
    
    def topology_check(self, low_memory = True):
        """
        This method will be the pipeline component for the last component of our RAG model - whether the slope/geomorphology is sloped downward,
            but flat enough to be conducive for a grave.

            To do so, it does the following steps:
            1. 

        Input
        ----------
        The method will use the input from the Lidar class previously made. No added parameters are needed unless there's a separate file you would like to use.
        
        
        Parameters:
        ---------
            lidar_file: If let blank, it will use the previously specified LiDAR (.LAS) file; 
                otherwise, you can specify a specific ground return LiDAR file
            
            low_memory: True, will delete the intermediate map files created while creating the filter. Set to False, they will be preserved
        
        """

        ## Setting the region
        extent = self.gs.read_command(
            "r.in.pdal"
            ,flags ='sg'
            ,input = self.lidar_file
            ,overwrite = True
            ,output = self.clean_fname[-15:]
        )

        #Create Extent
        extent_dict = {}
        extent_split = extent.split()
        for ext_str in extent_split:
            k,v = ext_str.split('=')
            extent_dict[k] = float(v)


        self.gs.run_command(
            'g.region'
            ,n= extent_dict['n']
            ,s=extent_dict['s']
            ,w=extent_dict['w']
            ,e=extent_dict['e']
            ,t=extent_dict['t']
            ,b=extent_dict['b']
            ,grow = 5280
        )


        ## Reading the and de-noising the las 
        # Reading
        self.gs.run_command(
            "r.in.pdal"
            ,input = self.lidar_file
            ,method = 'mean'
            ,overwrite = True
            ,resolution = 1
            ,output = f'{self.clean_fname[-15:]}_mean'   
        )

       # De-noising
        self.gs.run_command(
            'r.neighbors'
            ,input=f'{self.clean_fname[-15:]}_mean'
            ,output = f'{self.clean_fname[-15:]}_mean_neighbor_gaus'
            ,method = 'average'
            ,size = 3
            ,weighting_function = 'gaussian'
            ,weighting_factor = 1
        )

        ## Topology Check
        if low_memory == True:
            self.gs.run_command(
                'r.param.scale'
                ,input = f'{self.clean_fname[-15:]}_mean_neighbor_gaus'
                ,output = f'{self.clean_fname[-15:]}_profc_temp'
                ,size = 3 
                ,method = 'profc'
                ,overwrite = True  
            )

            self.gs.run_command(
                'r.param.scale'
                ,input = f'{self.clean_fname[-15:]}_mean_neighbor_gaus'
                ,output = f'{self.clean_fname[-15:]}_planc_temp'
                ,size = 3 
                ,method = 'planc'
                ,overwrite = True  
            )

            self.gs.run_command(
                'r.param.scale'
                ,input = f'{self.clean_fname[-15:]}_mean_neighbor_gaus'
                ,output = f'{self.clean_fname[-15:]}_slope_temp'
                ,size = 3 
                ,method = 'slope'
                ,overwrite = True  
            )

            self.gs.run_command(
                    'r.mapcalc',
                    expression = f'pit_basin_filter = ({self.clean_fname[-15:]}_profc_temp < 0.0) & ({self.clean_fname[-15:]}_planc_temp > 0.0) & ({self.clean_fname[-15:]}_slope_temp < 0.5)'
            )

            # Widening the area
            self.gs.run_command(
                    'r.neighbors'
                    ,input= 'pit_basin_filter'
                    ,output = 'pit_basin_filter_wide'
                    ,method = 'maximum'
                    ,size = 5
                    ,overwrite = True
            )

            ## Removing layers        
            self.gs.run_command(
                'g.remove'
                ,type = 'raster'
                ,pattern = '*_temp'
                ,quiet = True
            )

        else:
            self.gs.run_command(
            'r.param.scale'
            ,input = f'{self.clean_fname[-15:]}_mean_neighbor_gaus'
            ,output = f'{self.clean_fname[-15:]}_profc'
            ,size = 3 
            ,method = 'profc'
            ,overwrite = True  
        )

            self.gs.run_command(
                'r.param.scale'
                ,input = f'{self.clean_fname[-15:]}_mean_neighbor_gaus'
                ,output = f'{self.clean_fname[-15:]}_planc'
                ,size = 3 
                ,method = 'planc'
                ,overwrite = True  
            )

            self.gs.run_command(
                'r.param.scale'
                ,input = f'{self.clean_fname[-15:]}_mean_neighbor_gaus'
                ,output = f'{self.clean_fname[-15:]}_slope'
                ,size = 3 
                ,method = 'slope'
                ,overwrite = True  
            )

            self.gs.run_command(
                    'r.mapcalc',
                    expression = f'pit_basin_filter = ({self.clean_fname[-15:]}_profc < 0.0) & ({self.clean_fname[-15:]}_planc > 0.0) & ({self.clean_fname[-15:]}_slope < 0.5)'
            )

            # Widening the area
            self.gs.run_command(
                    'r.neighbors'
                    ,input= 'pit_basin_filter'
                    ,output = 'pit_basin_filter_wide'
                    ,method = 'maximum'
                    ,size = 5
                    ,overwrite = True
            )


    def rag_ranking(self, low_memory = True, shapefile = False, text_file = True):
        """
        This is the final method to group the areas into 3 categories:
            1. Red, where we believe there are potential unmarked graves
            2. Amber, where we think there may be unmarked graves
            3. Green, areas we do not think there are unmarked graves
        
        :param low_memory: True, will delete the intermediate map files created while creating the filter. Set to False, they will be preserved
        """

        ### Create Index of PLaces that meet highest criteria
        ## Part 1: Red Sites

        # Step 1: Get Parts of the Raster part of the FMSF Buffer
        self.gs.run_command(
            'r.mask'    # Could clip (r.clip) the raster too instead
            ,vector = f'{self.vector_map_fname}_quart_mi_buffered'
        )
        
        # Step 2: Filtering on Elevation and Topology
        self.gs.run_command(
            'r.mapcalc'
            ,expression = 'red_sites = if(pit_basin_filter_wide == 1 && diff_fin_wide < 1, 1, null())'  # Getting the sites that are the lowest and basins, within our mask
        )

        # Step 3: Remove the Mask
        self.gs.run_command(
            'r.mask'
            ,flags = 'r'
        )

        # Step 4: Grow the Spots
        self.gs.run_command(
            'r.grow'
            ,input = 'red_sites'
            ,output = 'red_sites_grow'
            ,radius = 3
            ,metric = 'euclidean'
            ,overwrite = True
        )

         ## Optional Step 5: Create Shapefiles
        if shapefile == True:

            # Making the Raster into a vector file
            self.gs.run_command('r.to.vect'
                                ,input = 'red_sites_grow'
                                ,output = 'red_sites_grow_vect'
                                ,type = 'area')
            
            # Writing to Shapefile
            self.gs.run_command('v.out.ogr'
                                ,input = 'red_sites_grow_vect'
                                ,output = f'{Path(__file__).parent.resolve().joinpath('outputs/red_sites.shp')}'
                                ,format = 'ESRI_Shapefile'
                                ,type = 'area')

        ## Part 2: Amber Sites
        # Step 1: Sites that are part of the 1/4 mile buffer
        self.gs.run_command(
            'r.mask'    # Could clip (r.clip) the raster too instead
            ,vector = f'{self.vector_map_fname}_quart_mi_buffered'
        )

        # Step 2: Filtering on Elevation and Topology -- Figure out the next category
        self.gs.run_command(
            'r.mapcalc'
            ,expression = 'amber_sites_0 = if(pit_basin_filter_wide == 1 && diff_fin_wide < 1, 1, null())'  # Getting the sites that are the lowest and basins, within our mask
        )

        # Step 3: Remove Initial Mask
        self.gs.run_command(
            'r.mask'
            ,flags = 'r'
        )

        # Step 4: Sites that are part of the 1/2 mile buffer
        self.gs.run_command(
            'r.mask'    # Could clip (r.clip) the raster too instead
            ,vector = f'{self.vector_map_fname}_half_mi_buffered'
        )

        # Step 5: Filtering on Elevation and Topology that is the highest category
        self.gs.run_command(
            'r.mapcalc'
            ,expression = 'amber_sites_1 = if(pit_basin_filter_wide == 1 && diff_fin_wide < 1, 1, null())'  # Getting the sites that are the lowest and basins, within our mask
        )

        # Step 6: Remove Mask
        self.gs.run_command(
            'r.mask'
            ,flags = 'r'
        )

        # Step 7: Append the Sites
        self.gs.run_command(
            'r.patch'
            ,input = 'amber_sites_0,amber_sites_1'
            ,output = 'amber_sites'
        )

        # Step 8: Grow them to be visible
        self.gs.run_command(
            'r.grow'
            ,input = 'amber_sites'
            ,output = 'amber_sites_grow'
            ,radius = 3
            ,metric = 'euclidean'
            ,overwrite = True 
        )
        if text_file == True:
            ## Step 9: Write files
            self.gs.run_command(
                'r.out.xyz'
                ,input = 'red_sites'
                ,output =f'{self.clean_parent}/red_sites.asc'
            )

            self.gs.run_command(
                'r.out.xyz'
                ,input = 'amber_sites'
                ,output =f'{self.clean_parent}/amber_sites.asc'
            )

            ## Step 10: Proj The Files
            self.gs.run_command(
                'm.proj'
                ,flags='od'
                ,input=f'{self.clean_parent}/amber_sites.asc'
                ,output=f'{self.clean_parent}/amber_sites_proj.asc'
            )

            self.gs.run_command(
                'm.proj'
                ,flags='od'
                ,input=f'{self.clean_parent}/red_sites.asc'
                ,output=f'{self.clean_parent}/red_sites_proj.asc'
            )
            
        if shapefile == True:
            # Making the Raster into a vector file
                self.gs.run_command('r.to.vect'
                                    ,input = 'amber_sites_grow'
                                    ,output = 'amber_sites_grow_vect'
                                    ,type = 'area')
                
                # Writing to Shapefile
                self.gs.run_command('v.out.ogr'
                                    ,input = 'amber_sites_grow_vect'
                                    ,output = f'{Path(__file__).parent.resolve().joinpath('outputs/amber_sites.shp')}'
                                    ,format = 'ESRI_Shapefile'
                                    ,type = 'area')

    def unmarked_graves_pipeline(self,lidar_fname,proj_path, low_memory, historical_file):
        ## Startup the env
        self.setup_grass_env(lidar_fname=lidar_fname
                             ,proj_path=proj_path)
        
        ## Reading Historical Sites
        self.historical_sites_check(historical_file=historical_file)

        ## Checking Elevation
        self.elevation_check()

        ## Topology
        self.topology_check(low_memory=low_memory)

        ## Ranking and Writing
        self.rag_ranking()

        print('The pipeline has run.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unmarked Graves Detection Pipeline")

    ## Adding Args to the Parser
    parser.add_argument("--lidar-file", required=True, help="Path to the LiDAR .las/.laz file")
    parser.add_argument("--proj-path", required=True, help="Path to the GRASS project directory")
    parser.add_argument("--historical-file", required=True, help="Path to the historical sites shapefile/vector file")
    parser.add_argument("--low-memory", action="store_true", help="Enable low memory mode")

    args = parser.parse_args()

    ## Run the pipeline
    ug = UnmarkedGraves()
    ug.unmarked_graves_pipeline(
        lidar_fname= args.lidar_file
        ,proj_path=args.proj_path
        ,low_memory= args.low_memory
        ,historical_file=args.historical_file
    )