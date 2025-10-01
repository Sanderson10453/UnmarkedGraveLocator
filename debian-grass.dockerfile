# syntax=docker/dockerfile:1
#Debian Image
FROM debian


#Ignore Interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

#Get Dependencies
RUN apt-get update && apt-get install -y \
	python3 \
	python3-pip \
	build-essentials \
	curl \
	vim \
	unzip \
	wget \
	&& apt-get clean

## Add section to install Grass gis
RUN apt install grass \
    grass-dev
# Getting r.in.pdal extension
RUN grass --tmp-location EPSG:4326 --exec g.extension extension=r.in.pdal

## Add section to get conda
RUN mkdir -p ~/miniconda3 \
    && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh \
    && bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3 \
    && rm ~/miniconda3
# See if above remove will remove the whole dir

## Create Conda Env
RUN source ~miniconda3/bin/activate \
    && conda init \
    && bash \
    && conda config --set auto_accept yes
    && conda create -n "lidarvenv" python=3.14.0 \
    && conda deactivate

#Conda Download
RUN conda activate lidarvenv \
    && conda install --channel conda-forge pdal py-pdal \
    && pip install -r requirements.txt


## Setting working dir
WORKDIR /app

## Copying files over
COPY ./app
