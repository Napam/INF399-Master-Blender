#!/usr/bin/env bash
DOCKER_FLAGS=""
ARGS=""
USER=$(whoami)
HOSTNAME="BLENDER-CONTAINER"

error() {
        echo "u do sumting wong"
}

while getopts "dpg:u:" option; do
    case $option in
        d) DOCKER_FLAGS+="-d ";;
        g) DOCKER_FLAGS+="--gpus ${OPTARG} ";;
        p) DOCKER_FLAGS+="--publish 5556:8888 ";;
        u) USER=${OPTARG};;
        *) error; exit;;
    esac
done

# $@ is an array or something, start at $OPTIND and rest
ARGS+=${@:$OPTIND}

docker run ${DOCKER_FLAGS} -it --hostname ${HOSTNAME} \
        --user ${USER} \
        -v "$(pwd)/volume":/app \
        --rm --name blender-nam012-cntr nam012-blender ${ARGS}



