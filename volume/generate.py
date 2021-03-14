'''
Code used to setup scenes, and extracting labels

Written by Naphat Amundsen
'''
import abc
import os
import pathlib
import random
import sys
import time
from importlib import reload
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import bpy
import numpy as np

# Add local files ty pythondir in order to import relative files
dir_ = os.path.dirname(bpy.data.filepath)
if dir_ not in sys.path:
    sys.path.append(dir_)
dirpath = pathlib.Path(dir_)

import sqlite3 as db

import config as cng
import utils
from debug import debug, debugs, debugt

reload(utils)
reload(cng)


def get_spawn_locs(n: int, spawnbox: Optional[str] = None) -> np.ndarray:
    """
    Helper function get spawn location for objects

    Parameters:
    ------------
    n: rows of matrix

    spawnbox: name is the spawning box, that is the cube that the fishes can spawn
              within

    Returns:
    --------
    points: np.ndarray of size (n,3), each row representing a 3D location for one
            object.
    """
    if spawnbox is None:
        spawnbox = cng.SPAWNBOX_OBJ

    box = bpy.data.objects[spawnbox]
    loc = np.array(box.location)  # Center location
    scale = np.array(box.scale)

    points = np.random.uniform(low=-scale, high=scale, size=(n, 3)) + loc
    return points


def get_euler_rotations(n: int) -> np.ndarray:
    """
    Helper function to get euler rotations for objects

    Parameters:
    -----------
    n: rows of matrix

    Returns:
    --------
    rotations: np.ndarray of size (n,3), each row representing a euler rotation for
               one object. Angles are in radians.
    """
    mus = cng.ROT_MUS
    stds = cng.ROT_STDS
    rotations = np.random.normal(loc=mus, scale=stds, size=(n, 3))
    return rotations


def change_to_spawnbox_coords(loc: np.ndarray) -> np.ndarray:
    """Helper function to change locations to spawnbox locations, will normalize wil
    respect to spawnbox dimensions. Assumes that spawnbox does not have no rotation, that
    is the spawnbox sides is parallell to axes.

    Parameters
    ----------
    loc : Sequence[float]
        Location vector
    """
    spawnbox: bpy.types.Object = bpy.data.objects[cng.SPAWNBOX_OBJ]
    new_origo = np.array(spawnbox.location)  # location is center point
    new_loc = loc - np.array(new_origo)
    return new_loc / np.array(spawnbox.dimensions)


def create_datadir(dirname: Optional[str] = None) -> None:
    """
    Given a filepath for a directory, create the directory.

    Specialized function to make directory for generated data

    Parameters:
    -----------
    dirname: optional, directory name. Defaults to value in config file
    """
    if dirname is None:
        dirname = cng.GENERATED_DATA_DIR

    dirname = cng.GENERATED_DATA_DIR

    pathlib.Path(dirpath / dirname).mkdir(parents=True, exist_ok=True)


def create_metadata(scene: "Scenemaker") -> None:
    """
    Creates a text file containing the metadata which is as of now a dictionary
    between
    """
    create_datadir()

    with open(dirpath / cng.GENERATED_DATA_DIR / cng.METADATA_FILE, "w+") as f:
        f.write(str(scene.num2name))


def get_max_imgid(cursor: db.Cursor, table: str) -> int:
    """
    Get max imgid, which should represent the id number (integer) of the latest
    inserted image to the database.

    Return
    ------
    maxid if there are any entries in table, else return -1
    """
    res = cursor.execute(f"SELECT MAX({cng.BBOX_DB_IMGRNR}) FROM {table}")
    maxid: int = res.fetchall()[0][0]

    if maxid is None:
        return -1
    else:
        return maxid


def camera_view_bounds_2d(
    scene: bpy.types.Scene, cam_ob: bpy.types.Object, me_ob: bpy.types.Object
) -> Tuple[int, int, int, int]:
    """
    Shamelessly copy pasted from
    https://blender.stackexchange.com/a/158236/105631
    Idk how it works, but it works

    Returns camera space bounding box of mesh object.

    Negative 'z' value means the point is behind the camera.

    Takes shift-x/y, lens angle and sensor size into account
    as well as perspective/ortho projections.

    :arg scene: Scene to use for frame size.
    :type scene: :class:`bpy.types.Scene`
    :arg obj: Camera object.
    :type obj: :class:`bpy.types.Object`
    :arg me: Untransformed Mesh.
    :type me: :class:`bpy.types.Mesh´
    :return: a Box object (call its to_tuple() method to get x, y, width and height)
    :rtype: :class:tuple
    """

    mat = cam_ob.matrix_world.normalized().inverted()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    # me_ob.evaluated_get(depsgraph) crashed on Linux build in Blender 2.83.9, but works in 2.83.13. 
    # Solution was to copy me_ob. first. But that resulted in memory leak.
    mesh_eval = me_ob.evaluated_get(depsgraph)  
    me = mesh_eval.to_mesh()  
    me.transform(me_ob.matrix_world)
    me.transform(mat)

    camera: bpy.types.Camera = cam_ob.data
    frame = [-v for v in camera.view_frame(scene=scene)[:3]]
    camera_persp: bool = camera.type != "ORTHO"  # True of PERSP

    lx = []
    ly = []

    min_x: float
    max_x: float
    min_y: float
    max_y: float

    for v in me.vertices:
        co_local: Sequence[float] = v.co
        z: float = -co_local.z

        if camera_persp:
            if z == 0.0:
                lx.append(0.5)
                ly.append(0.5)
            # Does it make any sense to drop these?
            # if z <= 0.0:
            #    continue
            else:
                frame = [(v / (v.z / z)) for v in frame]

        min_x, max_x = frame[1].x, frame[2].x
        min_y, max_y = frame[0].y, frame[1].y

        x = (co_local.x - min_x) / (max_x - min_x)
        y = (co_local.y - min_y) / (max_y - min_y)

        lx.append(x)
        ly.append(y)

    min_x = np.clip(min(lx), 0.0, 1.0)
    max_x = np.clip(max(lx), 0.0, 1.0)
    min_y = np.clip(min(ly), 0.0, 1.0)
    max_y = np.clip(max(ly), 0.0, 1.0)

    mesh_eval.to_mesh_clear()

    # r: 'bpy.types.RenderSettings' = scene.render
    # fac: float = r.resolution_percentage * 0.01
    # dim_x: float = r.resolution_x * fac
    # dim_y: float = r.resolution_y * fac

    # Sanity check
    # if round((max_x - min_x) * dim_x) == 0 or round((max_y - min_y) * dim_y) == 0:
    #     return (0, 0, 0, 0)

    # Relative values
    return (
        round(min_x, 4),  # X
        round(1 - max_y, 4),  # Y
        round((max_x - min_x), 4),  # Width
        round((max_y - min_y), 4),  # Height
    )

    # Absolute values
    return (
        int(round(min_x * dim_x)),  # X
        int(round(dim_y - max_y * dim_y)),  # Y
        int(round((max_x - min_x) * dim_x)),  # Width
        int(round((max_y - min_y) * dim_y)),  # Height
    )


class Scenevisitor(metaclass=abc.ABCMeta):
    """
    Scenevisitor interface
    """

    @abc.abstractmethod
    def visit(self, other):
        """
        Do visitor thing
        """
        pass


class DatadumpVisitor(Scenevisitor):
    """
    Visitor for Scenemaker class
    """

    def __init__(
        self,
        stdbboxcam: bpy.types.Object,
        bbox_modes: Optional[Sequence[str]] = None,
        cursor: Optional[db.Cursor] = None,
    ) -> None:
        """
        Parameters:
        -----------
        stdbboxcam: bpy.types.Object, camera object that should be used to calculate standard
                    bounding boxes. The function needs a reference

        bbox_mode: Optional[str], mode to save to SQL. Available: cps, xyz, full, std

        table: Optional str, name of table, if None, then use table specified
               in config file

        con: Optional sqlite3.connection, if None, then connection is established
             using information from config file. Changes will be committed and
             connection will close just before the method returns.
             If cursor is given, the SQL executions will be done the cursor. No comitting
             will be done. In other words, the user will have more control over what
             happens with the database when the ```cursor``` parameter is specified.
        """
        self.con = None
        self.cursor = cursor
        if self.cursor is None:
            self.con = db.connect(str(dirpath / cng.GENERATED_DATA_DIR / cng.BBOX_DB_FILE))
            self.cursor = self.con.cursor()

        self.bbox_modes = bbox_modes
        if self.bbox_modes is None:
            self.bbox_modes = (cng.DEFAULT_BBOX_MODE,)

        self.stdbboxcam = stdbboxcam

        # THE CODE BELOW DOES NOT WORK SINCE WHEN YOU GIVE A VARIABLE IN A FUNCTION CALL
        # PYTHON WILL REMEMBER IT AS A POINTER TO THE VARIBLE INSTEAD OF DEREFERENCING THE POINTER

        # self.strategy_map = {
        # choice: lambda s: self._db_store(f(s), table)
        # for choice, table, f in (
        # (cng.BBOX_MODE_CPS, cng.BBOX_DB_TABLE_CPS, self.extract_labels_cps),
        # (cng.BBOX_MODE_XYZ, cng.BBOX_DB_TABLE_XYZ, self.extract_labels_xyz),
        # )
        # }

        self.strategy_map = {
            cng.BBOX_MODE_CPS: lambda s: self._db_store(
                self.extract_labels_cps(s), cng.BBOX_DB_TABLE_CPS
            ),
            cng.BBOX_MODE_XYZ: lambda s: self._db_store(
                self.extract_labels_xyz(s), cng.BBOX_DB_TABLE_XYZ
            ),
            cng.BBOX_MODE_FULL: lambda s: self._db_store(
                self.extract_labels_full(s), cng.BBOX_DB_TABLE_FULL
            ),
            cng.BBOX_MODE_STD: lambda s: self._db_store(
                self.extract_labels_std(s), cng.BBOX_DB_TABLE_STD
            ),
        }

        self.n: int = None
        self.n_is_set: bool = False

    def set_n(self, n: int) -> None:
        """
        Set n, for image number, so if n = 12, then it will save img12...
        """
        self.n_is_set = True
        self.n = n

    def _db_store(self, labels: Sequence[Tuple[int, np.ndarray]], table: str) -> None:
        """Store labels in given table. Must be correct table or things will crash

        Parameters
        ----------
        labels : Sequence[Tuple[int, np.ndarray]]
            Sequence of tuples: [(class, things), (class, things), ...]
        table : str
            Table name in SQL database
        """
        # Labels are expected to be
        # [
        #   (class, points),
        #   (class, points)
        #         .
        #         .
        #         .
        # ]
        # Where points are np.arrays
        # There should also always be one fish in the scene => len(labels) >= 1

        n_points = np.prod(labels[0][1].shape)

        gen = ((self.n, class_, *points.ravel().round(3)) for class_, points in labels)

        # First two "?" are for image id and class respectively, rest are for points
        sql_command = (
            f'INSERT INTO {table} VALUES {("?","?",*["?" for i in range(n_points)])}'
        ).replace("'", "")

        self.cursor.executemany(sql_command, gen)

    @staticmethod
    def extract_labels_cps(scene: "Scenemaker") -> List[Tuple[int, np.ndarray]]:
        """
        Gets labels as cornerpoints (8 points in 3D space)

        Assumes that the copies of the originals are named e.g. mackerel.001, whiting.001
        etc. Blender 2.83 does this automatically at least

        Returns
        -------
        boxes_list = [(class, box), (class, box), ...]
        """
        objects = utils.select_collection(scene.target_collection)
        boxes_list = []

        for obj in objects:
            objclass = obj.name.split(".")[0]
            cornermatrix = np.empty((8, 3))
            for j, corner in enumerate(obj.bound_box):
                cornermatrix[j] = corner

            boxes_list.append((scene.name2num[objclass], cornermatrix))

        return boxes_list

    @staticmethod
    def extract_labels_xyz(scene: "Scenemaker") -> List[Tuple[int, np.ndarray]]:
        """
        Gets labels as width, length and height of box

        Assumes that the copies of the originals are named e.g. mackerel.001, whiting.001
        etc. Blender 2.83 does this automatically at least

        Returns
        -------
        boxes_list = [(class, box), (class, box), ...]
        """
        objects = utils.select_collection(scene.target_collection)
        boxes_list = []

        for obj in objects:
            objclass = obj.name.split(".")[0]
            xyz = np.array(obj.dimensions)
            boxes_list.append((scene.name2num[objclass], xyz))

        return boxes_list

    @staticmethod
    def extract_labels_full(scene: "Scenemaker") -> List[Tuple[int, np.ndarray]]:
        """
        Gets labels as bounding box dimensions, bounding box euler rotation, 3d location

        Location is in reference of spawnbox, and uses relative coordinates.

        Assumes that the copies of the originals are named e.g. mackerel.001, whiting.001
        etc. Blender 2.83 does this automatically at least

        Returns
        -------
        boxes_list = [(class, box), (class, box), ...]

                                                                     3d vectors
        where box: np.ndarray, box.shape: (9,), consists of [location, bboxdim, rotation]

        location is relative to spawnbox, that is origo is at spawnbox center,
        and the values are normalized with respect to spawnbox dimensions.
        """
        objects = utils.select_collection(scene.target_collection)
        boxes_list = []

        for obj in objects:
            objclass = obj.name.split(".")[0]
            dim = obj.dimensions
            rot = obj.rotation_euler  # Radians
            loc = change_to_spawnbox_coords(np.array(obj.location))
            boxes_list.append((scene.name2num[objclass], np.concatenate((loc, dim, rot))))

        return boxes_list

    def extract_labels_std(self, scene: "Scenemaker") -> List[Tuple[int, np.ndarray]]:
        """
        Gets labels as regular 2D bounding boxes on the image

        Assumes that the copies of the originals are named e.g. mackerel.001, whiting.001
        etc. Blender 2.83 does this automatically at least when copying

        Returns
        -------
        boxes_list = [(class, box), (class, box), ...]
        """
        objects = utils.select_collection(scene.target_collection)
        camera = self.stdbboxcam
        boxes_list = []
        for obj in objects:
            objclass = obj.name.split(".")[0]  # eg mackerel.002 -> mackerel
            box = camera_view_bounds_2d(scene=bpy.context.scene, cam_ob=camera, me_ob=obj)
            boxes_list.append((scene.name2num[objclass], np.array(box)))

        return boxes_list

    def visit(self, scene: "Scenemaker") -> None:
        """
        Visit scene
        """
        assert (
            self.n_is_set
        ), "The value of self.n must be updated using self.set_n before visiting a scene"

        for bbox_mode in self.bbox_modes:
            self.strategy_map[bbox_mode](scene)

        self.n_is_set = False


class Scenemaker:
    """
    Class for scene generation for fishes and stuff
    """

    def __init__(self, src_collection: str = None, target_collection: str = None):
        """
        Parameters
        ----------
        src_collection: name of collection containing source objects to be copied,
                           defaults to "Originals"

        target_collection: name of collection to contain copied objects
        """
        if src_collection is None:
            src_collection = cng.SRC_CLTN

        if target_collection is None:
            target_collection = cng.TRGT_CLTN

        self.src_collection = bpy.data.collections[src_collection]
        self.target_collection = bpy.data.collections[target_collection]
        self.src_objects = tuple(bpy.data.collections[src_collection].all_objects)

        # Will update classdict in-place
        self.create_classdict()

    def generate_scene(self, n: int = 3, spawnbox: Optional[str] = None) -> List[bpy.types.Object]:
        """
        Copy fishes from src_collection and place them within "spawnbox" (a box)

        Parameters
        -----------
        n: number of fishes to spawn

        spawnbox: optional, name of cube that represent spawning region, defaults to
                  "spawnbox"
        """
        locs = get_spawn_locs(n, spawnbox)
        rots = get_euler_rotations(n)

        self.src_objects: Tuple[bpy.types.Object]
        src_samples = random.choices(self.src_objects, k=n)

        for obj, loc, rot in zip(src_samples, locs, rots):
            new_obj = obj.copy() # Creates a "placeholder" that links to same attributes as orignal
            new_obj.data = obj.data.copy() # VERY IMPORTANT, actually replaces important stuff

            ##################################
            ### Set object attributes here ###
            ##################################
            new_obj.location = loc
            new_obj.rotation_euler = rot  # Treated as radians
            new_obj.scale *= np.random.normal(loc=1, scale=0.1)
            new_obj.show_bounds = True
            new_obj.show_name = False
            ##################################
            ##################################

            # Link to target collection
            self.target_collection.objects.link(new_obj)
        return src_samples

    def clear(self) -> None:
        """
        Clears objects in target collection
        """
        utils.rm_collection(self.target_collection)

    def create_classdict(self) -> Dict[str, int]:
        """
        Old behavior: Creates dictionaries between numerical and string representation of the classes

        New begaviot: Returns CLASS_DICT from config file, stricter enforcement of classes at the cost
                      of more manual labor


        Returns
        -------
        string to num dictionary for object classes
        """
        # self.name2num = {obj.name: i for i, obj in enumerate(self.src_objects)}
        # self.num2name = {i: obj.name for i, obj in enumerate(self.src_objects)}
        
        self.name2num = cng.CLASS_DICT
        self.num2name = {v: k for k, v in cng.CLASS_DICT.items()}
        return self.name2num
