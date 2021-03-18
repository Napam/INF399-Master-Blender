#!/usr/bin/env bash
screen -L -Logfile screen.log -S render ./render.sh \
    --wait \
    --engine CYCLES \
    --dir 3d_data \
    --stdbboxcam left \
    --view-mode all \
    20000