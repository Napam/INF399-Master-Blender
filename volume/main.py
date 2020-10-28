import os
import pathlib
import sys
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple
from pprint import pprint

import bpy
import numpy as np

# Add local files ty pythondir in order to import relative files
dir_ = os.path.dirname(bpy.data.filepath)
if dir_ not in sys.path:
    sys.path.append(dir_)
dirpath = pathlib.Path(dir_)

import sqlite3 as db

import blender_config as cng
import blender_utils as utils

import generate as gen
from setup_db import DatabaseMaker


def check_generate_datadir() -> None:
    # If generated data directory does NOT exit
    if not os.path.isdir(cng.GENERATED_DATA_DIR):
        # Create directory
        pathlib.Path(dirpath / cng.GENERATED_DATA_DIR).mkdir(parents=True, exist_ok=True)

        print("DB not found, setting up DB")
        # Setup database
        db_ = DatabaseMaker()
        db_.create_bboxes_cps_table()
        db_.create_bboxes_xyz_table()


def main(n: int, bbox_modes: Sequence[str]) -> None:
    """Main function for generating data with Blender

    Parameters
    ----------
    n : int
        Number of images to render
    bbox_modes : Sequence[str]
        Sequence of modes to save bounding boxes, given as strings. Avilable: xyz cps
    """
    check_generate_datadir()

    scene = gen.Scenemaker()
    gen.create_metadata(scene)
    con = db.connect(str(dirpath / cng.GENERATED_DATA_DIR / cng.BBOX_DB_FILE))
    cursor = con.cursor()

    datavisitor = gen.DatadumpVisitor(bbox_modes=bbox_modes, cursor=cursor)

    maxids = [
        gen.get_max_imgid(cursor, table) for table in (cng.BBOX_DB_TABLE_CPS, cng.BBOX_DB_TABLE_XYZ)
    ]

    maxid = max(maxids)

    if maxid < 0:
        maxid = 0
    else:
        maxid += 1

    imgpath = str(dirpath / cng.GENERATED_DATA_DIR / cng.IMAGE_DIR / cng.IMAGE_NAME)
    commit_interval = 32  # Commit every 32th
    commit_flag: bool = False  # To make Pylance happy
    print(f"\n{'':*^40}\n*{'Rendering initialized':^38}*")
    print(f"*{f'Starting at index: {maxid}':^38}*\n{'':*^40}") # I'm a bit extra sometimes
    for i in range(maxid, maxid + n):
        scene.clear()
        scene.generate_scene(np.random.randint(1, 6))
        utils.render_and_save(imgpath + str(i))

        datavisitor.set_n(i)
        datavisitor.visit(scene)

        # Commit at every 32nd scene
        commit_flag = not i % commit_interval

        if commit_flag:
            con.commit()

    # If loop exited without commiting remaining stuff
    if commit_flag == False:
        con.commit()

    con.close()


def set_attrs_gpucpu(target_device: str) -> None:
    '''target_device can be CUDA or CPU'''
    # YOU NEED TO DO THIS SO THAT BLENDER LOADS AVAILABLE DEVICES!!!
    assert target_device in ('CUDA', 'CPU')

    print('Getting hardware devices:')
    devices = bpy.context.preferences.addons['cycles'].preferences.get_devices()
    pprint(devices)
    try:
        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
        for device in bpy.context.preferences.addons['cycles'].preferences.devices:
            if device.type == target_device:
                print(f'Enabling device: {device}')
                device.use = True
            else:
                device.use = False
    except IndexError as e:
        print('Cycles engine cannot find any devices:')
        print(e)
    
    # Set cycles settings
    if target_device == 'CUDA':
        bpy.context.scene.cycles.device = 'GPU' 
    else:
        bpy.context.scene.cycles.device = 'CPU'


def set_attrs_cycles(samples: int) -> None:
    print('Setting Cycles attributes')
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.aa_samples = samples
    print(f'Cycles will render with {bpy.context.scene.cycles.aa_samples} samples')
    bpy.context.scene.cycles.progressing = "BRANCHED_PATH"


def set_attrs_eevee(samples: int) -> None:
    print('Setting Eevee attributes')
    # EEVEE only works with GPU, no need to explicitly set GPU usage
    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    bpy.context.scene.eevee.taa_render_samples = samples
    print(f'Eevee will render with {bpy.context.scene.eevee.taa_render_samples} samples')


def clear_generated_data():
    print('Clearing generated data')
    import errno, stat, shutil

    def handleRemoveReadonly(func: Callable, path: str, exc):
        try:
            excvalue = exc[1]
            if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
                os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
                func(path)
            else:
                raise exc[1]
        except FileNotFoundError:
            print(f"{cng.GENERATED_DATA_DIR} not found, doing nothing")

    shutil.rmtree(cng.GENERATED_DATA_DIR, ignore_errors=False, onerror=handleRemoveReadonly)


if __name__ == "__main__":
    print(f"{'':*^40}\n*{'FISH GENERATION BABYYY':^38}*\n{'':*^40}\n")

    parser = utils.ArgumentParserForBlender()

    parser.add_argument(
        "n_imgs", help="Number of images to generate", type=int, nargs="?", default=1
    )

    parser.add_argument(
        "-e",
        "--engine",
        help="Specify Blender GPU engine",
        choices=("eevee", "cycles"),
        default=cng.ARGS_DEFAULT_ENGINE,
        const=cng.ARGS_DEFAULT_ENGINE,
        nargs="?",
    )

    parser.add_argument(
        "-c", "--clear", help="Clears generated data before running", action="store_true"
    )

    parser.add_argument(
        "--cpu", help="Force CPU, otherwise will try to enable GPU", action="store_true"
    )

    parser.add_argument("--clear-exit", help="Clears generated data and exits", action="store_true")

    parser.add_argument(
        "-s",
        "--samples",
        help=f"Rendering samples for cycles and eevee, default {cng.ARGS_DEFAULT_RENDER_SAMPLES}",
        type=int,
        nargs="?",
        default=cng.ARGS_DEFAULT_RENDER_SAMPLES,
    )

    parser.add_argument(
        "-b",
        "--bbox",
        help=f"Bounding box type to be stored in SQL database, default: {cng.ARGS_DEFAULT_BBOX_MODE}",
        choices=(cng.BBOX_MODE_CPS, cng.BBOX_MODE_XYZ, "all"),
        default=cng.ARGS_DEFAULT_BBOX_MODE,
        const=cng.ARGS_DEFAULT_BBOX_MODE,
        nargs="?",
    )

    parser.add_argument(
        "-r", "--reference", help="Include reference objects in render", action="store_false"
    )

    args = parser.parse_args()

    if args.clear == True:
        clear_generated_data()

    if args.clear_exit == True:
        clear_generated_data()
        exit()

    if args.cpu == True:
        print('GPU setup disabled, will use CPU')
        set_attrs_gpucpu('CPU')
    else:
        set_attrs_gpucpu('CUDA')

    if args.engine == "cycles":
        set_attrs_cycles(args.samples)
    elif args.engine == "eevee":
        set_attrs_eevee(args.samples)
    else:
        raise ValueError(f"Unsupported render engine specified, got f{args.engine}")

    bbox = None
    if args.bbox == "all":
        bbox = (cng.BBOX_MODE_CPS, cng.BBOX_MODE_XYZ)
    else:
        bbox = (args.bbox,)

    utils.show_reference(hide=args.reference)
    main(args.n_imgs, bbox)
