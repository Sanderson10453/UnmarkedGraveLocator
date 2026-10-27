# unmarked-graves
<b> Description: </b> To find unmarked gravesites, the most accurate methods include ground penatrating radar, direct knowledge of a gravesite, and/or someone noticing soft ground underfoot. While these methods high have accuracy,  given the sheer number of unmarked gravesites, thes methods may not be feasible for uncovering large numbers of gravesites. This model aims to serve as an initial sweep - this would need follow-up by ground penetrating radar, group sweeps, or other methods to confirm preliminary findings - of areas suspected of having unmarked gravesites. Through the use of aerial LiDAR, which is readily availble, this model would allow individuals, groups, and researchers to investigate large swaths of land to help improve the speed at which unmarked gravesites are identified.

<b> Note: </b> The current model has a focus on Florida. As more work and contributions to the model are made, we will expand the areas the model works. 

## Model Framework
Previous research has highlighted how the Red-Amber-Green (RAG) method has been used to help with identification of unmarked graves[^1,^2]. With this in mind, our current model builds an index that will be used to inform our RAG prioritization system. This new system will classify areas as Red, Amber, or Green, in respect to liklihood of unmarked graves. In the RAG model, the following is true:
	- <b> Red </b>
	- <b> Amber </b>
	- <b> Green </b>

Within our model, the following components are used to power our index. 

### 1. Historical Relevance
The initial part of the index takes into account a site's proximity to a place of worship or cultural landmark. Our initial model seeks to find, primarily, unmarked African-American gravesites; these sites tend to be  near church/temples/mosques or other places of worship. For this reason, we give the most value to gravesites that are located within a quarter mile (1,320 feet) of a religious site, and those within a half mile (2,640 feet) of a religious site getting the next set of weighting. 

For our list of historical sites, we use data from the Florida Master Site File (FMSF). <b> This dataset requires authorization from Florida Divison of Historical Records (part of the Department of State) - this can be done at this [site](https://dos.fl.gov/historical/preservation/master-site-file/documents-forms/), specifically with this [form](https://dos.fl.gov/media/708884/guide_structure_v50.pdf). Once you've been granted access - you will use the path to the files in the model. If you are having issues/or have privacy issues with accessing the data, please reach out to us! </b>

### 2. Absolute Elevation Difference
The model uses elevation (z-values) from LiDAR .las files to search for areas (with a size estimate of around 4 feet) that are noticeably lower elevation than the areas around it. This works as Florida is, generally, exceptionally flat. After finding these areas, the model delves deeper to ensure that these areas are not just "noise" from the LiDAR file. LiDAR files can be downloaded from the United States Geological Survey [site](https://apps.nationalmap.gov/lidar-explorer/#/)

Once it has identified these lower elevation areas, these areas are considered in the next step of the index.

### 3. Topological Classification
Finally, the current model uses topological classification to further add to the index as to what may be an unmarked gravesite. Again, as this model is based on terrain in Florida - tolerances are coded with reasonably flat terrain in mind. When checking topology, the model looks for areas that are: concave up, as these areas would signify downward sloping due to an unmarked grave underfoots. Research has shown that gravesites over time move from concave down (due to the newly removed soil being packed on the recently buried remains); to flat (as the removed soil starts to pack in); finally, to concave down (as the remains decay and the soil can pack back in)[^3]. 


### Output
Once run, the model will consider the previously mentioned factors to then create a shapefile of areas it believes may fall into the category of Red, high likelihood of an unmarked grave, and Amber, probable likelihood of an unmarked grave. This areas that comprise this shapefile are printed to a text file as X-Y coordinates that can then be further investigated. 


## Setup
<b> This model is currently in Beta mode and will be updated - see changelog </b>
To setup the model, we've found that using a Docker container is the easiest way - more information on Docker can be found [here](https://www.docker.com/get-started). For users who are new to Docker, I recommend using [Docker Desktop](https://www.docker.com/products/docker-desktop/), as its inferace is more user friendly and presents users with prompts.

*This docker container will take ~11Gb of space*

To being with, you will want to clone this git repo - using the following code:

1. You should navigate to the location you want to download the files to:

```
cd /path/to/directory/
```

2. Once in that director, run the following command to clone the repo: 

```
git clone https://gitlab.com/kristophersmith/unmarked-graves.git
```

<b> Note: </b> At this point, it's easiest to move your historical and lidar files to the *app* subdirectory.

3. Once you have the repo cloned and all the files, you will need to navigate into the git repo/directory :
```
cd ./git-repo-dir
```

4. Now, you will build the docker image :
```
docker build -t unmarked-graves -f ./debian-grass.dockerfile .
```

5. Run the unmarked graves script in the image
if on a windows: 
```
docker run -v "/path/to/where/you/want/outputs":"/app/output" unmarked-graves^
		 python ./unmarked_graves_pipeline.py --lidar-file "./test-cases/name-of-your-lidar-file.las"^
		  --historical-file "./test-cases/name-of-historical-file.shp^
		  --proj-path "project-name"
```
if on a mac/linux:
```
docker run -v "/path/to/where/you/want/outputs":"/app/output" unmarked-graves \
		 python ./unmarked_graves_pipeline.py --lidar-file "./test-cases/name-of-your-lidar-file.las" \
		  --historical-file "./test-cases/Duval_sites.shp \
		  --proj-path "unmarked-graves"
```

For example:
```
docker run -v "C:\users\spenser\Documents\unmarked":"/app/output" unmarked-graves^
		 python ./unmarked_graves_pipeline.py --lidar-file "./test-cases/USGS_LPC_FL_Peninsular_FDEM_2018_D19_DRRA_LID2019_218755_E.las"^
		  --historical-file "./test-cases/name-of-historical-file.shp^
		  --proj-path "project-name"

```
<b> Note: </b> Linux/Mac users may have to add sudo in front of docker commands

## Results
After running these commands, you should find two output text files - red_sites.asc and amber_sites.asc. These contain coordinates to the points of interest.


## License
MIT Licensed


[^1]: Geomorphological and geoforensic interpretation of maps, aerial imagery, conditions of diggability and the colour-coded RAG prioritization system in searches for criminal burials, Laurance Donnelly; Mark Harrison, 2013

[^2]: A GIS-based Quantitative Approach for the Search of Clandestine Graves, Italy , Roberta Somma, Maria Cascio, et. al. 2017

[^3]: Locating and characterizing burials using 3D ground-penetrating radar (GPR) and terrestrial laser scanning (TLS) at the historic Mueschke Cemetery, Houston, Texas
