import bpy
import os
import sys
import numpy as np 
from importlib import reload
from tqdm import tqdm 

dir_ = os.path.dirname(bpy.data.filepath)
if not dir_ in sys.path: sys.path.append(dir_)

import setup
import utils 
# Ensures that they update everytime in case of file change
reload(setup)
reload(utils)

def main():
    pass

if __name__ == '__main__': 
    setup.init(globals(), False)
    main()
    