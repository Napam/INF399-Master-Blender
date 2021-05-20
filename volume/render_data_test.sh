#!/usr/bin/env bash
screen -L -Logfile screen.log -S render ./render.sh \
    --device CUDA \
    --engine CYCLES \
    --dir 3d_data_2 \
    --stdbboxcam left \
    --view-mode all \
    10000
