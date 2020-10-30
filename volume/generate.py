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

import blender_config as cng
import blender_setup as setup
import blender_utils as utils

reload(setup)
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
               one object.
    """
    mus = cng.ROT_MUS
    stds = cng.ROT_STDS
    rotations = np.random.normal(loc=mus, scale=stds, size=(n, 3))
    return rotations


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

    with open(dirpath / cng.GENERATED_DATA_DIR / "metadata.txt", "w+") as f:
        f.write(str(scene.num2name))


def get_max_imgid(cursor: db.Cursor, table: str) -> int:
    """
    Get max imgid, which should represent the id number (integer) of the latest
    inserted image to the database.

    Return
    ------
    maxid if there are any entries in table, else return -1
    """
    res = cursor.execute(f"SELECT MAX(imgnr) FROM {table}")
    maxid = res.fetchall()[0][0]

    if maxid is None:
        return -1
    else:
        return maxid


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
        bbox_modes: Optional[Sequence[str]] = None,
        cursor: Optional[db.Cursor] = None,
    ) -> None:
        """
        Parameters:
        -----------
        bbox_mode: Optional[str], mode to save to SQL. Available: cps, xyz

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
        }

        self.n: int = None
        self.n_is_set: bool = False

    def set_n(self, n: int) -> None:
        """
        Set n
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
        Gets labels

        Assumes that the copies of the originals are named e.g. mackerel.001, whiting.001
        etc.

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
        Gets labels

        Assumes that the copies of the originals are named e.g. mackerel.001, whiting.001
        etc.

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

    def visit(self, scene: "Scenemaker"):
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
                           defaults to "Fishes"

        target_collection: name of collection to contain copied objects
        """
        if src_collection is None:
            src_collection = cng.SRC_CLTN

        if target_collection is None:
            target_collection = cng.TRGT_CLTN

        self.src_collection = bpy.data.collections[src_collection]
        self.target_collection = bpy.data.collections[target_collection]
        self.src_objects = list(bpy.data.collections[src_collection].all_objects)

        # Will update classdict in-place
        self.create_classdict()

    def generate_scene(self, n: int = 3, spawnbox: Optional[str] = None) -> List[bpy.types.Object]:
        """
        Copy fishes from src_collection and place them within "spawnbox" (a Cube)

        Parameters
        -----------
        n: number of fishes to spawn

        spawnbox: optional, name of cube that represent spawning region, defaults to
                  "spawnbox"
        """
        locs = get_spawn_locs(n, spawnbox)
        rots = get_euler_rotations(n)
        src_samples = random.choices(self.src_objects, k=n)

        for obj, loc, rot in zip(src_samples, locs, rots):
            new_obj = obj.copy()

            ##############################
            # Set object attributes here #
            ##############################
            new_obj.location = loc
            new_obj.rotation_euler = rot
            new_obj.scale *= np.random.normal(loc=1, scale=0.1)
            new_obj.show_bounds = True
            new_obj.show_name = False
            ##############################
            ##############################

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
        Creates dictionaries between numerical and string representation of the classes

        Returns
        -------
        string to num dictionary for object classes
        """
        self.name2num = {obj.name: i for i, obj in enumerate(self.src_objects)}
        self.num2name = {i: obj.name for i, obj in enumerate(self.src_objects)}
        return self.name2num
