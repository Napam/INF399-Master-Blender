import bpy
import os
import sys
import numpy as np 
from tqdm import tqdm

# Just set collection, objects in collection, scene and context as global variables
Ctn = bpy.data.collections['CNT1']
Objs = Ctn.objects
Mats = bpy.data.materials
Meshes = bpy.data.meshes
Lights = bpy.data.lights
Scene = bpy.data.scenes['Scene']
C = bpy.context

def unused_remover(block):
    '''Remove all unused in block'''
    for obj in block:
        if obj.users == 0:
            block.remove(obj)

def rm(collection):
    '''Remove objects'''
    [bpy.data.objects.remove(c, do_unlink=True) for c in collection.objects]    
    unused_remover(Mats)
    unused_remover(Meshes)
    unused_remover(Lights)

def add_box_grid():        
    n = 5
    extent = 20
    xspace = np.linspace(-extent,extent,n)
    yspace = np.linspace(-extent,extent,n)
    zspace = np.linspace(-extent,extent,n)
    
    X, Y, Z = np.meshgrid(xspace, yspace, zspace)
    locs = np.array([X.ravel(), Y.ravel(), Z.ravel()]).T
    scale = np.full(3, 4)
    
    print(f'Generating {len(locs)} objects:')
    for i, loc in tqdm(enumerate(locs)):
         # Add the thing
         bpy.ops.mesh.primitive_cube_add(location=loc)
         # Get object reference
         curr = C.active_object
         
         ### Do things here ###
         gridindex = np.unravel_index(i, shape=(n,n,n))
         curr.scale = scale
         curr.name = f'Cube{gridindex}'
         mat = bpy.data.materials.new(name=f'Material{gridindex}')
         mat.diffuse_color = np.random.rand(4)
         curr.data.materials.append(mat)
         ######################
         
         # Unlink active object from wherever it was linked to
         bpy.ops.collection.objects_remove_all()
         # Link to target collection
         Ctn.objects.link(curr)
        
    print('')

def add_sun():
    val = 50
    locs = [
        (0,0,val),
        (0,0,-val),
        (-val,0,0),
        (val,0,0),
        (0,val,0),
        (0,-val,0),
    ]
    
    for loc in locs:
        bpy.ops.object.light_add(type='POINT', radius=1, location=loc)
        curr = C.active_object
        curr.data.energy = 7000
        curr.data.color = (1, 0.850543, 0.432107)

        
        # Unlink active object from wherever it was linked to
        bpy.ops.collection.objects_remove_all()
        # Link to target collection
        Ctn.objects.link(curr)

def main():            
    rm(Ctn)
    add_box_grid()
    add_sun()

def setup_environment():
    dir_ = os.path.dirname(bpy.data.filepath)
    if not dir_ in sys.path:
        sys.path.append(dir_)
            
if __name__ == '__main__':
    setup_environment()
    main()