'''
Module for convenience when scripting in Blender

Adds common use variables into environment

Written by Naphat Amundsen
'''

import bpy
import sys
import os
import pathlib

def insert_into_namespace(items: dict, namespace: dict, verbose=False):
    '''
    Inserts variable given name and value into name_space
    
    Defaults to global namespace if name_space is not specified
    '''    
    namespace.update(items)
    if verbose:
        for key, val in items.items():
            print(f'Inserted {key} in given namespace')

def add_local_path():
    '''
    Enables relative (to blender file) imports

    This function needs to be copy pasted into the blender script
    '''
    dir_ = os.path.dirname(bpy.data.filepath)
    if not dir_ in sys.path:
        sys.path.append(dir_)

def inject_vars(namespace: dict, verbose=True):
    '''Injects variables such as context, scene, materials etc into namespace'''
    # Injects context and scene into global namespace
    insert_into_namespace(dict(
        C=bpy.context,
        D=bpy.data,
        SCENE=bpy.data.scenes['Scene'],
    ), namespace=namespace, verbose=verbose)

    # Injects materials, meshes and lights into global namespace 
    insert_into_namespace(dict(
        MATERIALS=bpy.data.materials,
        MESHES=bpy.data.meshes,
        LIGHTS=bpy.data.lights        
    ), namespace=namespace, verbose=verbose)
    
    # Adds materials, meshes and lights to global namespace
    # Add collections into global namespace. 
    # Will be assigned same names as collection names
    insert_into_namespace(
        {name:c for name, c in namespace['SCENE'].collection.children.items()},
        namespace=namespace,
        verbose=verbose
    )

def init(namespace: dict, verbose=True):
    '''
    Initializes Python environment in Blender

    namespace: globals()
    bpy_module: bpy 
    '''
    inject_vars(namespace, verbose)

if __name__ == '__main__':
    pass