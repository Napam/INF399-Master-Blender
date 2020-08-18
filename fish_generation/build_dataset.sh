#!/bin/bash

num_images=1000
max_fish=4
output_dir="./generated_fish_dataset"
python3 code/imagesim.py -n ${num_images} -e ${max_fish} -b data/backgrounds -c data/classes -o ${output_dir}


