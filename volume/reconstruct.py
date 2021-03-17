"""
Code used to setup scenes, and extracting labels

Written by Naphat Amundsen
"""
import abc
import os
import pathlib
import random
import sys
import time
from importlib import reload
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

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

reload(utils)
reload(cng)


class Sceneloader:
    """
    Class to recreate scene from labels from "bboxes_full"
    """

    def __init__(
        self,
        data_dir: str,
        src_collection: Optional[str] = None,
        target_collection: Optional[str] = None,
    ):
        if src_collection is None:
            src_collection = cng.SRC_CLTN

        if target_collection is None:
            target_collection = cng.TRGT_CLTN

        self.src_collection = bpy.data.collections[src_collection]
        self.target_collection = bpy.data.collections[target_collection]
        self.src_objects = tuple(bpy.data.collections[src_collection].all_objects)
        self.data_dir = data_dir

        # Will be set in self._connect_and_assert
        self.con: Optional[db.Connection] = None
        self.c: Optional[db.Cursor] = None

        self._connect_and_assert()

        with open(os.path.join(data_dir, "metadata.txt"), "r") as f:
            self.num2name: dict = eval(f.read())
            self.name2num: dict = {v: k for k, v in self.num2name.items()}

    def _connect_and_assert(self) -> None:
        """
        Connects to sqlite3 database and asserts that the table "bboxes_full" exists

        Initializes self.con, and self.c
        """
        self.con = db.connect(f"file:{os.path.join(self.data_dir, 'bboxes.db')}?mode=ro", uri=True)
        self.c = self.con.cursor()

        # Assert that the table "bboxes_full" exists
        assert "bboxes_full" in (
            # Unpack from tuple
            x[0]
            for x in self.c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        ), "Database does not contain the necessary table 'bboxes_full'"

        # Assert bboxes_full contains 9+2 (9 for bounding box, 1 for imgnr, 1 for class) columns
        n_table_cols = len(self.c.execute("SELECT * FROM bboxes_full").fetchone())
        assert (
            n_table_cols == 11
        ), f"Expected table 'bboxes_full' to have 11 columns, but got {n_table_cols}"

    def __del__(self):
        self.con.close()

    def reconstruct_scene(self, imgnr: int, spawnbox: Optional[str] = None, tag: str="") -> None:
        """
        This will not clear the existing target collection before setting up a new scene
        """
        if spawnbox is None:
            spawnbox: str = cng.SPAWNBOX_OBJ

        spawnbox: bpy.types.Object = bpy.data.objects[spawnbox]
        
        originals: Tuple[bpy.types.Object] = tuple(self.src_collection.all_objects)
        name2obj: Dict[str, bpy.types.Object] = {obj.name:obj for obj in originals}

        class_: int
        x: float
        y: float
        z: float
        w: float
        l: float
        h: float
        rx: float
        ry: float
        rz: float

        copies = []
        for class_, x, y, z, w, l, h, rx, ry, rz in self.c.execute(
            "SELECT class_, x, y, z, w, l, h, rx, ry, rz FROM bboxes_full WHERE imgnr=?", str(imgnr)
        ):
            _og_obj = name2obj[self.num2name[class_]]
            new_obj = _og_obj.copy()
            new_obj.data = _og_obj.data.copy()
            new_obj.location = np.array((x,y,z)) * (spawnbox.dimensions / 2) + spawnbox.location
            new_obj.dimensions = (w, l, h)
            new_obj.rotation_euler = np.array((rx, ry, rz)) * 2 * np.pi

            new_obj.name += tag
            new_obj.show_bounds = True
            new_obj.show_name = True

            # Link to target collection
            self.target_collection.objects.link(new_obj)            
            copies.append(new_obj)

        return copies

    def clear(self) -> None:
        """
        Clears objects in target collection
        """
        utils.rm_collection(self.target_collection)


if __name__ == "__main__":
    DIR = "nogit_gen"
    loader = Sceneloader(DIR)
    loader.reconstruct_scene(0)
