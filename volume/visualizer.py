import os
import pathlib
import sys
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import bpy
import numpy as np

# Add local files ty pythondir in order to import relative files
# This is solves a problem that occurs when running code from internal
# Blender code editor
dir_ = os.path.dirname(bpy.data.filepath)
if dir_ not in sys.path:
    sys.path.append(dir_)
dirpath = pathlib.Path(dir_)

import sqlite3 as db

import blender_config as cng
import blender_utils as utils