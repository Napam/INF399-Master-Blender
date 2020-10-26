#!/usr/bin/env bash
DOCKER_FLAGS=""
DOCKER_COMMAND=""

error() {
        echo "u do sumting wong"
}

while getopts "d" option; do
        case $option in
                d) DOCKER_FLAGS+="-d";;
                *) error; exit;;
        esac
done

docker run ${DOCKER_FLAGS} -it -v $(pwd)/volume:/app -p 5556:8888 \
        --ipc=host --rm --gpus all nam012-blender ${DOCKER_COMMAND}



