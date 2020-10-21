'''
Configuration file for Blender environment

Contains constants that will be used for Blender master project

Written by Naphat Amundsen
'''

import numpy as np 

'''generate.py'''
SRC_CLTN = 'Fishes'
TRGT_CLTN = 'Copies'
SPAWNBOX = 'spawnbox'
ROT_MUS = [np.pi/2, 0, np.pi]
ROT_STDS = [0.5, 1, 1]
DEFAULT_BBOX_MODE = 'lwh'

'''Filesystem'''
GENERATED_DATA_DIR = 'generated_data'
# BBOX_FILE = 'bboxes.csv'
IMAGE_DIR = 'images'
IMAGE_NAME = 'img'

'''DB'''
BBOX_DB_FILE = 'bboxes.db'
# BBOX_DB_TABLE = 'bboxes' # Compatibility during dev
BBOX_DB_TABLE_XYZ = 'bboxes_xyz' # Length width height
BBOX_DB_TABLE_CPS = 'bboxes_cps' # Corner points
DEFAULT_BBOX_MODE = 'cps'
DEFAULT_DB_TABLE = BBOX_DB_TABLE_CPS


