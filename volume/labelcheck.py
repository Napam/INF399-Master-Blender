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
import sqlite3 as db

# Add local files ty pythondir in order to import relative files
dir_ = os.path.dirname(bpy.data.filepath)
if dir_ not in sys.path:
    sys.path.append(dir_)
dirpath = pathlib.Path(dir_)

import config as cng
import utils
import pandas as pd 
from debug import debug, debugs, debugt
from setup_db import DatabaseMaker
import reconstruct as recon
import main as mainfile

reload(utils)
reload(cng)
reload(recon)


@utils.section("Label data directory")
def check_or_create_datadir(directory: str, db_file: str) -> None:
    """Checks and if necessary, sets up directories and sqlite3 database"""
    print(f"Specified directory for reconstructed data:\n\t{directory}")
    # If generated data directory does NOT exit
    if not os.path.isdir(directory):
        # Create directory
        print(f"Directory for generated data {utils.red('not found')}")
        print(f"Creating directory for generated data: {utils.yellow(directory)}")
        pathlib.Path(dirpath / directory).mkdir(parents=True, exist_ok=True)
    else:
        print(f"Found directory for generated data: {utils.yellow(directory)}")

    db_path = os.path.join(directory, db_file)
    if not os.path.isfile(db_path):
        print(f"DB {utils.red('not found')}, setting up DB at {utils.yellow(db_path)}")
        # Setup database
        db_ = DatabaseMaker(db_path)
        db_.create_labelcheck_table()
    else:
        print(f"Found database file: {utils.yellow(db_path)}")


@utils.section("Generated data directory")
def check_generated_datadir(directory: str, db_file: str) -> None:
    """Checks and if necessary, sets up directories and sqlite3 database"""
    print(f"Specified directory for generated data (ground truths):\n\t{directory}")
    # If generated data directory does NOT exit
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"{utils.red('Cannot find')} generated data at '{utils.yellow(directory)}'")
    else:
        print(f"Found directory for generated data: {utils.yellow(directory)}")

    db_path = os.path.join(directory, db_file)
    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"{utils.red('Cannot find')} database at '{utils.yellow(db_path)}'")
    else:
        print(f"Found database file: {utils.yellow(db_path)}")


def renderloop_imgnrs(
    imgnrs: Sequence[int], imgpath: str, wait: bool, view_mode: str, con: db.Connection, cursor: db.Cursor
):

    utils.print_boxed(
        "Output information:",
        f"Imgs to render: {len(imgnrs)}",
        f"Rendering given imgnrs",
        f"Saves images at: {os.path.join(cng.LABELCHECK_DATA_DIR, cng.LABELCHECK_IMAGE_DIR)}",
        f"Sqlite3 DB at: {os.path.join(cng.LABELCHECK_DATA_DIR, cng.LABELCHECK_DB_FILE)}",
    )

    if wait:
        input("Press enter to start rendering\n")

    utils.print_boxed("Rendering initalized")

    commit_flag: bool = False  # To make Pylance happy
    for i, nr in enumerate(imgnrs):
        imgfilepath = imgpath + str(nr)
        print(f"Starting to reacreate imgnr {nr}")
        utils.render_and_save(imgfilepath)
        print(f"Returned from rendering imgnr {nr}")

        try:
            mainfile.assert_image_saved(imgfilepath, view_mode)
        except FileNotFoundError as e:
            print(e)
            print("Breaking render loop")
            commit_flag == False  # Will enable commit after the loop
            break

        # Only commit in intervals
        commit_flag = not i % cng.COMMIT_INTERVAL

        if commit_flag:
            con.commit()

        sql_query = f"INSERT OR REPLACE INTO {cng.LABELCHECK_DB_TABLE} VALUES ({nr})"
        cursor.execute(sql_query)

    # If loop exited without commiting remaining stuff
    if commit_flag == False:
        con.commit()


def renderloop_imgrange(
    imgrange: Tuple[int, int], imgpath: str, wait: bool, view_mode: str, con: db.Connection, cursor: db.Cursor
):
    
    rng = range(*imgrange)

    utils.print_boxed(
        "Output information:",
        f"Imgs to render: {len(rng)}",
        f"Rendering range: {rng}",
        f"Saves images at: {os.path.join(cng.LABELCHECK_DATA_DIR, cng.LABELCHECK_IMAGE_DIR)}",
        f"Sqlite3 DB at: {os.path.join(cng.LABELCHECK_DATA_DIR, cng.LABELCHECK_DB_FILE)}",
    )

    if wait:
        input("Press enter to start rendering\n")

    utils.print_boxed("Rendering initalized")

    commit_flag: bool = False  # To make Pylance happy
    for i, nr in enumerate(rng):
        imgfilepath = imgpath + str(nr)
        print(f"Starting to reacreate imgnr {nr}")
        utils.render_and_save(imgfilepath)
        print(f"Returned from rendering imgnr {nr}")

        try:
            mainfile.assert_image_saved(imgfilepath, view_mode)
        except FileNotFoundError as e:
            print(e)
            print("Breaking render loop")
            commit_flag == False  # Will enable commit after the loop
            break

        # Only commit in intervals
        commit_flag = not i % cng.COMMIT_INTERVAL

        if commit_flag:
            con.commit()

        sql_query = f"INSERT OR REPLACE INTO {cng.LABELCHECK_DB_TABLE} VALUES ({nr})"
        cursor.execute(sql_query)

    # If loop exited without commiting remaining stuff
    if commit_flag == False:
        con.commit()


def renderloop_predfile(predfile: str):
    """Read csv file with predictions, mainly used to compare predictions with true labels

    Parameters
    ----------
    predfile : str
        [description]
    """
    df = pd.read_csv(predfile)
    

def main(
    data_labels_dir: str,
    wait: bool,
    view_mode: str,
    *,
    imgnrs: Optional[Iterable[int]] = None,
    predfile: Optional[str] = None,
    imgrange: Optional[Tuple[int, int]] = None,
):
    n_assert_arg = (imgnrs, predfile, imgrange).count(None)
    if n_assert_arg == 0:
        raise AssertionError(
            "Expected one of ('imgnrs', 'predfile', 'imgrange') to be specified, but got none"
        )
    elif n_assert_arg != 2:
        raise AssertionError(
            "Expected ONLY one of ('imgnrs', 'predfile', 'imgrange') to be specified,"
            f" but got {3-n_assert_arg}"
        )

    check_generated_datadir(data_labels_dir, cng.BBOX_DB_FILE)
    check_or_create_datadir(cng.LABELCHECK_DATA_DIR, cng.LABELCHECK_DB_FILE)
    loader = recon.Sceneloader(data_labels_dir)
    imgpath = str(
        dirpath / cng.LABELCHECK_DATA_DIR / cng.LABELCHECK_IMAGE_DIR / cng.LABELCHECK_IMAGE_NAME
    )
    con = db.connect(str(dirpath / cng.LABELCHECK_DATA_DIR / cng.LABELCHECK_DB_FILE))
    cursor = con.cursor()

    output_info = []

    labeliter: Union[Iterable[int], range]
    if imgnrs:
        # renderloop_imgnrs(imgnrs, imgpath, wait, view_mode, con, cursor)
        labeliter = imgnrs
        output_info.append(f"Rendering given imgnrs")
    elif predfile:
        renderloop_predfile(predfile)
    elif imgrange:
        assert len(imgrange) == 2
        assert isinstance(imgrange[0], int)
        assert isinstance(imgrange[1], int)
        # renderloop_imgrange(imgrange, imgpath, wait, view_mode, con, cursor)
        labeliter = range(imgrange[0], imgrange[1])
        output_info.append(f"Rendering given imgrange: {labeliter}")

    utils.print_boxed(
        "Output information:",
        f"Imgs to render: {len(labeliter)}",
        *output_info,
        f"Saves images at: {os.path.join(cng.LABELCHECK_DATA_DIR, cng.LABELCHECK_IMAGE_DIR)}",
        f"Sqlite3 DB at: {os.path.join(cng.LABELCHECK_DATA_DIR, cng.LABELCHECK_DB_FILE)}",
    )

    if wait:
        input("Press enter to start rendering\n")

    utils.print_boxed("Rendering initalized")

    commit_flag: bool = False  # To make Pylance happy
    for i, nr in enumerate(labeliter):
        print(f"Reacreating imgnr: {nr}")
        loader.clear()
        loader.reconstruct_scene_from_db(nr)
        imgfilepath = imgpath + str(nr)
        print(f"Starting to render imgnr {nr}")
        utils.render_and_save(imgfilepath)
        print(f"Returned from rendering imgnr {nr}")

        try:
            mainfile.assert_image_saved(imgfilepath, view_mode)
        except FileNotFoundError as e:
            print(e)
            print("Breaking render loop")
            commit_flag == False  # Will enable commit after the loop
            break

        # Only commit in intervals
        commit_flag = not i % cng.COMMIT_INTERVAL

        if commit_flag:
            con.commit()

        cursor.execute(f"INSERT OR REPLACE INTO {cng.LABELCHECK_DB_TABLE} VALUES ({nr})")
        print("Progress: ", utils.yellow(f"{i+1} / {len(labeliter)}"))

    # If loop exited without commiting remaining stuff
    if commit_flag == False:
        con.commit()


def set_attrs_directories(labels_dir: str) -> None:
    """
    labels_dir: directory of original labels
    """
    cng.LABELCHECK_DATA_DIR = labels_dir


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

    parser.add_argument(
        "--no-wait",
        help="Dont wait for user input before rendering",
        action="store_false",
    )

    parser.add_argument(
        "--view-mode",
        help=f"Set render mode between leftright (stereo), topside (top and center), center (single), or all (every camera) default: {cng.ARGS_DEFAULT_VIEW_MODE}",
        choices=("leftright", "center", "topcenter", "all"),
        default=cng.ARGS_DEFAULT_VIEW_MODE,
    )

    parser.add_argument(
        "--reference", help="Include reference objects in render", action="store_false"
    )

    parser.add_argument(
        "-e",
        "--engine",
        help="Specify Blender GPU engine",
        choices=("BLENDER_EEVEE", "CYCLES"),
        default=cng.ARGS_DEFAULT_ENGINE,
    )

    parser.add_argument(
        "-s",
        "--samples",
        help=f"Rendering samples for cycles and eevee, default {cng.ARGS_DEFAULT_RENDER_SAMPLES}",
        default=cng.ARGS_DEFAULT_RENDER_SAMPLES,
        type=int,
    )

    parser.add_argument(
        "-d",
        "--device",
        help=f"Specify Blender target hardware, defults: {cng.ARGS_DEFAULT_DEVICE}",
        choices=("CUDA", "CPU"),
        default=cng.ARGS_DEFAULT_DEVICE,
    )

    parser.add_argument("--clear", help="Clears generated data before running", action="store_true")
    parser.add_argument("--clear-exit", help="Clears generated data and exits", action="store_true")

    args = parser.parse_args()
    set_attrs_directories(args.dir)
    mainfile.set_attrs_device(args.device)
    mainfile.set_attrs_engine(args.engine, args.samples)
    mainfile.set_attrs_view(args.view_mode)
    mainfile.show_reference(args.reference)
    mainfile.handle_clear(args.clear, args.clear_exit, args.dir)

    main(
        data_labels_dir=args.labelsdir,
        wait=args.no_wait,
        view_mode=args.view_mode,
        imgnrs=args.imgnrs,
        predfile=args.predfile,
        imgrange=args.imgrange,
    )
