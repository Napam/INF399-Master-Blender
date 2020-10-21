import bpy
import os
import sys
import numpy as np 
from tqdm import tqdm

# Just set collection, objects in collection, scene and context as global variables
Ctn = bpy.data.collections['CNT1']
Ctn_LIGHTS = bpy.data.collections['LIGHTS']
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
    
def add_spheres(collection):
    R = 20
    N = 20
    pad = 0.05
    thetas = np.linspace(0, 2*np.pi, N)[:-1]
    phis = np.linspace(0+pad, 2*np.pi-pad, int(N*1.5))[:-1]

    T, P = np.meshgrid(thetas, phis)
    thetas, phis = np.array([T.ravel(), P.ravel()])

    R_ = R*np.sin(phis)
    locs = np.array([R_*np.cos(thetas), R_*np.sin(thetas), R*np.cos(phis)]).T
    
    scale = np.full(3,2)
    sinphis = np.sin(phis)
    print(f'Adding {len(locs)} cubes:')
    for i, loc in tqdm(enumerate(locs)):
        bpy.ops.mesh.primitive_cube_add(location=loc)

        # Get object reference
        curr = C.active_object
        
        ### Do things here ###
        gridindex = i
        curr.scale = np.full(3, 1.5*sinphis[i])
        curr.name = f'Cube{gridindex}'
        mat = bpy.data.materials.new(name=f'Material{gridindex}')
        mat.diffuse_color = np.random.rand(4)
        curr.data.materials.append(mat)
        curr.rotation_euler = (0.0, phis[i], thetas[i])
        ######################
        
        # Unlink active object from wherever it was linked to
        bpy.ops.collection.objects_remove_all()
        # Link to target collection
        collection.objects.link(curr)

def add_lights(collection):
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
        curr.data.energy = 9000
        curr.data.color = (1, 0.850543, 0.432107)
        
        # Unlink active object from wherever it was linked to
        bpy.ops.collection.objects_remove_all()
        # Link to target collection
        collection.objects.link(curr)

def main():            
    rm(Ctn)
    rm(Ctn_LIGHTS)
    add_spheres(Ctn)
    add_lights(Ctn_LIGHTS)

def setup_environment():
    dir_ = os.path.dirname(bpy.data.filepath)
    if not dir_ in sys.path:
        sys.path.append(dir_)
            
if __name__ == '__main__':
    setup_environment()
    main()