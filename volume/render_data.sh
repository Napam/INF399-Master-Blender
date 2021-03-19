#!/usr/bin/env bash
screen -L -Logfile screen.log -S render ./render.sh \
    --wait \
    --device CUDA \
    --engine CYCLES \
    --dir 3d_data \
    --stdbboxcam left \
    --view-mode all \
    20000
