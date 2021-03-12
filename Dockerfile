# FROM ubuntu:focal
FROM nvidia/cuda:11.1-base-ubuntu20.04

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
ENV BLENDER_VERSION 2.83.13
ENV BLENDER_URL https://download.blender.org/release/Blender${BLENDER_MAJOR}/blender-${BLENDER_VERSION}-linux64.tar.xz

WORKDIR ${WORKDIR}

# Download binaries and extract them to BLENDER_DIR
RUN curl -L ${BLENDER_URL} | tar -xJ -C ${BLENDER_DIR}/ && \ 
    mv ${BLENDER_DIR}/blender-${BLENDER_VERSION}-linux64 ${BLENDER_DIR}/blender 

# python binaries will be available as python3.7m
ENV PATH="${PATH}:${BLENDER_DIR}/blender:${BLENDER_DIR}/blender/${BLENDER_MAJOR}/python/bin" 

# pip install stuff
RUN python3.7m -m ensurepip && python3.7m -m pip --no-cache-dir install --upgrade \
	pip \ 
	setuptools \
	wheel \
    pandas

# Remove build dependencies
RUN apt-get -y --purge autoremove \
    curl

# Configure user
ARG user=kanyewest
ARG uid=1000
ARG gid=1000

RUN groupadd -g $gid stud && \
    useradd --shell /bin/bash -u $uid -g $gid $user && \
    usermod -a -G sudo $user && \
    usermod -a -G root $user && \
    passwd -d $user

# Common bash rc
COPY bashrc /etc/bash.bashrc 
# Assert everyone can use bashrc, and remove root home dir so it also uses the bashrc
RUN chmod a+rwx /etc/bash.bashrc && rm -rf /root/

CMD ["/bin/bash"] 
