#########################################################
### Author: Spenser
### Date: 17 Dec 2025
### Description: Attempting to get Grass GIS to work
###                 as a standalone

#########################################################

## Import Libraries
import argparse
import os
import subprocess
import sys
from pathlib import Path

# Geospatial
import laspy
from pyproj import CRS

## Creating Classes

# Getting grass python
class GrassConfigs:
    _grass_py_path = None

    @classmethod
    def get_grass_path(cls) -> str:
        if cls._grass_py_path is not None:
            return cls._grass_py_path
        
        try:
            # If Linux or Mac
            if os.name == 'posix':
                cls._grass_py_path = subprocess.check_output(["grass", "--config", "python_path"], text = True).strip()

            # If Windows
            elif os.name == 'nt':
                grass_cmd = [r'C:\\Program Files\\GRASS GIS 8.4\\grass84.bat', "--config", "python_path"] 
                cls._grass_py_path = subprocess.check_output(grass_cmd, text = True, shell = True).strip()
            
            # BCD or Something else
            else:
                raise OSError(f"Unsupported OS - Put a ticket in for dev: {os.name}")
            
        except FileNotFoundError as e:
            raise EnvironmentError("Do you have Grass GIS Installed? Is it on your PATH?") from e
        
        return cls._grass_py_path


class UnmarkedGraves(GrassConfigs):
    """
    This class contains all the methods, and essentially the pipeline, to help highlight areas 
        where there may be unmarked graves. To start, when instantiation the class - add your lidar (.las) as a parameter.
       This will allow all the methods to be able to access this same file     
    
    """
    def __init__(self):
        
        ## Declaring Attributes
        self.fname = None
        self.project_path = Path()
        self.lidar_file = Path()
        self.vector_map_fname = None

        # Ensuring Grass is Initialized
        self._grass_initialized = False


    def setup_grass_env(self
                        ,project_path : Path|str
                        ,lidar_file : Path|str
                        ):
        """
        This method will start the grass script environment and check if the specified project/location exist.
        
        Parameters
        -----------
            project_path : str, Path
                The path where you want to create/have created the grass gis project
            lidar_file: str, Path
                The path of your lidar .las file that will be used for the model

        """
        if self._grass_initialized:
            return
        
        # For Testing
        if project_path:
            self.project_path = Path(project_path)

        if lidar_file:
            self.lidar_file = Path(lidar_file)

        # Updating Attributes
        self.dbase = self.project_path.parent
        
        # Appending python path
        sys.path.append(GrassConfigs.get_grass_path())



        ## Import GRASS Python bindings
        import grass.jupyter as gj
        import grass.script as gs
        import grass.script.setup as gsetup

        # Ensuring other Modules have access 
        self.gs = gs
        self.gj = gj 

        # Grabbing ESPG from laspy file
        self.las_espg = CRS.from_wkt(str(laspy.read(self.lidar_file).header.parse_crs())).sub_crs_list[0].to_epsg()
        

        ## Checking if Project & Mapset has been created
        if not self.project_path.exists():

            # Does the Database directory exist?
            if not self.project_path.parent.exists():
                print(f"Creating database directory: {self.project_path.parent}")
                self.project_path.parent.mkdir(parents = True, exist_ok = True)

            # Checking if the database exists - if not, create location and project
            # If Linux
            if os.name == 'posix':
                # Creating Database and Perm. location
                subprocess.run(["grass", "-c", f"epsg:{self.las_espg}", "-e", f"{self.project_path}"], check = True)

            # If Windows
            elif os.name == 'nt':
                 # Creating Database and Perm. location
                grass_exe = r'C:\Program Files\GRASS GIS 8.4\grass84.bat'
                grass_perm = (f'"{grass_exe}" -c epsg:{self.las_espg} -e "{self.project_path}"')
                subprocess.run(grass_perm, check = True, shell = True, timeout= 300)

            # Checking the session is running
            # gsetup.init(self.dbase, self.project_path.name, 'UnmarkedGravesSearch')
            gj.init(self.project_path)
            self._grass_initialized = True
            
        else: 
            # Checking the session is running
            gj.init(Path(self.project_path))
            self._grass_initialized = True

    def _list_maps(self):

        ## Parsing
        map_dict = self.gs.parse_command('g.list', type ='all')
        map_ls = list(map_dict.keys())
        return map_ls

    def historical_sites_check(self
                               ,historical_file: str|Path
                               ,overwrite = False
                               ):
        """
        This method will be the pipeline component for the first component of our RAG model - whether there is a historic site
        within a set distance of the site. Sites within a quarter mile of a church will be most rewarded, while sites
        that are within a half mile will still receive some points.

        To do so, it does the following steps:
        1. Uses the Florida Master Site Files (unless another file is provided) church and cultural sites
        2. Draws a circular buffer around the sites
        3. Then later checks if our points of interest are within these buffers.

        Parameters
        -----------
            historical file : Str, Path 
                a shapefile that contains historical sites. If let blank, it will use the FMSF
                data by default. 
            
            overwrite : bool, default = False
                By default this method will not overwrite the already existing buffers; however, if set to True,
                        it will overwrite the buffers. This is not suggested unless you are planning on using a new file.
        
        """  
        ## Testing 
        self.historical_file = Path(historical_file)
        ## Attributes
        existance = True   # Assuming vector map does not exist

        if not overwrite:
            'check if buffer exists'

            # If it exists and overwrite is False, then skip running this
            existance = False   

        if existance == False or overwrite == True:
            # Importing
            self.gs.run_command(
                    'v.import'
                    ,input = self.historical_file
                            )

            ## Adding the Buffer
            # Gettng Vector Map Name
            self.vector_map_fname = self.historical_file.stem

            # Running the command
            self.gs.run_command(
                            'v.buffer'
                            ,input = self.vector_map_fname
                            ,output = f'{self.vector_map_fname}_quart_mi_buffered'
                            ,where = '1=1'
                            ,distance = '1320'  # 1/4 mi
            )

            self.gs.run_command(
                            'v.buffer'
                            ,input = self.vector_map_fname
                            ,output = f'{self.vector_map_fname}_half_mi_buffered'
                            ,where = '1=1'
                            ,distance = '2640'  # 1/2 mi
            )


            print(f'Historical Site Buffer is complete. Find it in Grass GIS under file name \n {self.vector_map_fname}_*_buffered ')

    def _filter_ground_returns(self, output_suffix = '_grnd'):
        """
        This method filters LiDAR files, using lapsy, to return ground returns only.
        It creates a temporary .las file that the pipeline will use

        Returns
        ----------
            Path to filtered temporary .las file
        """

        # Read the file
        las_data = laspy.read(self.lidar_file)

        ## Creating the masks to filter the las file
        ground_mask = las_data.classification == 2
        building_mask = las_data.classification == 6

        ## Writing the new temporary file
        ground_las = laspy.LasData(header = las_data.header)
        ground_las.points = las_data.points[ground_mask]

        # Writing
        filt_fname = (self.lidar_file.parent).joinpath(f'{self.lidar_file.stem}{output_suffix}.las')

        # Ensuring directory exists
        # Making temp directory
        self.temp_dir = Path(self.gs.tempdir())
        # filt_fname.parent.mkdir(parents = True, exist_ok = True)
        ground_las.write(self.temp_dir.joinpath(f'{self.lidar_file.stem}{output_suffix}.las'))

        return filt_fname, building_mask, las_data


    def elevation_check(self
                        ,denoise = True
                        ,low_memory = True
                        ,overwrite = False
                        ,filter_buildings = True
                        ):        
        """
        This method will be the pipeline component for the next component of our RAG model - does an area have lower elevation than the areas 
            around it?

        
        Parameters
        ---------            
            denoise : bool, default True
                If True, will use the neighbors to normalize the lidar data
            overwrite : bool, Default False
                If true, will overwrite previous elevation layers of the same name
            filter_buildings : bool Default True
                If True, will remove LiDAR data with a class of 6 during the import

        Notes
        -----
            On approaches
            1. Use r.stats/quantiles to create quantiles
                - Filter cells that fall below this value?
            2. Check if there's a way to use r.volume to calculate average elev by clumps?
        
        """

        # File Name without Ext
        self.clean_fname = (self.lidar_file.stem)[-15:]
        self.clean_path = (self.lidar_file.stem)[-15:]
        self.clean_parent = Path(self.lidar_file).parent.joinpath('output').resolve()

        # If Filtering for buildings
        if filter_buildings:
            lidar_input, building_mask, las_data = self._filter_ground_returns()
        else:
            lidar_input = self.lidar_file


        ## Creating list of maps in mapset
        map_ls = self._list_maps()

        ## Elevation Testing
        ## Setting the region
        extent = self.gs.read_command(
            "r.in.pdal"
            ,flags ='sg'
            ,input = lidar_input
            ,overwrite = True
            ,output = self.clean_fname[-15:]
        )

        # Create Extent
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


        ## Reading the las
        self.gs.run_command(
            "r.in.pdal"
            ,input = lidar_input
            ,method = 'mean'
            ,overwrite = True
            ,resolution = 1
            ,output = f'{self.clean_fname}_mean'
        )

        ## Filtering out buildings and creating buffer
        if filter_buildings:

            # Creating the building lidar file
            building_las_data = laspy.LasData(header = las_data.header)
            building_las_data.points = las_data.points[building_mask]
            # building_fname = Path(self.clean_parent).joinpath('bulding_tmp.las')

            # Ensuring directory exists
            # Using temp dir
            building_fname = self.temp_dir.joinpath('bulding_tmp.las')
            # building_fname.parent.mkdir(parents = True, exist_ok = True)
            building_las_data.write(building_fname)

            # Reading the building file to create the raster buffer
            self.gs.run_command(
                'r.in.pdal'
                ,input = building_fname
                ,output = 'buildings_tmp'
                ,method = 'n'
                ,resolution = 1
                ,overwrite = True
                                )
            # Creating the mask
            self.gs.run_command(
                'r.mapcalc'
                ,expression = 'buildings_mask_tmp = if(buildings_tmp > 0, 1, null())'
                ,overwrite = True
                                )
            # Expanding the mask a bit
            self.gs.run_command(
                'r.grow'
                ,input = 'buildings_mask_tmp' 
                ,output = 'buildings_buffered'
                ,radius = 3
                ,metric = 'euclidean'
                ,overwrite = True
                                )
            
        ## Writing Neighborhood Models to Compare Elev
        ## Minimum Output
        self.gs.run_command(
            'r.neighbors'
            ,input=f'{self.clean_fname}_mean'
            ,output = f'{self.clean_fname}_mean_neighbor'
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
            ,expression = f"diff = {self.clean_fname}_mean - {self.clean_fname}_mean_neighbor"
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
        if low_memory:

            # Dropping files ending in temp
            self.gs.run_command(
                'g.remove'
                ,flags = 'f'
                ,type = 'raster'
                ,pattern = '*_tmp'
            )


            # Dropping Dif
            self.gs.run_command(
                'g.remove'
                ,flags = 'f'
                ,type = 'raster'
                ,pattern = 'diff*'
                ,exclude = '*wide'
            )

            # Dropping Temp Building Files
            lidar_input.unlink(missing_ok = True)
            building_fname.unlink(missing_ok = True)

        ## Getting rid of the temp file from laspy
        self.gs.try_rmdir(self.temp_dir)
    
    def topology_check(self, low_memory = False):
        """
        This method will be the pipeline component for the last component of our RAG model - whether the slope/geomorphology is sloped downward,
            but flat enough to be conducive for a grave.

        The method will use the input from the Lidar class previously made. No added parameters are needed unless there's a separate file you would like to use.
        
        
        Parameters
        ---------            
            low_memory : bool, default True
                Will delete the intermediate map files created while creating the filter. Set to False, they will be preserved
        
        """

        ## Setting the region
        extent = self.gs.read_command(
            "r.in.pdal"
            ,flags ='sg'
            ,input = self.lidar_file
            ,overwrite = True
            ,output = self.clean_fname[-15:]
        )

        # Create Extent
        extent_dict = {}
        extent_split = extent.split()
        for ext_str in extent_split:
            k,v = ext_str.split('=')
            extent_dict[k] = float(v)


        self.gs.run_command(
            'g.region'
            ,n = extent_dict['n']
            ,s = extent_dict['s']
            ,w = extent_dict['w']
            ,e = extent_dict['e']
            ,t = extent_dict['t']
            ,b = extent_dict['b']
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
            ,input = 'pit_basin_filter'
            ,output = 'pit_basin_filter_wide'
            ,method = 'maximum'
            ,size = 5
            ,overwrite = True
    )

        if low_memory:
            self.gs.run_command(
                'g.remove'
                ,flags = 'f'
                ,type = 'raster'
                ,pattern = '*_?????'
                ,exclude = '*wide'
            )

            self.gs.run_command(
                'g.remove'
                ,flags = 'f'
                ,type = 'raster'
                ,pattern = 'pit_basin*'
                ,exclude = '*wide'
            )


    def rag_ranking(self, low_memory = True, shapefile = False, text_file = True):
        """
        This is the final method to group the areas into 3 categories:
            1. Red, where we believe there are potential unmarked graves
            2. Amber, where we think there may be unmarked graves
            3. Green, areas we do not think there are unmarked graves

        Parameters
        --------- 
         low_memory : bool, default True
            Will delete the intermediate map files created while creating the filter. Set to False, they will be preserved
        """
        # Guardrail for missing historical map
        if self.vector_map_fname is None:
            print("Missing Vector Map")
 
        ### Create Index of Places that meet highest criteria
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
        if shapefile:

            # Making the Raster into a vector file
            self.gs.run_command('r.to.vect'
                                ,input = 'red_sites_grow'
                                ,output = 'red_sites_grow_vect'
                                ,type = 'area')
            
            # Writing to Shapefile
            self.gs.run_command('v.out.ogr'
                                ,input = 'red_sites_grow_vect'
                                ,output = f"{self.clean_parent.joinpath('red_sites.shp')}"
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
        if text_file:
            ## Step 9: Write files
            self.gs.run_command(
                'r.out.xyz'
                ,input = 'red_sites'
                ,output = f"{self.clean_parent.joinpath('red_sites.asc')}"
            )

            self.gs.run_command(
                'r.out.xyz'
                ,input = 'amber_sites'
                ,output = f"{self.clean_parent.joinpath('amber_sites.asc')}"
            )


            ## Step 10: Proj The Files
            self.gs.run_command(
                'm.proj'
                ,flags = 'od'
                ,input = f"{self.clean_parent.joinpath('amber_sites.asc')}"
                ,output = f"{self.clean_parent.joinpath('amber_sites_proj.asc')}"
            )

            self.gs.run_command(
                'm.proj'
                ,flags = 'od'
                ,input = f"{self.clean_parent.joinpath('red_sites.asc')}"
                ,output = f"{self.clean_parent.joinpath('red_sites_proj.asc')}"
            )
            
        if shapefile:
            # Making the Raster into a vector file
            self.gs.run_command(
                'r.to.vect'
                ,input = 'amber_sites_grow'
                ,output = 'amber_sites_grow_vect'
                ,type = 'area'
                                )
            
            # Writing to Shapefile
            self.gs.run_command(
                'v.out.ogr'
                ,input = 'amber_sites_grow_vect'
                ,output = f"{self.clean_parent.joinpath('amber_sites.shp')}"
                ,format = 'ESRI_Shapefile'
                ,type = 'area'
                )
        if low_memory:
            self.gs.run_command(
                'g.remove'
                ,flags = 'f'
                ,type = 'raster'
                ,pattern = '*sites*'
                ,exclude = '*_grow'
            )

    def unmarked_graves_pipeline(self,lidar_fname,proj_path, low_memory, historical_file = None):

        # Save Args
        self.lidar_file = Path(lidar_fname)
        self.project_path = Path(proj_path)
        self.historical_file = Path(historical_file) if historical_file else None
        self.low_memory = low_memory

        ## Startup the env
        self.setup_grass_env()
        
        ## Reading Historical Sites
        if historical_file:
            self.historical_sites_check()
        else:
            print("You forgot to include the historical file - the pipeline will continue without it. \n Please get access to the Site Master File")

        ## Checking Elevation
        self.elevation_check()

        ## Topology
        self.topology_check()

        ## Ranking and Writing
        self.rag_ranking()

        print('The pipeline has run.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Unmarked Graves Detection Pipeline")

    ## Adding Args to the Parser
    parser.add_argument("--lidar-file", required = True, help = "Path to the LiDAR .las file")
    parser.add_argument("--proj-path", required = True, help = "Path to the GRASS project directory")
    parser.add_argument("--historical-file", required = False, help = "Path to the historical sites shapefile/vector file")
    parser.add_argument("--low-memory", action = "store_true", help = "Enable low memory mode")
    # parser.add_argument("--shapefile", action="store_false", help="Path to the LiDAR .las file")

    args = parser.parse_args()

    ## Run the pipeline
    ug = UnmarkedGraves()
    ug.unmarked_graves_pipeline(
        lidar_fname = args.lidar_file
        ,proj_path = args.proj_path
        ,low_memory = args.low_memory
        ,historical_file = args.historical_file
        # ,shapefile=args.shapefile
    )