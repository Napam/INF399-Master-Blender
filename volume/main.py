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
    """Checks and if necessary, sets up directories and sqlite3 database """
    # If generated data directory does NOT exit
    if not os.path.isdir(cng.GENERATED_DATA_DIR):
        # Create directory
        pathlib.Path(dirpath / cng.GENERATED_DATA_DIR).mkdir(parents=True, exist_ok=True)

        # TODO: Maybe set another if for checking if .db file exists
        print("DB not found, setting up DB")
        # Setup database
        db_ = DatabaseMaker()
        db_.create_bboxes_cps_table()
        db_.create_bboxes_xyz_table()


def print_boxed(*args: Tuple[str], end="\n"):
    """I'm a bit extra sometimes u know?"""
    print(f"{'':{cng.BOXED_SYMBOL_TOP}^{cng.HIGHLIGHT_WIDTH}}")
    for info in args:
        print(f"{cng.BOXED_SYMBOL_SIDE}{info:^{cng.HIGHLIGHT_WIDTH-4}}{cng.BOXED_SYMBOL_SIDE}")
    print(f"{'':{cng.BOXED_SYMBOL_BOTTOM}^{cng.HIGHLIGHT_WIDTH}}", end=end)


def section(info: str) -> Callable:
    """Decorator that takes in argument for informative text"""

    def section_decorator(f: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            print(f"{f' {info} ':{cng.SECTION_SYMBOL}^{cng.HIGHLIGHT_WIDTH}}")
            print(end=cng.SECTION_START_STR)
            result = f(*args, **kwargs)
            print(end=cng.SECTION_END_STR)
            return result

        return wrapper

    return section_decorator


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

    print_boxed(
        f"Rendering initialized",
        f"Imgs to render: {n}",
        f"Starting at index: {maxid}",
    )

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


@section("Device")
def set_attrs_device(target_device: str) -> None:
    """target_device can be CUDA or CPU"""
    assert target_device in ("CUDA", "CPU")

    print(f"Specified target device {target_device}")

    print("Getting hardware devices:")
    # YOU NEED TO DO THIS SO THAT BLENDER LOADS AVAILABLE DEVICES!!!
    devices = bpy.context.preferences.addons["cycles"].preferences.get_devices()
    pprint(devices)
    try:
        bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
        for device in bpy.context.preferences.addons["cycles"].preferences.devices:
            if device.type == target_device:
                print(f"Enabling device: {device}")
                device.use = True
            else:
                device.use = False
    except IndexError as e:
        print("Cycles engine cannot find any devices:")
        print(e)

    # Set cycles settings
    if target_device == "CUDA":
        bpy.context.scene.cycles.device = "GPU"
    else:
        bpy.context.scene.cycles.device = "CPU"
    print(f"Cycles device is now preemptively set to {bpy.context.scene.cycles.device}")


@section("Engine")
def set_attrs_engine(engine: str, samples: int) -> None:
    assert engine in ("BLENDER_EEVEE", "CYCLES")

    bpy.context.scene.render.engine = engine
    print(f"Render engine is now set to {bpy.context.scene.render.engine}")

    if engine == "CYCLES":
        bpy.context.scene.cycles.progressive = "BRANCHED_PATH"
        bpy.context.scene.cycles.samples = samples  # .samples for PATH tracing, not really used
        bpy.context.scene.cycles.aa_samples = samples  # .aa_samples for BRANCHED_PATH tracing
        print(f"Cycles is set to {bpy.context.scene.cycles.progressive}")
        print(f"Cycles will render with {bpy.context.scene.cycles.aa_samples} samples")
    elif engine == "BLENDER_EEVEE":
        # EEVEE only works with GPU, no need to explicitly set GPU usage
        bpy.context.scene.eevee.taa_render_samples = samples
        print(f"Eevee will render with {bpy.context.scene.eevee.taa_render_samples} samples")


@section("View mode")
def set_attrs_view(mode: str):
    camera = bpy.data.objects["Camera"]
    if mode == "stereo":
        bpy.context.scene.render.use_multiview = True
        bpy.context.scene.render.views["left"].file_suffix = cng.FILE_SUFFIX_LEFT
        bpy.context.scene.render.views["right"].file_suffix = cng.FILE_SUFFIX_RIGHT
        camera.data.stereo.interocular_distance = 1
        camera.data.stereo.pivot = "CENTER"
    elif mode == "single":
        bpy.context.scene.render.use_multiview = False

    print(f"Stereo mode is set to: {bpy.context.scene.render.use_multiview}")
    camera.data.lens_unit = "FOV"
    camera.data.angle = 1.0471975803375244  # 60 degrees in radians
    camera.data.clip_start = 0.0001
    camera.data.clip_end = 1000
    print(f"Camera attributes are set to hardcoded values")


@section("Clear data")
def clear_generated_data():
    print("Clearing generated data")
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
    print_boxed("FISH GENERATION BABYYY", end="\n\n")

    parser = utils.ArgumentParserForBlender()

    parser.add_argument(
        "n_imgs", help="Number of images to generate", type=int, nargs="?", default=1
    )

    parser.add_argument(
        "-e",
        "--engine",
        help="Specify Blender GPU engine",
        choices=("BLENDER_EEVEE", "CYCLES"),
        default=cng.ARGS_DEFAULT_ENGINE,
        const=cng.ARGS_DEFAULT_ENGINE,
        nargs="?",
    )

    parser.add_argument("--clear", help="Clears generated data before running", action="store_true")
    parser.add_argument("--clear-exit", help="Clears generated data and exits", action="store_true")

    parser.add_argument(
        "-d",
        "--device",
        help="Specify Blender target hardware",
        choices=("CUDA", "CPU"),
        default=cng.ARGS_DEFAULT_DEVICE,
        const=cng.ARGS_DEFAULT_DEVICE,
        nargs="?",
    )

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

    parser.add_argument(
        "--view-mode",
        help="Set render mode between stereo or single",
        choices=("stereo", "single"),
        default=cng.ARGS_DEFAULT_VIEW_MODE,
        const=cng.ARGS_DEFAULT_VIEW_MODE,
        nargs="?",
    )

    args = parser.parse_args()

    if args.clear == True:
        clear_generated_data()

    if args.clear_exit == True:
        clear_generated_data()
        exit()

    bbox = None
    if args.bbox == "all":
        bbox = (cng.BBOX_MODE_CPS, cng.BBOX_MODE_XYZ)
    else:
        bbox = (args.bbox,)

    set_attrs_device(args.device)
    set_attrs_engine(args.engine, args.samples)
    set_attrs_view(args.view_mode)

    utils.show_reference(hide=args.reference)
    main(args.n_imgs, bbox)
