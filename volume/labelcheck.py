"""
User interface for code used to setup scenes, and extracting labels

Written by Naphat Amundsen
"""
import abc
import os
import pathlib
import random
import sys
import time
from importlib import reload
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import bpy
import numpy as np
import pandas as pd
import sqlite3 as db

# Add local files ty pythondir in order to import relative files
dir_ = os.path.dirname(bpy.data.filepath)
if dir_ not in sys.path:
    sys.path.append(dir_)
dirpath = pathlib.Path(dir_)

import config as cng
import utils
from debug import debug, debugs, debugt
from setup_db import DatabaseMaker
import reconstruct as recon
import main

reload(utils)
reload(cng)
reload(recon)


@utils.section("Data directory")
def check_labelcheck_datadir() -> None:
    """Checks and if necessary, sets up directories and sqlite3 database """
    # If generated data directory does NOT exit
    if not os.path.isdir(cng.LABELCHECK_DATA_DIR):
        # Create directory
        print(f"Directory for label render data not found")
        print(f"Creating directory for label render data: {utils.yellow(cng.LABELCHECK_DATA_DIR)}")
        pathlib.Path(dirpath / cng.LABELCHECK_DATA_DIR).mkdir(parents=True, exist_ok=True)
    else:
        print(f"Found directory for label render data: {utils.yellow(cng.LABELCHECK_DATA_DIR)}")

    db_path = os.path.join(cng.LABELCHECK_DATA_DIR, cng.BBOX_DB_FILE)
    if not os.path.isfile(db_path):
        print(f"DB not found, setting up DB at {utils.yellow(db_path)}")
        # Setup database
        db_ = DatabaseMaker()
        db_.create_labelcheck_table()
    else:
        print(f"Found database file: {utils.yellow(db_path)}")


def main(
    generated_data_dir: str,
    wait: bool,
    view_mode: str,
    *,
    imgnrs: Optional[Sequence[int]] = None,
    predfile: Optional[str] = None,
    imgrange: Optional[Tuple[int, int]] = None,
):
    assert (imgnrs, predfile, imgrange).count(
        None
    ) == 2, "Expected only one of the arguments imgnrs, predfile, imgrange, but got multiple"
    check_labelcheck_datadir()
    loader = recon.Sceneloader(generated_data_dir)
    imgpath = str(dirpath / cng.LABELCHECK_DATA_DIR / cng.IMAGE_DIR / cng.IMAGE_NAME)
    con = db.connect(str(dirpath / cng.GENERATED_DATA_DIR / cng.BBOX_DB_FILE))
    cursor = con.cursor()

    utils.print_boxed(
        "Output information:",
        # f"Imgs to render: {n}",
        f"Saves images at: {os.path.join(cng.GENERATED_DATA_DIR, cng.IMAGE_DIR)}",
        f"Sqlite3 DB at: {os.path.join(cng.GENERATED_DATA_DIR, cng.BBOX_DB_FILE)}",
    )

    if wait:
        input("Press enter to start rendering\n")

    def commit():
        utils.print_boxed(f"Commited to {cng.BBOX_DB_FILE}")
        con.commit()

    utils.print_boxed("Rendering initialized")


if __name__ == "__main__":
    utils.print_boxed(
        "LABEL CHECKER :^)",
        f"Blender version: {bpy.app.version_string}",
        f"Python version: {sys.version.split()[0]}",
        end="\n\n",
    )

    parser = utils.ArgumentParserForBlender()
    parser_imgnrs = parser.add_mutually_exclusive_group(required=True)

    parser_imgnrs.add_argument(
        "--imgnrs",
        help="Image numbers (that is corresponind labels) to be renderd",
        type=int,
        nargs="*",
    )

    parser_imgnrs.add_argument("--imgrange", help="Render images in range", type=int, nargs=2)

    parser_imgnrs.add_argument(
        "--predfile",
        help="Render 'bboxes_full' prediction, can be .csv or .db (sqlite3) file",
        type=str,
        nargs=1,
    )

    parser.add_argument(
        "--labelsdir",
        help=f"Directory generated from the blender generation script {cng.GENERATED_DATA_DIR}",
        type=str,
        nargs=1,
        default=cng.GENERATED_DATA_DIR,
    )

    parser.add_argument(
        "--dir",
        help=f"Specify dir for rendered data, default: {cng.LABELCHECK_DATA_DIR}",
        type=str,
        nargs=1,
        default=cng.LABELCHECK_DATA_DIR,
    )

    parser.add_argument(
        "--no-target-alter",
        help=f"Dont turn label objects green and transparent",
        action="store_false",  # True if option is NOT given
    )

    print(parser.parse_args())