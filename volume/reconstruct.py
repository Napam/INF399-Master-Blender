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

import pandas as pd

import bpy
import numpy as np
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


def check_default_fish_node_tree(material: bpy.types.Material):
    """
    Asserts if shader nodes of fish (originals) materals are as expected
    """
    checklist = {"Material Output": False, "Image Texture": False, "Glossy BSDF": False}
    for node in material.node_tree.nodes:
        assert node.name in checklist, f"Found unexpected node: {node.name}"
        checklist[node.name] = True

    assert all(checklist.values()), "Did not find all expected nodes"


def make_fish_colored_transparent(material: bpy.types.Material):
    assert isinstance(material, bpy.types.Material)
    material.use_nodes = True  # Enable node mode
    check_default_fish_node_tree(material)
    utils.clear_all_node_links(material)

    nodes, links = material.node_tree.nodes, material.node_tree.links
    out = nodes["Material Output"]
    img = nodes["Image Texture"]
    glossy = nodes["Glossy BSDF"]
    mix = nodes.new("ShaderNodeMixShader")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix.inputs["Fac"].default_value = cng.DEFAULT_MIXSHADER_FAC
    transparent.inputs["Color"].default_value = cng.DEFAULT_ALTER_COLOR  # R G B A
    glossy.inputs["Roughness"].default_value = 0.85

    links.new(input=glossy.inputs[0], output=img.outputs[0])  # Connect img colors to glossy color
    links.new(input=mix.inputs[2], output=transparent.outputs[0])  # Connect Transparent to mix
    links.new(input=mix.inputs[1], output=glossy.outputs[0])  # Connect Glossy to mix
    links.new(input=out.inputs[0], output=mix.outputs[0])  # Mix to out
    return material


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
        """
        Parameters
        ----------
        data_dir: Path to directory that has been generated by generate.py

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
        self.con = db.connect(
            f"file:{os.path.join(self.data_dir, cng.BBOX_DB_FILE)}?mode=ro", uri=True
        )
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

    def reconstruct_scene_from_db(
        self, imgnr: int, tag: str = "", alter_material: bool = False, spawnbox: Optional[str] = None
    ) -> None:
        """
        Create scene from imgnr

        This will not clear the existing target collection before setting up a new scene

        imgnr: int, imgnr found in sqlite3 database generated using generate.py

        tag: str, string to append to object name in Blender

        alter_material: Optional[bool], make fish green and transparent
                        (useful for comparing prediction and true labels)

        spawnbox: Optional[str], name of spawnbox object, will be used for reference
        """
        if spawnbox is None:
            spawnbox: str = cng.SPAWNBOX_OBJ

        spawnbox: bpy.types.Object = bpy.data.objects[spawnbox]

        originals: Tuple[bpy.types.Object] = tuple(self.src_collection.all_objects)
        name2obj: Dict[str, bpy.types.Object] = {obj.name: obj for obj in originals}

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
        for class_n_box in self.c.execute(
            "SELECT class_, x, y, z, w, l, h, rx, ry, rz FROM bboxes_full WHERE imgnr=?",
            (str(imgnr),),
        ):
            original_object = name2obj[self.num2name[class_n_box[0]]]
            new_object = self.reconstruct_object(
                original_object=original_object,
                pos_size_rot=class_n_box[1:],
                tag=tag,
                alter_material=alter_material,
                spawnbox=spawnbox,
            )
            copies.append(new_object)

        return copies

    def reconstruct_scene_from_df(
        self,
        df: pd.DataFrame,
        tag: str = "",
        alter_material: bool = False,
        spawnbox: Optional[str] = None,
    ) -> None:
        """
        Create scene from imgnr

        This will not clear the existing target collection before setting up a new scene

        imgnr: int, imgnr found in sqlite3 database generated using generate.py

        tag: str, string to append to object name in Blender

        alter_material: Optional[bool], make fish green and transparent
                        (useful for comparing prediction and true labels)

        spawnbox: Optional[str], name of spawnbox object, will be used for reference
        """
        if spawnbox is None:
            spawnbox: str = cng.SPAWNBOX_OBJ

        spawnbox: bpy.types.Object = bpy.data.objects[spawnbox]

        originals: Tuple[bpy.types.Object] = tuple(self.src_collection.all_objects)
        name2obj: Dict[str, bpy.types.Object] = {obj.name: obj for obj in originals}

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
        for class_n_box in df.values[:,1:]:
            original_object = name2obj[self.num2name[class_n_box[0]]]
            new_object = self.reconstruct_object(
                original_object=original_object,
                pos_size_rot=class_n_box[1:],
                tag=tag,
                alter_material=alter_material,
                spawnbox=spawnbox,
            )
            copies.append(new_object)

        return copies

    def reconstruct_object(
        self,
        original_object: bpy.types.Object,
        pos_size_rot: Tuple[float, float, float, float, float, float, float, float, float],
        tag: str = "",
        alter_material: bool = False,
        spawnbox: Optional[str] = None,
    ):
        """Recreate given blender object and its physical attributes (position, size and rotation)

        Parameters
        ----------
        original_object : bpy.types.Object
        box : Tuple[float, float, float, float, float, float, float, float, float]
              pos      size      rotation
            x, y, z,  w, l, h,  rx, ry, rz
        tag : str, optional
            nametag, by default ""
        alter_material : bool, optional
            turn objects green transparent, by default False
        spawnbox : Optional[str], optional
            Name of spawnbox, by default None

        Returns
        -------
        bpy.types.Object
            Possibly altered copy of given object
        """
        x, y, z, w, l, h, rx, ry, rz = pos_size_rot
        new_obj = original_object.copy()
        new_obj.data = original_object.data.copy()

        new_obj.location = np.array((x, y, z)) * (spawnbox.dimensions / 2) + spawnbox.location
        new_obj.dimensions = (w, l, h)
        new_obj.rotation_euler = np.array((rx, ry, rz)) * 2 * np.pi

        new_obj.name += tag
        new_obj.show_bounds = True
        new_obj.show_name = True

        if alter_material:
            # Assuming original_object has one material slot, the line below is the same as
            # new_obj.material_slots[0].material = _og_obj.active_material.copy()
            new_material = original_object.active_material.copy()
            new_material = make_fish_colored_transparent(new_material)
            new_obj.active_material = new_material

        # Link to target collection
        self.target_collection.objects.link(new_obj)
        return new_obj

    def clear(self) -> None:
        """
        Clears objects in target collection
        """
        utils.rm_collection(self.target_collection)


if __name__ == "__main__":
    DIR = "nogit_gen"
    loader = Sceneloader(DIR)
    loader.reconstruct_scene_from_db(0)
