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
IMAGE_DIR = "images"  # Will be placed in GENERATED_DATA_DIR
IMAGE_NAME = "img"
DEFAULT_FILEFORMAT = "PNG" # This is what you give to Blender, the actual file extension is:
DEFAULT_FILEFORMAT_EXTENSION = ".png" # The actual file extension in file system

"""DATA AND DATABASE"""
BBOX_DB_FILE = "bboxes.db"
BBOX_DB_IMGRNR = "imgnr"  # Column name for image id
BBOX_DB_CLASS = "class_"  # Column name for classes
BBOX_MODE_CPS = "cps"
BBOX_MODE_XYZ = "xyz"
BBOX_DB_TABLE_XYZ = "bboxes_xyz"  # Length width height
BBOX_DB_TABLE_CPS = "bboxes_cps"  # Corner points
FILE_SUFFIX_LEFT = "_L"
FILE_SUFFIX_RIGHT = "_R"

"""CLI"""
ARGS_DEFAULT_ENGINE = "CYCLES"  # [BLENDER_EEVEE, CYCLES]
ARGS_DEFAULT_DEVICE = "CUDA"
ARGS_DEFAULT_RENDER_SAMPLES = 96
ARGS_DEFAULT_BBOX_MODE = "all"  # [BBOX_MODE_CPS, BBOX_MODE_XYZ, 'all']
ARGS_DEFAULT_VIEW_MODE = "stereo"  # [stereo, single]

"""INFO"""
HIGHLIGHT_WIDTH = 70
BOXED_SYMBOL_TOP = "="  # Only single char
BOXED_SYMBOL_BOTTOM = "="  # Only single char
BOXED_SYMBOL_SIDE = "||"  # Can be string
SECTION_SYMBOL = "-"  # Only single char
SECTION_START_STR = ""
SECTION_END_STR = "\n"

