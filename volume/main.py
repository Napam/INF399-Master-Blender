import os
import pathlib
import sys
from importlib import reload
from typing import Dict, List, Optional, Tuple
import argparse

import bpy
import numpy as np

# Add local files ty pythondir in order to import relative files
dir_ = os.path.dirname(bpy.data.filepath)
if dir_ not in sys.path:
    sys.path.append(dir_)
dirpath = pathlib.Path(dir_)

import sqlite3 as db

import blender_config as cng
import blender_setup as setup
import blender_utils as utils

import generate as gen

def main() -> None:
    # Set GPU settings
    # bpy.context.scene.render.engine = 'CYCLES'
    # bpy.context.scene.cycles.device = 'GPU'
    # bpy.context.scene.cycles.aa_samples = 128

    scene = gen.Scenemaker()
    con = db.connect(str(dirpath / cng.GENERATED_DATA_DIR / cng.BBOX_DB_FILE))
    cursor = con.cursor()
    bbox_mode = "xyz"
    datavisitor = gen.DatadumpVisitor(
        cursor=cursor,
        bbox_mode=bbox_mode,
    )
    datavisitor.create_metadata(scene)
    maxid = gen.get_max_imgid(
        cursor, cng.BBOX_DB_TABLE_CPS if bbox_mode == "cps" else cng.BBOX_DB_TABLE_XYZ
    )

    # If not start at zero, then must increment +1
    # Else just start at zero since want to start
    # counting at zero
    if maxid != 0:
        maxid += 1

    print("Starting at index:", maxid)
    imgpath = str(dirpath / cng.GENERATED_DATA_DIR / cng.IMAGE_DIR / cng.IMAGE_NAME)

    commitinterval = 32  # Commit every 32th

    n_data = 10
    for i in range(maxid, maxid + n_data):
        scene.clear()
        n = np.random.randint(1, 6)
        scene.generate_scene(n)
        utils.render_and_save(imgpath + str(i))
        # scene.save_labels_sqlite(i, cursor=cursor)
        datavisitor.set_n(i)
        datavisitor.visit(scene)

        # Commit at every 32nd scene
        commit_flag = i % commitinterval == 0

        if commit_flag:
            con.commit()

    # If loop exited without commiting remaining stuff
    if not commit_flag:
        con.commit()

    con.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'n',
        help='Number of images to generate',
        type=int,
        nargs='?',
        default=1
    )

    parser.add_argument(
        '-e', '--engine', 
        help="Specify Blender GPU engine", 
        choices=['eevee', 'cycles']
    )

    parser.add_argument(
        '-c', '--clear',
        help='Clears generated data',
        action='store_true'
    )

    args = parser.parse_args()

    if args.clear == False:
        pass
    if args.engine is not None:
        pass

    main()







