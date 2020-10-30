#!/usr/bin/env bash
DOCKER_FLAGS=""
DOCKER_COMMAND=""

error() {
        echo "u do sumting wong"
}

while getopts "dp" option; do
        case $option in
                d) DOCKER_FLAGS+=" -d";;
		p) DOCKER_FLAGS+=" --publish 5556:8888";;
                *) error; exit;;
        esac
done

docker run ${DOCKER_FLAGS} -it -v $(pwd)/volume:/app \
        --ipc=host --rm --gpus all --name blender-nam012-cntr nam012-blender ${DOCKER_COMMAND}



