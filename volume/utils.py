"""
Module containing utility functions for scripting environment in Blender 2.83 LTS (but may work
with other versions as well).

Contains functions for 

- Removing objects 
- Adding primitive objects
- Selecting objects
- And more similar utilities

Written by Naphat Amundsen
"""

import bpy
from typing import Callable, Optional, Union, Tuple, Any
import config as cng
import argparse
import sys
import functools
import os
import re

RE_ANSI = re.compile(r"\x1b\[[;\d]*[A-Za-z]")  # Taken from tqdm source code


def print_boxed(*args: Tuple[str], end="\n") -> None:
    """
    Encloses strings in a big box for extra visibility

    I'm a bit extra sometimes u know?
    """

    width: int = max(max(map(len, args)) + 2 * len(cng.BOXED_STR_SIDE) + 2, cng.HIGHLIGHT_MIN_WIDTH)

    print(f"{'':{cng.BOXED_SYMBOL_TOP}^{width}}")
    for info in args:
        # Adjust string length to accomdodate for ansi escape sequences
        ansilen = len("".join(RE_ANSI.findall(info)))
        print(
            f"{cng.BOXED_STR_SIDE}"
            f"{info:^{width-2*len(cng.BOXED_STR_SIDE)+ansilen}}"
            f"{cng.BOXED_STR_SIDE}"
        )
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


def rm_directory(directory: str, doublecheck: bool = False) -> None:
    """Removes the given directory"""
    if doublecheck:
        input(f"Are you sure you want to remove directory: '{directory}'?")
    print(f"Initalizing clearing process of directory '{yellow(directory)}'")
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
            print(f"{directory} not found, doing nothing")

    shutil.rmtree(directory, ignore_errors=False, onerror=handleRemoveReadonly)


def yellow(string: str):
    return f"\033[33m{string}\033[0m"


def red(string: str):
    return f"\033[31m{string}\033[0m"


class ArgumentParserForBlender(argparse.ArgumentParser):
    """
    This class is identical to its superclass, except for the parse_args
    method (see docstring). It resolves the ambiguity generated when calling
    Blender from the CLI with a python script, and both Blender and the script
    have arguments. E.g., the following call will make Blender crash because
    it will try to process the script's -a and -b flags:
    >>> blender --python my_script.py -a 1 -b 2

    To bypass this issue this class uses the fact that Blender will ignore all
    arguments given after a double-dash ('--'). The approach is that all
    arguments before '--' go to Blender, arguments after go to the script.
    The following calls work fine:
    >>> blender --python my_script.py -- -a 1 -b 2
    >>> blender --python my_script.py --
    """

    def _get_argv_after_doubledash(self):
        """
        Given the sys.argv as a list of strings, this method returns the
        sublist right after the '--' element (if present, otherwise returns
        an empty list).
        """
        try:
            idx = sys.argv.index("--")
            return sys.argv[idx + 1 :]  # the list after '--'
        except ValueError as e:  # '--' not in the list:
            return []

    # overrides superclass
    def parse_args(self):
        """
        This method is expected to behave identically as in the superclass,
        except that the sys.argv list will be pre-processed using
        _get_argv_after_doubledash before. See the docstring of the class for
        usage examples and details.
        """
        return super().parse_args(args=self._get_argv_after_doubledash())


def unused_remover(block) -> None:
    """
    Remove all unused in block

    Parameters
    -----------
    block: for example bpy.data.materials and bpy.data.meshes
    """
    for obj in block:
        if obj.users == 0:
            block.remove(obj)


def select_collection(
    collection: Union[bpy.types.Collection, str], deselect_first: bool = True
) -> list:
    """
    Select all objects in collection and returns them in a list

    Parameters
    ----------
    collection: Union[bpy.types.Collection, str]
        if string, then get collection by bpy.data.collections[collection]
    form string

    deselect_first: whether to deselect everything else first or not
    """
    if isinstance(collection, str):
        collection: bpy.types.Collection = bpy.data.collections[collection]

    if deselect_first:
        deselect_all()

    for obj in collection.all_objects:
        obj.select_set(True)

    return list(collection.all_objects)


def deselect_all() -> None:
    """Deselects everything"""
    # Deselect everything first
    bpy.ops.object.select_all(action="DESELECT")


def rm_collection(
    collection: Union[bpy.types.Collection, str],
    materials: bool = True,
    meshes: bool = True,
    lights: bool = True,
) -> None:
    """Remove objects in given collection and unused materials, meshes and lights

    Parameters
    ----------
    collection : Union[bpy.types.Collection, str]
        if string, then get collection by bpy.data.collections[collection]
    materials : bool, optional
        remove materials bound to objects, by default True
    meshes : bool, optional
        remove meshes bound to objects, by default True
    lights : bool, optional
        remove lights bound to objeects, by default True
    """
    if isinstance(collection, str):
        collection: bpy.types.Collection = bpy.data.collections[collection]

    for obj in collection.objects:
        bpy.data.objects.remove(obj, do_unlink=True)

    # IMPORTANT: Must be removed in this order to get expected behavior. See:
    # https://blender.stackexchange.com/questions/102025/how-to-prevent-memory-leakage-in-blender
    # Basically, meshes "uses" materials and so on ...
    if meshes:
        unused_remover(bpy.data.meshes)
    if materials:
        unused_remover(bpy.data.materials)
    if lights:
        unused_remover(bpy.data.lights)


def render_and_save(filepath: str, fileformat: Optional[str] = None) -> dict:
    """Captures image from camera and dumps to file
    Will automatically add fileformat and camera suffixed to filename,
    e.g. filepath = img3, fileformat: PNG -> img3_C_TOP.png

    Parameters
    ----------
    filepath : str
        filepath
    fileformat : Optional[str], optional
        Must be supported types by blender, by default PNG

    Returns
    -------
    dict :
        Blender return value from bpy.ops.render.render(write_still=True)
    """
    if fileformat is None:
        fileformat = cng.DEFAULT_FILEFORMAT

    # Set values in Blender environment
    bpy.context.scene.render.image_settings.file_format = fileformat
    bpy.context.scene.render.filepath = filepath
    return bpy.ops.render.render(write_still=True)


def clear_all_node_links(material: bpy.types.Material):
    """
    Clears all linkes between shader nodes in given material
    """
    for link in material.node_tree.links:
        material.node_tree.links.remove(link)


def disable_all_render_views():
    """
    Disables all cameras in
    Properties pane -> Output properties -> Stereoscopy -> Multi-View
    """
    for camera in bpy.context.scene.render.views:
        camera.use = False


def add_object(
    add: Callable, collection: bpy.types.Collection = None, modifier=None, *args, **kwargs
) -> None:
    """
    Adds object using built in add methods

    add: add method (for example bpy.ops.mesh.primitive_cube_add) or the return value of
         add method

    modifer: If modifier is specified it will pass on the
             newly created object to the modifier (a function)

    collection: If collection is specified it will link
                the newly created object to collection
    """

    # bpy.ops methods returns a set
    if not type(add) == set:
        add(*args, **kwargs)
    curr = bpy.context.active_object
    if not modifier == None:
        modifier(curr)
    if not collection == None:
        bpy.ops.collection.objects_remove_all()
        collection.objects.link(curr)
    return curr


def add_primitive_plane(collection: bpy.types.Collection):
    return add_object(bpy.ops.mesh.primitive_plane_add(), collection)


def add_primitive_cube(collection: bpy.types.Collection):
    return add_object(bpy.ops.mesh.primitive_cube_add(), collection)


def add_primitive_circle(collection: bpy.types.Collection):
    return add_object(bpy.ops.mesh.primitive_circle_add(), collection)


def add_primitive_uv_sphere(collection: bpy.types.Collection):
    return add_object(bpy.ops.mesh.primitive_uv_sphere_add(), collection)


def add_primitive_ico_sphere(collection: bpy.types.Collection):
    return add_object(bpy.ops.mesh.primitive_ico_sphere_add(), collection)


def add_primitive_cylinder(collection: bpy.types.Collection):
    return add_object(bpy.ops.mesh.primitive_cylinder_add(), collection)


def add_primitive_cone(collection: bpy.types.Collection):
    return add_object(bpy.ops.mesh.primitive_cone_add(), collection)


def add_primitive_torus(collection: bpy.types.Collection):
    return add_object(bpy.ops.mesh.primitive_torus_add(), collection)


def add_primitive_grid(collection: bpy.types.Collection):
    return add_object(bpy.ops.mesh.primitive_grid_add(), collection)


def add_primitive_monkey(collection: bpy.types.Collection):
    return add_object(bpy.ops.mesh.primitive_monkey_add(), collection)
