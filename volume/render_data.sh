#!/usr/bin/env bash
screen -L -Logfile screen.log -S render ./render.sh \
    --device CUDA \
    --engine CYCLES \
    --dir 3d_data \
    --stdbboxcam left \
    --view-mode all \
    10000
