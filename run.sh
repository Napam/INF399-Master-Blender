#!/usr/bin/env bash
DOCKER_FLAGS=""
ARGS=""

error() {
        echo "u do sumting wong"
}

while getopts "dpg:" option; do
    case $option in
        d) DOCKER_FLAGS+="-d ";;
        g) DOCKER_FLAGS+="--gpus ${OPTARG} ";;
        p) DOCKER_FLAGS+="--publish 5556:8888 ";;
        *) error; exit;;
    esac
done

# $@ is an array or something, start at $OPTIND and rest
ARGS+=${@:$OPTIND}

docker run ${DOCKER_FLAGS} -it -v $(pwd)/volume:/app \
        --ipc=host --rm --name blender-nam012-cntr nam012-blender ${ARGS}



