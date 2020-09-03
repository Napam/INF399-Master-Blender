import bpy
from types import FunctionType
from typing import Callable
import pathlib

def unused_remover(block):
    '''
    Remove all unused in block
    
    Parameters
    -----------
    block: for example bpy.data.materials and bpy.data.meshes
    '''
    for obj in block:
        if obj.users == 0:
            block.remove(obj)

def select_collection(collection: bpy.types.Collection, deselect_first: bool=True) -> list:
    '''
    Select all objects in collection and returns them in a list

    Parameters
    ----------
    collection: collection object

    deselect_first: whether to deselect everything else first or not
    '''
    if deselect_first:
        bpy.ops.object.select_all(action='DESELECT')

    for obj in collection.all_objects:
        obj.select_set(True)
    
    return list(collection.all_objects)

def rm_collection(collection: bpy.types.Collection, materials: bool=True, meshes: bool=True, 
                  lights: bool=True):
    '''Remove objects in given collection and unused materials, meshes and lights'''
    [bpy.data.objects.remove(c, do_unlink=True) for c in collection.objects]    
    if materials: unused_remover(bpy.data.materials)
    if meshes: unused_remover(bpy.data.meshes)
    if lights: unused_remover(bpy.data.lights)

def capture_camera(fileformat: str=None, filepath: str=None):
    '''
    Renders image through camera anad dumps to filepath
    '''
    if fileformat is None:
        fileformat = 'PNG'
    if filepath is None:
        filepath = str(pathlib.Path(bpy.data.filepath).parent / 'renders/image')

    bpy.context.scene.render.image_settings.file_format = fileformat
    bpy.context.scene.render.filepath = filepath
    print('Rendering and saving')
    return bpy.ops.render.render(write_still=True)

def add_object(add: Callable, collection: bpy.types.Collection=None, modifier=None):
    '''
    Adds object using built in add methods
    
    add: add method (for example bpy.ops.mesh.primitive_cube_add) or the return value of 
         add method

    modifer: If modifier is specified it will pass on the 
             newly created object to the modifier (a function) 

    collection: If collection is specified it will link
                the newly created object to collection 
    '''
    # bpy.ops methods returns a set
    if not type(add) == set: add(*args, **kwargs)
    curr = bpy.context.active_object
    if not modifier == None: modifier(curr)
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
