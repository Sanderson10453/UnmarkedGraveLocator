# unmarked-graves
<b> Description: </b> Current methods to find unmarked gravesites require being on the ground and often take lots of time and energy - these methods include ground penatrating radar, word of mouth, and/or noticing soft ground underfoot. Given how many unmarked gravesites may exist, these methods for an initial sweep of areas is unfeasible. We're working on a model that allows the use of various aerial and satelite imagery to highlight areas that may contain unmarked graves. This model would be able to investigate large swaths of land to help improve the speed at which unmarked gravesites are identified.

## Model Framework
Previous research has highlighted how the Red-Amber-Green (RAG) method can help with identification of unmarked graves [^1]. With this in mind, we're updating our current model - based primarily on statistically lower elevation - to include an index that will be used to inform our RAG prioritization system. This new system will classify areas as Red, Amber, or Green, in respect to liklihood of unmarked graves.

### 1. Absolute Elevation Difference
Our current model is built around finding sites within a LiDAR cloud that have a ground elevation that is statistically lower than other points. Given how flat Florida is, this will find sites that could be burial sites.


### 2. Geomorphon Classification
The next part of the model - geomorphon classification -  aims to further filter sites beyond just elevation. Through geomorphon classifying LiDAR clouds, we can classify our areas into the most common landforms:
	
	- Peak 
	- ridge
	- shoulder
	- spur
	- slope
	- hollow
	- footslope
	- valley
	- pit
	- and, flat 

For our sake, we are interested in identifying places that are slopes. 

### 3. Historical Relevance
The final part of the index takes into account a site's proximity to a place of worship or cultural landmark. Generally speaking, people are buried near church/temples/mosques or other places of worship - sites within 100 yards of a place of worhsip or cultural landmark will receive weight in our index.


## Config Steps (Tested on EC2 : unmarked-graves-fl)
1. Download Grass GIS
	- sudo apt install grass grass-dev
		- has a y/n 
2. Once downloaded, be sure to install the r.in.pdal extension
	- grass --tmp-location EPSG:4326 --exec g.extension extension=r.in.pdal
3. Download Conda
	- mkdir -p ~/miniconda3
	- wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
	- bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
	- rm ~/miniconda3/miniconda.sh
4. Create Conda Environment
	- source ~/miniconda3/bin/activate
	- conda init
	- Refresh the shell (figure out)
	- conda create -n "lidarvenv" python=3.14.0
		Ask for TOS
		- (A)ccept/(R)eject/(V)iew
		- (A)ccept/(R)eject/(V)iew, again
		- Proceed Y/N
	- Figure out how to have conda auto accept terms and conditions
		- https://www.anaconda.com/docs/getting-started/tos-plugin
		- https://stackoverflow.com/questions/56100217/how-to-accept-the-license-agreement-when-building-rti-connext-dds-5-3-1-with-doc?noredirect=1
5. Ensure pip is installed
	- conda deactivate
	- sudo apt update
	- sudo apt upgrade
	- sudo apt install python3-pip
6. Install packages into conda environment
	- conda activate lidarvenv
	- conda install conda-forge::pdal py-pdal
	- pip install -r requirements.txt	(Havent done in EC2)
7. Activate the conda environment and run the grass gis standalone script
8. r.denoise
	- Requires mdenoise
	- On windows, needs g++
	- Might need to download MSYS2
	- Need toolkit
		- pacman -S --needed base-devel mingw-w64-x86_64-toolchain


## License
MIT Licensed


[^1]: Geomorphological and geoforensic interpretation of maps, aerial imagery, conditions of diggability and the colour-coded RAG prioritization system in searches for criminal burials, Laurance Donnelly; Mark Harrison, 2013