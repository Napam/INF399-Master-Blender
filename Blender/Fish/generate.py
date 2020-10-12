import abc
import os
import pathlib
import random
import sys
import time
from importlib import reload
from typing import Dict, List, Optional, Tuple

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

import glob
from pprint import pprint


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
        spawnbox = cng.SPAWNBOX

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


def get_max_imgid(cursor: db.Cursor, table: str) -> int:
    """
    Get max imgid, which should represent the id number (integer) of the latest
    inserted image to the database.

    Return
    ------
    maxid
    """
    res = cursor.execute(f"SELECT MAX(imgnr) FROM {table}")
    maxid = res.fetchall()[0][0]

    if maxid is None:
        return 0
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
        bbox_mode: Optional[str] = None,
        cursor: Optional[db.Cursor] = None,
    ) -> None:
        """
        Parameters:
        -----------
        bbox_mode: Optional[str], mode to save to SQL. Available: cornerpints, lwh

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

        self.bbox_mode = bbox_mode
        if self.bbox_mode is None:
            self.bbox_mode = cng.DEFAULT_BBOX_MODE

        if self.bbox_mode == "cps":
            self.table = cng.BBOX_DB_TABLE_CPS
        elif self.bbox_mode == "xyz":
            self.table = cng.BBOX_DB_TABLE_XYZ

        self.db_method = None
        if self.bbox_mode == "cps":
            self.db_method = lambda s: self._db_store(self.extract_labels_cps(s))
        elif self.bbox_mode == "xyz":
            self.db_method = lambda s: self._db_store(self.extract_labels_lwh(s))
        else:
            raise ValueError(f"Unsupported mode for bbox, got {self.bbox_mode}")

        self.n: int = None
        self.n_is_set = False

    def set_n(self, n: int) -> None:
        """
        Set n
        """
        self.n_is_set = True
        self.n = n

    def _db_store(self, labels: List[Tuple[int, np.ndarray]]) -> None:
        """
        Store labels in sqlite server.
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
            f'INSERT INTO {self.table} VALUES {("?","?",*["?" for i in range(n_points)])}'
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
    def extract_labels_lwh(scene: "Scenemaker") -> List[Tuple[int, np.ndarray]]:
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
            lwh = np.array(obj.dimensions)
            boxes_list.append((scene.name2num[objclass], lwh))

        return boxes_list

    def create_metadata(self, scene: "Scenemaker") -> None:
        """
        Creates a text file containing the metadata which is as of now a dictionary
        between
        """
        create_datadir()

        with open(dirpath / cng.GENERATED_DATA_DIR / "metadata.txt", "w+") as f:
            f.write(str(scene.num2name))

    def visit(self, scene: "Scenemaker"):
        """
        Visit scene
        """
        assert (
            self.n_is_set
        ), "The value of self.n must be updated using self.set_n before visiting a scene"

        self.db_method(scene)
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

        # Deselect everything first
        bpy.ops.object.select_all(action="DESELECT")

        for obj, loc, rot in zip(src_samples, locs, rots):
            obj.select_set(True)

            # Duplicate all selected (which should be the current object only)
            # This operation should change the selected objects to the
            # duplicated objects
            bpy.ops.object.duplicate()

            new_obj = bpy.context.selected_objects[0]

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

            # Unlink object from whatever collection it was assigned to
            bpy.ops.collection.objects_remove_all()

            # Link to target collection
            self.target_collection.objects.link(new_obj)

            # Deselect object
            new_obj.select_set(False)

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
        print(self.num2name)
        return self.name2num


def main() -> None:
    scene = Scenemaker()
    con = db.connect(str(dirpath / cng.GENERATED_DATA_DIR / cng.BBOX_DB_FILE))
    cursor = con.cursor()
    bbox_mode = "xyz"
    datavisitor = DatadumpVisitor(
        cursor=cursor,
        bbox_mode=bbox_mode,
    )
    datavisitor.create_metadata(scene)
    maxid = get_max_imgid(
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

    n_data = 20
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


if __name__ == "__main__":
    main()


