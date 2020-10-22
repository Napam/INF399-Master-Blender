import os
import pathlib
import sys
from importlib import reload
from typing import Any, Dict, Iterable, List, Optional, Tuple


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
from setup_db import DatabaseMaker


def check_generate_datadir() -> None:
    # If generated data directory does NOT exit
    if not os.path.isdir(cng.GENERATED_DATA_DIR):
        # Create directory
        pathlib.Path(dirpath / cng.GENERATED_DATA_DIR).mkdir(parents=True, exist_ok=True)

        # Setup database
        db_ = DatabaseMaker()
        db_.create_bboxes_cps_table()
        db_.create_bboxes_xyz_table()


def main(n: int) -> None:
    check_generate_datadir()

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
    if maxid is None:
        maxid = 0
    else:
        assert isinstance(maxid, int)
        maxid += 1

    print("Starting at index:", maxid)
    imgpath = str(dirpath / cng.GENERATED_DATA_DIR / cng.IMAGE_DIR / cng.IMAGE_NAME)

    commitinterval = 32  # Commit every 32th

    for i in range(maxid, maxid + n):
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

def set_attrs_cycles(samples: int) -> None:
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.device = "GPU"
    bpy.context.scene.cycles.aa_samples = samples
    bpy.context.scene.cycles.progressing = "BRANCHED_PATH"

def set_attrs_eevee(samples: int) -> None:
    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    bpy.context.scene.eevee.taa_render_samples = args.samples

if __name__ == "__main__":
    parser = utils.ArgumentParserForBlender()

    parser.add_argument("n_imgs", help="Number of images to generate", type=int, nargs="?", default=1)

    parser.add_argument(
        "-e", "--engine", help="Specify Blender GPU engine", choices=["eevee", "cycles"]
    )

    parser.add_argument(
        "-c", "--clear", help="Clears generated data before running", action="store_true"
    )

    parser.add_argument(
        "-s",
        "--samples",
        help="Rendering samples for cycles and eevee",
        type=int,
        nargs="?",
        default=96,
    )

    args = parser.parse_args()

    if args.clear == True:
        import shutil
        shutil.rmtree(cng.GENERATED_DATA_DIR, ignore_errors=True)

    if args.engine is not None:
        # Set GPU settings
        if args.engine == "cycles":
            set_attrs_cycles(args.samples)
        elif args.engine == "eevee":
            set_attrs_eevee(args.samples)
        else:
            raise ValueError(f"Unsupported cycles engine specified, got f{args.engine}")
    else:
        set_attrs_eevee(args.samples)

    main(args.n_imgs)
