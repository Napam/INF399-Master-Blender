"""
Main python file to control Blender application

Written by Naphat Amundsen
"""

import os
import pathlib
import sys
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
import abc

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

import config as cng
import utils

import generate as gen
from setup_db import DatabaseMaker


@utils.section("Data directory")
def check_or_create_datadir(directory: str, db_file: str) -> None:
    """Checks and if necessary, sets up directories and sqlite3 database """
    print(f"Specified directory for generated data:\n\t{directory}")
    # If generated data directory does NOT exit
    if not os.path.isdir(directory):
        # Create directory
        print(f"Directory for generated data not found")
        print(f"Creating directory for generated data: {utils.yellow(directory)}")
        pathlib.Path(dirpath / directory).mkdir(parents=True, exist_ok=True)
    else:
        print(f"Found directory for generated data: {utils.yellow(directory)}")

    db_path = os.path.join(directory, db_file)
    if not os.path.isfile(db_path):
        print(f"DB not found, setting up DB at {utils.yellow(db_path)}")
        # Setup database
        print("Creating instance of DatabaseMaker to create database")
        db_ = DatabaseMaker(db_path)
        # Create all tables
        for f in db_.table_create_funcs:
            f()
    else:
        print(f"Found database file: {utils.yellow(db_path)}")


def assert_image_saved(filepath: str, view_mode: str) -> None:
    """
    Used to assert that image in filepath exists, will automatically handle stereo and single
    case
    """
    assert view_mode in ("leftright", "topcenter", "center", "all")

    errormsgs = "Render results are missing:"

    if view_mode in ("leftright", "all"):
        print(f"Asserting multiview ({utils.yellow('leftright')}) output")
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
    if view_mode in ("topcenter", "all"):
        print(f"Asserting multiview ({utils.yellow('topcenter')}) output")
        center_path = filepath + f"{cng.FILE_SUFFIX_CENTER}{cng.DEFAULT_FILEFORMAT_EXTENSION}"
        center_top_path = (
            filepath + f"{cng.FILE_SUFFIX_CENTER_TOP}{cng.DEFAULT_FILEFORMAT_EXTENSION}"
        )

        center_exists = os.path.exists(center_path)
        centertop_exists = os.path.exists(center_top_path)

        if not center_exists:
            errormsgs += f"\nCenter image not found, expected to find: \n\t{center_path}"
        if not centertop_exists:
            errormsgs += f"\nTop center image not found, expected to find: \n\t{center_top_path}"

        if not (center_path and center_top_path):
            raise FileNotFoundError(errormsgs)
    if view_mode == "center":
        print(f"Asserting singleview ({utils.yellow('center')}) output")
        path = filepath + cng.DEFAULT_FILEFORMAT_EXTENSION
        file_exists = os.path.exists(path)
        if not file_exists:
            raise FileNotFoundError(f"Center image not found, expected to find: \n\t{path}")


class BaseBlenderRender(abc.ABC):
    """
    Base class for scene making and rendering

    This class has a self.setup_scene attribute that must be set to a method, taking in imgnr.
    The reason self.setup_scene is not made into an abstract method is so you
    can flexibly determine what it should be based on arguments.
    """

    def __init__(
        self,
        data_dir: str,
        img_dir: str,
        base_img_name: str,
        wait: bool,
        view_mode: str,
        interval: Optional[int] = None,
    ):
        """Base class for classes that follows the pattern:
            1. Set up objects and stuff in Blender scene
            2. Render stuff
            3. Extract information by callbacks
            4. Dump information (and renders) to directory

        Parameters
        ----------
        data_dir : str
            Directory to dump data into
        base_img_name : str
            Base name of images, e.g. "img", so renders will be img0.png, img1.png ...
        wait : bool
            Ask for user to press enter before running render loop (to read messages)
        view_mode : str
            center, leftright, topcenter, all
        interval : Optional[int], optional
            Interval to call intervalled callback, by default None
        """
        self.wait: bool = wait
        self.data_dir: str = data_dir
        self.base_img_name: str = base_img_name
        self.view_mode: str = view_mode
        self.imgpath: str = str(dirpath / data_dir / img_dir / base_img_name)
        self.interval = cng.COMMIT_INTERVAL if interval is None else interval

        self.imgnr_iter: Optional[Iterable[int]] = None
        self.pre_loop_messages: Optional[Sequence[str]] = None
        self.setup_scene: Optional[Callable] = None  # Called every iteration before rendering
        self.iter_callback: Optional[Callable] = None  # Called after every render
        self.interval_callback: Optional[Callable] = None  # Called in intervals after render
        self.end_callback: Optional[Callable] = None  # Called after render loop is done

        self.setup_scene_kwargs: dict = {}

    @abc.abstractmethod
    def initalize_imgnr_iter(self):
        """
        Should set self.imgnr_iter to something

        Will get called at beginning of self.render_loop
        """
        raise NotImplementedError()

    def assert_before_loop(self):
        assert self.imgnr_iter is not None, "attribute self.imgnr_iter (iterable) is not set!"
        assert self.setup_scene is not None, "attibute self.setup_scene (callable) is not set!"
        assert self.iter_callback is not None, "attribute self.iter_callback (callable) is not set!"
        assert (
            self.interval_callback is not None
        ), "attribute self.intervalled_callback (callable) is not set!"
        assert self.end_callback is not None, "attribute self.end_callback (callable) is not set!"

    def render_loop(self):
        """
        Provides a base behavior for blender render loops
        """
        self.initalize_imgnr_iter()
        self.assert_before_loop()

        if self.pre_loop_messages:
            utils.print_boxed("Output information:", *self.pre_loop_messages)

        if self.wait:
            input("Press enter to start rendering\n")

        utils.print_boxed("Rendering initialized")

        len_iter = len(self.imgnr_iter)
        interval_flag: bool = False  # To make Pylance happy
        for iternum, imgnr in enumerate(self.imgnr_iter):
            self.setup_scene(imgnr, **self.setup_scene_kwargs)
            imgfilepath = self.imgpath + str(imgnr)
            print(f"Starting to render imgnr {imgnr}")
            utils.render_and_save(imgfilepath)
            print(f"Returned from rendering imgnr {imgnr}")

            try:
                assert_image_saved(imgfilepath, self.view_mode)
            except FileNotFoundError as e:
                print(e)
                print("Breaking render loop")
                interval_flag == False  # Will enable callback after the loop
                break

            self.iter_callback(imgnr)

            # Only commit in intervals
            interval_flag = not imgnr % self.interval

            if interval_flag:
                self.interval_callback(imgnr)

            print("Progress: ", utils.yellow(f"{iternum+1} / {len_iter}"))

        # If loop exited without commiting remaining stuff
        # This test is kinda redundant, but idk man
        if interval_flag == False:
            self.interval_callback(imgnr)

        self.end_callback()


class BlenderRenderGenerater(BaseBlenderRender):
    def __init__(
        self,
        data_dir: str,
        img_dir: str,
        base_img_name: str,
        wait: bool,
        view_mode: str,
        n: int,
        bbox_modes: Sequence[str],
        stdbboxcam: bpy.types.Object,
        nspawnrange: Tuple[int, int],
    ):
        super().__init__(data_dir, img_dir, base_img_name, wait, view_mode)
        check_or_create_datadir(cng.GENERATED_DATA_DIR, cng.BBOX_DB_FILE)

        self.n: int = n
        self.bbox_modes: Sequence[str] = bbox_modes
        self.stdbboxcam: bpy.types.Object = stdbboxcam
        self.nspawnrange: Tuple[int, int] = nspawnrange

        self.con = db.connect(str(dirpath / cng.GENERATED_DATA_DIR / cng.BBOX_DB_FILE))
        self.cursor = self.con.cursor()

        self.maker = gen.Scenemaker()
        gen.create_metadata(self.maker)
        self.extractor = gen.DatadumpVisitor(
            stdbboxcam=stdbboxcam, bbox_modes=bbox_modes, cursor=self.cursor
        )

        self.setup_scene = self._setup_scene
        self.interval_callback = self.commit
        self.iter_callback = self.extract_labels
        self.end_callback = self.close_con

    def commit(self, imgnr: Optional[int] = None):
        self.con.commit()
        utils.print_boxed(f"Commited to {cng.BBOX_DB_FILE}")

    def extract_labels(self, imgnr: int):
        self.extractor.set_n(imgnr)
        self.extractor.visit(self.maker)

    def close_con(self):
        utils.print_boxed(f"Closed connection to {cng.BBOX_DB_FILE}")
        self.con.close()

    def _setup_scene(self, imgnr: int):
        self.maker.clear()
        self.maker.generate_scene(np.random.randint(*self.nspawnrange))

    def initalize_imgnr_iter(self):
        maxids = [
            gen.get_max_imgid(self.cursor, table)
            for table in (cng.BBOX_DB_TABLE_CPS, cng.BBOX_DB_TABLE_XYZ)
        ]

        maxid = max(maxids)

        if maxid < 0:
            maxid = 0
        else:
            maxid += 1

        self.pre_loop_messages = (
            f"Imgs to render: {self.n}",
            f"Starting at index: {maxid}",
            f"Ends at index: {maxid+self.n-1}",
            f"Saves images at: {os.path.join(self.data_dir, cng.IMAGE_DIR)}",
            f"Sqlite3 DB at: {os.path.join(self.data_dir, cng.BBOX_DB_FILE)}",
            f"Metadata at: {os.path.join(self.data_dir, cng.METADATA_FILE)}",
            f"bbox_modes: {self.bbox_modes}",
        )

        self.maxid = maxid
        self.imgnr_iter = range(maxid, maxid + self.n)


def main(
    n: int,
    bbox_modes: Sequence[str],
    wait: bool,
    stdbboxcam: bpy.types.Object,
    view_mode: str,
    nspawnrange: Tuple[int, int],
) -> None:
    """Main function for generating data with Blender

    Parameters
    ----------
    n : int
        Number of images to render
    bbox_modes : Sequence[str]
        Sequence of modes to save bounding boxes, given as strings. Available: xyz cps full std
    wait : bool
        Wait for user input before starting rendering process
    stdbboxcam : bpy.types.Object
        Camera object that is to be used for extracting 2D bounding boxes
    view_mode : str
        Essentially which cameras to render from,
    """
    check_or_create_datadir(cng.GENERATED_DATA_DIR, cng.BBOX_DB_FILE)

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

    utils.print_boxed(
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
        input("Press enter to start rendering\n")

    def commit():
        utils.print_boxed(f"Commited to {cng.BBOX_DB_FILE}")
        con.commit()

    utils.print_boxed("Rendering initialized")

    commit_flag: bool = False  # To make Pylance happy
    for iternum, i in enumerate(range(maxid, maxid + n)):
        scene.clear()
        scene.generate_scene(np.random.randint(*nspawnrange))
        imgfilepath = imgpath + str(i)
        print(f"Starting to render imgnr {i}")
        utils.render_and_save(imgfilepath)
        print(f"Returned from rendering imgnr {i}")

        try:
            assert_image_saved(imgfilepath, view_mode)
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

        print("Progress: ", utils.yellow(f"{iternum+1} / {n}"))

    # If loop exited without commiting remaining stuff
    if commit_flag == False:
        commit()

    con.close()


@utils.section("Device")
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
                print(f"Enabling device: {utils.yellow(device.id)}")
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


@utils.section("Engine")
def set_attrs_engine(engine: str, samples: int) -> None:
    assert engine in ("BLENDER_EEVEE", "CYCLES")

    bpy.context.scene.render.engine = engine
    print(f"Render engine is now set to: {utils.yellow(bpy.context.scene.render.engine)}")

    if engine == "CYCLES":
        bpy.context.scene.cycles.progressive = "BRANCHED_PATH"
        bpy.context.scene.cycles.samples = samples  # .samples for PATH tracing, not r eally used
        bpy.context.scene.cycles.aa_samples = samples  # .aa_samples for BRANCHED_PATH tracing
        print(f"Cycles is set to: {bpy.context.scene.cycles.progressive}")
        print(
            f"Cycles will render with {utils.yellow(str(bpy.context.scene.cycles.aa_samples))} samples"
        )
    elif engine == "BLENDER_EEVEE":
        # EEVEE only works with GPU, no need to explicitly set GPU usage
        bpy.context.scene.eevee.taa_render_samples = samples
        print(f"Eevee will render with {bpy.context.scene.eevee.taa_render_samples} samples")


@utils.section("View mode")
def set_attrs_view(mode: str) -> None:
    """
    Select which cameras to do rendering

    modes:
        'center'
        'leftright'
        'topcenter'
        'all'
    """
    assert mode in ("center", "leftright", "topcenter", "all")
    print(f"View mode: {mode}")

    if mode == "center":
        bpy.context.scene.render.use_multiview = False
    elif mode in ("leftright", "topcenter", "all"):
        bpy.context.scene.render.use_multiview = True
    else:
        raise ValueError(f"Got invalid view mode, got {mode}")

    bpy.context.scene.render.views_format = (
        "MULTIVIEW"  # no effect if bpy.context.scene.render.use_multiview = False
    )

    views = bpy.context.scene.render.views
    cams: Mapping[str, bpy.types.Object] = bpy.data.collections[cng.CAM_CLTN].objects

    # Keys correspond to "Output properties" -> Stereoscopy -> Multi-View in Blender
    views["left"].file_suffix = cng.FILE_SUFFIX_LEFT
    views["right"].file_suffix = cng.FILE_SUFFIX_RIGHT
    views["center"].file_suffix = cng.FILE_SUFFIX_CENTER
    views["center_top"].file_suffix = cng.FILE_SUFFIX_CENTER_TOP

    view2cam = {
        "left": cams[cng.CAMERA_OBJ_LEFT],
        "right": cams[cng.CAMERA_OBJ_RIGHT],
        "center": cams[cng.CAMERA_OBJ_CENTER],
        "center_top": cams[cng.CAMERA_OBJ_CENTER_TOP],
    }

    views_dict: Dict[str, bool] = {
        "center": False,
        "top_center": False,
        "left": False,
        "right": False,
    }

    if mode == "center":
        views_dict["center"] = True
    elif mode == "leftright":
        views_dict["left"] = True
        views_dict["right"] = True
    elif mode == "topcenter":
        views_dict["center"] = True
        views_dict["center_top"] = True
    elif mode == "all":
        views_dict["left"] = True
        views_dict["right"] = True
        views_dict["center"] = True
        views_dict["center_top"] = True

    # Disables all cameras in Properties pane -> Output properties -> Stereoscopy -> Multi-View
    # to get a "clean slate"
    for camera in bpy.context.scene.render.views:
        camera.use = False

    for view_name, use in views_dict.items():
        if use:
            views[view_name].use = True
            cam = view2cam[view_name]
            print(f"Camera '{utils.yellow(cam.name)}' will be used for rendering")
            cam.data.type = "PERSP"
            cam.data.lens_unit = "FOV"
            cam.data.angle = 1.0471975803375244  # 60 degrees in radians
            cam.data.clip_start = 0.0001
            cam.data.clip_end = 1000
            print(f"{cam.name}'s attributes are set to hardcoded values")


# Decorate existing function
rm_directory: Callable = utils.section("Clear data")(utils.rm_directory)


def set_attrs_dir(dir_: str) -> None:
    cng.GENERATED_DATA_DIR = dir_

utils.section("Clear data")
def handle_clear(clear: bool, clear_exit: bool, directory: str) -> None:
    """
    Handles --clear and --clear-exit options
    """
    if (clear or clear_exit) == True:
        rm_directory(directory, doublecheck=True)
        if clear_exit == True:
            print("Exiting")
            exit()


def handle_bbox(bbox: str) -> Tuple[str]:
    """
    Handles -b and --bbox options
    """
    if bbox == "all":
        bbox_ = (cng.BBOX_MODE_CPS, cng.BBOX_MODE_XYZ, cng.BBOX_MODE_FULL, cng.BBOX_MODE_STD)
    else:
        bbox_ = (bbox,)
    return bbox_


@utils.section("Standard bounding box options")
def handle_stdbboxcam(camchoice: str, view_mode: str) -> bpy.types.Object:
    """
    Takes --stdbboxcam and --view-mode arguments and returns a camera object
    """
    print("Note: camera for bounding box will be set regardless of use")
    camdict = {
        "left": cng.CAMERA_OBJ_LEFT,
        "right": cng.CAMERA_OBJ_RIGHT,
        "center": cng.CAMERA_OBJ_CENTER,
        "top": cng.CAMERA_OBJ_CENTER_TOP,
    }
    assert camchoice in camdict, "Invalid camchoice"

    dicky = {
        "leftright": {"left", "right"},
        "all": camdict.keys(),
        "topcenter": {"top", "center"},
        "center": {"center"},
    }

    print(f"Choice of camera: {camchoice}")
    if not camchoice in dicky[view_mode]:
        print(
            f"{utils.red('WARNING:')} Choice of stdbbox camera is \"{camchoice}\", which is not\n"
            f"{' '*len('WARNING: ')}included for rendering since view mode is \"{view_mode}\""
        )

    # Should match the name of corresponding camera in Blender
    camera_name: str = camdict[camchoice]
    print(f"{utils.yellow(camera_name)} will be used to calculate standard bounding boxes")
    return bpy.data.objects[camera_name]


@utils.section("Show reference (UiB owl)")
def show_reference(hide: bool) -> None:
    """Show reference collection or not. Reference collection contains object used to sanity
    check Blender stuff.

    Parameters
    ----------
    hide : bool
    """
    bpy.data.collections[cng.REF_CLTN].hide_render = hide
    print(f"Hide objects in reference collection: {bpy.data.collections[cng.REF_CLTN].hide_render}")


@utils.section("Number of fish to spawn")
def handle_minmax(minmax: Optional[Tuple[int, int]]) -> Tuple[int, int]:
    """Handles --minmax option that should give a list of two ints

    Parameters
    ----------
    minmax : Optional[Tuple[int, int]]
        spawn range ~Uniform(*minmax)
    """
    if minmax is None:
        minmax = cng.DEFAULT_SPAWNRANGE

    assert len(minmax) == 2
    assert isinstance(minmax[0], int)
    assert isinstance(minmax[1], int)

    print(
        f"Number of fish in a scene will be sampled from {utils.yellow(f'Uniform({minmax[0]}, {minmax[1]})')}"
    )
    return minmax


if __name__ == "__main__":
    utils.print_boxed(
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
    )

    parser.add_argument("--clear", help="Clears generated data before running", action="store_true")
    parser.add_argument("--clear-exit", help="Clears generated data and exits", action="store_true")

    parser.add_argument(
        "-d",
        "--device",
        help=f"Specify Blender target hardware, defults: {cng.ARGS_DEFAULT_DEVICE}",
        choices=("CUDA", "CPU"),
        default=cng.ARGS_DEFAULT_DEVICE,
    )

    parser.add_argument(
        "-s",
        "--samples",
        help=f"Rendering samples for cycles and eevee, default {cng.ARGS_DEFAULT_RENDER_SAMPLES}",
        default=cng.ARGS_DEFAULT_RENDER_SAMPLES,
        type=int,
    )

    parser.add_argument(
        "-b",
        "--bbox",
        help=f"Bounding box type to be stored in SQL database, default: {cng.ARGS_DEFAULT_BBOX_MODE}",
        choices=(cng.BBOX_MODE_CPS, cng.BBOX_MODE_XYZ, cng.BBOX_MODE_STD, "all"),
        default=cng.ARGS_DEFAULT_BBOX_MODE,
    )

    parser.add_argument(
        "--reference", help="Include reference objects in render", action="store_false"
    )

    parser.add_argument(
        "--view-mode",
        help=f"Set render mode between leftright (stereo), topside (top and center), center (single), or all (every camera) default: {cng.ARGS_DEFAULT_VIEW_MODE}",
        choices=("leftright", "center", "topcenter", "all"),
        default=cng.ARGS_DEFAULT_VIEW_MODE,
    )

    parser.add_argument(
        "--no-wait",
        help="Dont wait for user input before rendering",
        action="store_false",
    )

    parser.add_argument(
        "--dir",
        help=f"Specify dir for generated data, default: {cng.GENERATED_DATA_DIR}",
        default=cng.GENERATED_DATA_DIR,
    )

    parser.add_argument(
        "--stdbboxcam",
        help=f"Specify which camera std bbox should be generated to, default: {cng.ARGS_DEFAULT_STDBBOX_CAM}",
        choices=("left", "right", "center", "top"),
        default=cng.ARGS_DEFAULT_STDBBOX_CAM,
    )

    parser.add_argument(
        "--minmax",
        help=f"The number of fish in a scene is sampled from ~U(min, max), nrange specifies min max",
        type=int,
        nargs=2,
    )

    args = parser.parse_args()
    set_attrs_dir(args.dir)
    set_attrs_device(args.device)
    set_attrs_engine(args.engine, args.samples)
    set_attrs_view(args.view_mode)
    show_reference(args.reference)
    handle_clear(args.clear, args.clear_exit, args.dir)

    # main(
    #     n=args.n_imgs,
    #     bbox_modes=handle_bbox(args.bbox),
    #     wait=args.no_wait,
    #     stdbboxcam=handle_stdbboxcam(args.stdbboxcam, args.view_mode),
    #     view_mode=args.view_mode,
    #     nspawnrange=handle_minmax(args.minmax),
    # )

    BlenderRenderGenerater(
        data_dir=args.dir,
        img_dir=cng.IMAGE_DIR,
        base_img_name=cng.IMAGE_NAME,
        n=args.n_imgs,
        bbox_modes=handle_bbox(args.bbox),
        wait=args.no_wait,
        stdbboxcam=handle_stdbboxcam(args.stdbboxcam, args.view_mode),
        view_mode=args.view_mode,
        nspawnrange=handle_minmax(args.minmax),
    ).render_loop()