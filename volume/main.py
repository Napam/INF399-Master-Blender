"""
Main python file to control Blender application

Written by Naphat Amundsen
"""

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

import generate as gen
from setup_db import DatabaseMaker
import functools


def print_boxed(*args: Tuple[str], end="\n") -> None:
    """
    Encloses strings in a big box for extra visibility

    I'm a bit extra sometimes u know?
    """

    width = max(max(map(len, args)) + 2 * len(cng.BOXED_STR_SIDE) + 2, cng.HIGHLIGHT_MIN_WIDTH)

    print(f"{'':{cng.BOXED_SYMBOL_TOP}^{width}}")
    for info in args:
        print(f"{cng.BOXED_STR_SIDE}{info:^{width-2*len(cng.BOXED_STR_SIDE)}}{cng.BOXED_STR_SIDE}")
    print(f"{'':{cng.BOXED_SYMBOL_BOTTOM}^{width}}", end=end)


def section(info: str) -> Callable:
    """Decorator that takes in argument for informative text"""

    def section_decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            print(f"{f' {info} ':{cng.SECTION_SYMBOL}^{cng.HIGHLIGHT_MIN_WIDTH}}")
            print(end=cng.SECTION_START_STR)
            result = f(*args, **kwargs)
            print(end=cng.SECTION_END_STR)
            return result

        return wrapper

    return section_decorator


@section("Data directory")
def check_generate_datadir() -> None:
    """Checks and if necessary, sets up directories and sqlite3 database """
    # If generated data directory does NOT exit
    if not os.path.isdir(cng.GENERATED_DATA_DIR):
        # Create directory
        print(f"Directory for generated data not found")
        print(f"Creating directory for generated data: {cng.GENERATED_DATA_DIR}")
        pathlib.Path(dirpath / cng.GENERATED_DATA_DIR).mkdir(parents=True, exist_ok=True)
    else:
        print(f"Found directory for generated data: {cng.GENERATED_DATA_DIR}")

    db_path = os.path.join(cng.GENERATED_DATA_DIR, cng.BBOX_DB_FILE)
    if not os.path.isfile(db_path):
        print(f"DB not found, setting up DB at {db_path}")
        # Setup database
        db_ = DatabaseMaker()
        # Create all tables
        for f in db_.table_create_funcs:
            f()
    else:
        print(f"Found database file: {db_path}")


def assert_image_saved(filepath: str) -> None:
    """
    Used to assert that image in filepath exists, will automatically handle stereo and single
    case
    """
    errormsgs = "Render results are missing:"
    if bpy.context.scene.render.use_multiview:
        print("Asserting multiview output")
        l_path = filepath + f"{cng.FILE_SUFFIX_LEFT}{cng.DEFAULT_FILEFORMAT_EXTENSION}"
        r_path = filepath + f"{cng.FILE_SUFFIX_RIGHT}{cng.DEFAULT_FILEFORMAT_EXTENSION}"

        l_exists = os.path.exists(l_path)
        r_exists = os.path.exists(r_path)

        if not l_exists:
            errormsgs += f"\nLeft image not found, expected to find: \n\t{l_path}"
        if not r_exists:
            errormsgs += f"\nRight image not found, expected to find: \n\t{r_path}"

        if not (l_exists and r_exists):
            raise FileNotFoundError(errormsgs)
    else:
        print("Asserting singleview output")
        path = filepath + cng.DEFAULT_FILEFORMAT_EXTENSION
        file_exists = os.path.exists(path)
        if not file_exists:
            raise FileNotFoundError(f"Image not found, expected to find: \n\t{path}")


def main(n: int, bbox_modes: Sequence[str], wait: bool, stdbboxcam: bpy.types.Object) -> None:
    """Main function for generating data with Blender

    Parameters
    ----------
    n : int
        Number of images to render
    bbox_modes : Sequence[str]
        Sequence of modes to save bounding boxes, given as strings. Available: xyz cps
    """
    check_generate_datadir()

    scene = gen.Scenemaker()
    gen.create_metadata(scene)
    con = db.connect(str(dirpath / cng.GENERATED_DATA_DIR / cng.BBOX_DB_FILE))
    cursor = con.cursor()

    datavisitor = gen.DatadumpVisitor(stdbboxcam=stdbboxcam, bbox_modes=bbox_modes, cursor=cursor)

    maxids = [
        gen.get_max_imgid(cursor, table) for table in (cng.BBOX_DB_TABLE_CPS, cng.BBOX_DB_TABLE_XYZ)
    ]

    maxid = max(maxids)

    if maxid < 0:
        maxid = 0
    else:
        maxid += 1

    imgpath = str(dirpath / cng.GENERATED_DATA_DIR / cng.IMAGE_DIR / cng.IMAGE_NAME)

    print_boxed(
        "Output information:",
        f"Imgs to render: {n}",
        f"Starting at index: {maxid}",
        f"Ends at index: {maxid+n-1}",
        f"Saves images at: {os.path.join(cng.GENERATED_DATA_DIR, cng.IMAGE_DIR)}",
        f"Sqlite3 DB at: {os.path.join(cng.GENERATED_DATA_DIR, cng.BBOX_DB_FILE)}",
        f"Metadata at: {os.path.join(cng.GENERATED_DATA_DIR, cng.METADATA_FILE)}",
        f"bbox_modes: {bbox_modes}",
    )

    if wait:
        input("Press enter to start rendering")

    def commit():
        print_boxed(f"Commited to {cng.BBOX_DB_FILE}")
        con.commit()

    print_boxed("Rendering initialized")

    commit_flag: bool = False  # To make Pylance happy
    for i in range(maxid, maxid + n):
        scene.clear()
        scene.generate_scene(np.random.randint(1, 6))
        imgfilepath = imgpath + str(i)
        print(f"Starting to render imgnr {i}")
        utils.render_and_save(imgfilepath)
        print(f"Returned from rendering imgnr {i}")

        try:
            assert_image_saved(imgfilepath)
        except FileNotFoundError as e:
            print(e)
            print("Breaking render loop")
            commit_flag == False  # Will enable commit after the loop
            break

        datavisitor.set_n(i)
        datavisitor.visit(scene)

        # Only commit in intervals
        commit_flag = not i % cng.COMMIT_INTERVAL

        if commit_flag:
            commit()

    # If loop exited without commiting remaining stuff
    if commit_flag == False:
        commit()

    con.close()


@section("Device")
def set_attrs_device(target_device: str) -> None:
    """target_device can be CUDA or CPU"""
    assert target_device in ("CUDA", "CPU")
    print("Note: Eevee only supports GPU, so setting GPU will only affect CYCLES")
    print(f"Specified target device: {target_device}")
    print("Getting hardware devices:")
    # YOU NEED TO DO THIS SO THAT BLENDER LOADS AVAILABLE DEVICES!!!
    bpy.context.preferences.addons["cycles"].preferences.get_devices()
    # Also note that EEVEE only runs on GPU, so there is need to explicitly activate GPU for EEVEE
    devices: Iterable = bpy.context.preferences.addons["cycles"].preferences.devices
    for d in devices:
        print("\t", d.id)

    try:
        bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
        for device in devices:
            if device.type == target_device:
                print(f"Enabling device: {device.id}")
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
    print(f"Cycles device is now preemptively set to: {bpy.context.scene.cycles.device}")


@section("Engine")
def set_attrs_engine(engine: str, samples: int) -> None:
    assert engine in ("BLENDER_EEVEE", "CYCLES")

    bpy.context.scene.render.engine = engine
    print(f"Render engine is now set to: {bpy.context.scene.render.engine}")

    if engine == "CYCLES":
        bpy.context.scene.cycles.progressive = "BRANCHED_PATH"
        bpy.context.scene.cycles.samples = samples  # .samples for PATH tracing, not r eally used
        bpy.context.scene.cycles.aa_samples = samples  # .aa_samples for BRANCHED_PATH tracing
        print(f"Cycles is set to: {bpy.context.scene.cycles.progressive}")
        print(f"Cycles will render with {bpy.context.scene.cycles.aa_samples} samples")
    elif engine == "BLENDER_EEVEE":
        # EEVEE only works with GPU, no need to explicitly set GPU usage
        bpy.context.scene.eevee.taa_render_samples = samples
        print(f"Eevee will render with {bpy.context.scene.eevee.taa_render_samples} samples")


@section("View mode")
def set_attrs_view(mode: str) -> None:
    """
    modes:
        'center'
        'leftright'
    """
    print(f"View mode: {mode}")
    if mode == "center":
        bpy.context.scene.render.use_multiview = False
    if mode == "leftright":
        bpy.context.scene.render.use_multiview = True

    bpy.context.scene.render.views_format = (
        "MULTIVIEW"  # no effect if bpy.context.scene.render.use_multiview = False
    )
    bpy.context.scene.render.views["left"].file_suffix = cng.FILE_SUFFIX_LEFT
    bpy.context.scene.render.views["right"].file_suffix = cng.FILE_SUFFIX_RIGHT
    bpy.context.scene.render.views["center"].file_suffix = cng.FILE_SUFFIX_CENTER

    # (left, right, center)
    cammask = (False, False, True)  # Defaults to center only, also to make PyLance happy

    if mode == "center":  # Know this is redundant, but it is to emphasize all possible choices
        cammask = (False, False, True)  # Defaults to center only, also to make PyLance happy
    if mode == "leftright":
        cammask = (True, True, False)

    (
        bpy.context.scene.render.views["left"].use,
        bpy.context.scene.render.views["right"].use,
        bpy.context.scene.render.views["center"].use,
    ) = cammask

    cameras: Tuple[bpy.types.Object] = tuple(bpy.data.collections[cng.CAM_CLTN].all_objects)
    for use, cam in zip(cammask, cameras):
        if use:
            print(f"{cam.name} will be used for rendering")
            cam.data.type = "PERSP"
            cam.data.lens_unit = "FOV"
            cam.data.angle = 1.0471975803375244  # 60 degrees in radians
            cam.data.clip_start = 0.0001
            cam.data.clip_end = 1000
            print(f"{cam.name}'s attributes are set to hardcoded values")


@section("Clear data")
def clear_generated_data() -> None:
    """Removes the directory cng.GENEREATED_DATA_DIR"""
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


def set_attrs_dir(dir_: str) -> None:
    cng.GENERATED_DATA_DIR = dir_


def handle_clear(clear: bool, clear_exit: bool) -> None:
    if (clear or clear_exit) == True:
        clear_generated_data()
        if clear_exit == True:
            print("Exiting")
            exit()


def handle_bbox(bbox: str) -> Tuple[str]:
    if bbox == "all":
        bbox_ = (cng.BBOX_MODE_CPS, cng.BBOX_MODE_XYZ, cng.BBOX_MODE_FULL, cng.BBOX_MODE_STD)
    else:
        bbox_ = (bbox,)
    return bbox_


@section("Standard bounding box options")
def handle_stdbboxcam(camchoice: str, view_mode: str) -> bpy.types.Object:
    print("Note: camera for bounding box will be set regardless of use")
    info = "{} will be used to calculate standard bounding"
    if view_mode == "center":
        print(info.format(cng.CAMERA_OBJ_CENTER))
        return bpy.data.objects[cng.CAMERA_OBJ_CENTER]
    if view_mode == "leftright":
        if camchoice == "left":
            print(info.format(cng.CAMERA_OBJ_LEFT))
            return bpy.data.objects[cng.CAMERA_OBJ_LEFT]
        if camchoice == "right":
            print(info.format(cng.CAMERA_OBJ_RIGHT))
            return bpy.data.objects[cng.CAMERA_OBJ_RIGHT]


@section("Show reference")
def show_reference(hide: bool) -> None:
    """Show reference collection or not. Reference collection contains object used to sanity
    check Blender stuff.

    Parameters
    ----------
    hide : bool
    """
    bpy.data.collections[cng.REF_CLTN].hide_render = hide
    print(f"Hide objects in reference collection: {bpy.data.collections[cng.REF_CLTN].hide_render}")


if __name__ == "__main__":
    print_boxed(
        "FISH GENERATION BABYYY",
        f"Blender version: {bpy.app.version_string}",
        f"Python version: {sys.version.split()[0]}",
        end="\n\n",
    )

    parser = utils.ArgumentParserForBlender()

    parser.add_argument(
        "n_imgs", help="Number of images to generate, default 1", type=int, nargs="?", default=1
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
        help=f"Specify Blender target hardware, defults: {cng.ARGS_DEFAULT_DEVICE}",
        choices=("CUDA", "CPU"),
        default=cng.ARGS_DEFAULT_DEVICE,
        const=cng.ARGS_DEFAULT_DEVICE,
        nargs="?",
    )

    parser.add_argument(
        "-s",
        "--samples",
        help=f"Rendering samples for cycles and eevee, default {cng.ARGS_DEFAULT_RENDER_SAMPLES}",
        default=cng.ARGS_DEFAULT_RENDER_SAMPLES,
        type=int,
        nargs="?",
    )

    parser.add_argument(
        "-b",
        "--bbox",
        help=f"Bounding box type to be stored in SQL database, default: {cng.ARGS_DEFAULT_BBOX_MODE}",
        choices=(cng.BBOX_MODE_CPS, cng.BBOX_MODE_XYZ, cng.BBOX_MODE_STD, "all"),
        default=cng.ARGS_DEFAULT_BBOX_MODE,
        const=cng.ARGS_DEFAULT_BBOX_MODE,
        nargs="?",
    )

    parser.add_argument(
        "-r", "--reference", help="Include reference objects in render", action="store_false"
    )

    parser.add_argument(
        "--view-mode",
        help=f"Set render mode between leftright (stereo) or center (single), default: {cng.ARGS_DEFAULT_VIEW_MODE}",
        choices=("leftright", "center"),
        default=cng.ARGS_DEFAULT_VIEW_MODE,
        const=cng.ARGS_DEFAULT_VIEW_MODE,
        nargs="?",
    )

    parser.add_argument(
        "-w",
        "--wait",
        help="Ask for user to press enter before starting rendering process",
        action="store_true",
    )

    parser.add_argument(
        "--dir",
        help=f"Specify dir for generated data, default: {cng.GENERATED_DATA_DIR}",
        default=cng.GENERATED_DATA_DIR,
    )

    parser.add_argument(
        "--stdbboxcam",
        help=f"Specify which camera std bbox should be generated to, default: {cng.ARGS_DEFAULT_STDBBOX_CAM}",
        choices=("left", "right"),
        default=cng.ARGS_DEFAULT_STDBBOX_CAM,
        const=cng.ARGS_DEFAULT_STDBBOX_CAM,
        nargs="?",
    )

    args = parser.parse_args()

    set_attrs_dir(args.dir)
    set_attrs_device(args.device)
    set_attrs_engine(args.engine, args.samples)
    set_attrs_view(args.view_mode)
    show_reference(args.reference)
    handle_clear(args.clear, args.clear_exit)

    main(
        n=args.n_imgs,
        bbox_modes=handle_bbox(args.bbox),
        wait=args.wait,
        stdbboxcam=handle_stdbboxcam(args.stdbboxcam, args.view_mode),
    )
