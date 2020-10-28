"""
Configuration file for Blender environment

Contains constants that will be used for Blender master project

Written by Naphat Amundsen
"""

import numpy as np

"""generate.py"""
SRC_CLTN = "Fishes"  # Collection of original objects
TRGT_CLTN = "Copies"  # Collection of copies (to be rendered)
REF_CLTN = "Reference"  # Collection of reference item, used to sanity check renders
SPAWNBOX_OBJ = "spawnbox"  # Spawnbox object, representing the spawn area
ROT_MUS = [np.pi / 2, 0, np.pi]
ROT_STDS = [0.5, 1, 1]
DEFAULT_BBOX_MODE = "xyz"  # cps xyz

"""Filesystem"""
GENERATED_DATA_DIR = "generated_data"
# BBOX_FILE = 'bboxes.csv'
IMAGE_DIR = "images"
IMAGE_NAME = "img"
DEFAULT_FILEFORMAT = "PNG"

"""DB"""
BBOX_DB_FILE = "bboxes.db"
BBOX_MODE_CPS = "cps"
BBOX_MODE_XYZ = "xyz"
BBOX_DB_TABLE_XYZ = "bboxes_xyz"  # Length width height
BBOX_DB_TABLE_CPS = "bboxes_cps"  # Corner points

"""CLI"""
ARGS_DEFAULT_ENGINE = "cycles"
ARGS_DEFAULT_RENDER_SAMPLES = 96
ARGS_DEFAULT_BBOX_MODE = "all"
