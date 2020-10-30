# FROM ubuntu:focal
FROM nvidia/cuda:10.1-devel-ubuntu18.04

# apt install stuff
RUN apt-get update && apt-get install -y \
	curl \
	libfreetype6 \
	libglu1-mesa \
	libxi6 \
	libxrender1 \
	screen \ 
	sqlite3 \
	xz-utils \
     && apt-get -y autoremove && rm -rf /var/lib/apt/lists/*

ENV WORKDIR /app
ENV BLENDER_DIR /usr/local
ENV BLENDER_MAJOR 2.83
ENV BLENDER_VERSION 2.83.7
ENV BLENDER_URL https://download.blender.org/release/Blender${BLENDER_MAJOR}/blender-${BLENDER_VERSION}-linux64.tar.xz

WORKDIR ${WORKDIR}

# Download binaries and extract them to BLENDER_DIR
RUN curl -L ${BLENDER_URL} | tar -xJ -C ${BLENDER_DIR}/ && \ 
    mv ${BLENDER_DIR}/blender-${BLENDER_VERSION}-linux64 ${BLENDER_DIR}/blender 

# python binaries will be available as python3.7m
ENV PATH="${PATH}:${BLENDER_DIR}/blender:${BLENDER_DIR}/blender/${BLENDER_MAJOR}/python/bin" 

# pip install stuff
#RUN python3.7m -m ensureipip && python3.7m -m pip install --upgrade \
#	pip \ 
#	setuptools \
#	wheel 

CMD ["/bin/bash"] 
