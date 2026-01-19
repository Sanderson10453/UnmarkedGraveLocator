# syntax=docker/dockerfile:1
# Debian Image
FROM debian


# Ignore Interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Env vars
ENV CONDA_DIR=/opt/conda
ENV PATH=${CONDA_DIR}/envs/lidarvenv/bin:${CONDA_DIR}/bin:${PATH}


# Set Shell to bash
SHELL ["/bin/bash", "-c"]


# Get Dependencies
RUN apt-get update && apt-get install -y \
	python3 \
	python3-pip \
	build-essential \
	curl \
	vim \
	unzip \
	wget \
    grass \
    grass-dev \ 
	&& apt-get clean
    
# Getting r.in.pdal extension
RUN grass --tmp-location EPSG:4326 --exec g.extension extension=r.in.pdal

## Get the libraries from requirements file
# Move the requirements from git repo to docker
COPY ./app/requirements.txt /tmp/

## Add section to get conda
RUN mkdir -p ~/miniconda3 \
    && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -u -p ${CONDA_DIR} \
    && rm /tmp/miniconda.sh

## Create Conda Env and download libraries
RUN conda config --set always_yes true \
    && conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main \
    && conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r \ 
    && conda create -n "lidarvenv" python=3.11.0 \
    && conda install --channel conda-forge pdal \
    && pip install -r /tmp/requirements.txt

## Get the libraries from requirements file
# Move the requirements from git repo to docker
COPY ./app/requirements.txt /tmp/

# Download the requirements 
# RUN ${CONDA_DIR}/envs/lidarvenv/bin/pip install -r /tmp/requirements.txt


## Setting working dir
WORKDIR /app

## Copying files over
COPY /app /app/

## Ensuring the correct shell is used
# Copying Entrypoint script
COPY /conda-entrypoint.sh /usr/local/bin/conda-entrypoint.sh

# Ensuring executable
RUN chmod +x /usr/local/bin/conda-entrypoint.sh

## Entrypoint
ENTRYPOINT [ "/usr/local/bin/conda-entrypoint.sh" ]

## Making it so this container just runs the script
CMD ["python", "unmarked_graves_pipeline.py"]

