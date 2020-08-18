import bpy 
import numpy as np 
from pprint import pprint

Ctn = bpy.data.collections['CNT1']
Ctn_LIGHTS = bpy.data.collections['LIGHTS']
Objs = Ctn.objects
Mats = bpy.data.materials
Meshes = bpy.data.meshes
Lights = bpy.data.lights
Scene = bpy.data.scenes['Scene']
C = bpy.context
    
def getlocs(collection):
    return [obj.location.copy() for obj in collection.objects]

def getscales(collection):
    return [obj.scale.copy() for obj in collection.objects]

def setlocs(collection, locs):
    for obj, loc in zip(collection.objects, locs):
        obj.location = loc

def setscales(collection, scales):
    for obj, scale in zip(collection.objects, scales):
        obj.scale = scale
        
def reset_anime():
    pass

def animate(collection, original_locs, original_scales):
    start = 0
    end = 400
    step = 5 
    frame_indices = np.arange(start+step, end, step)
    n_frames = len(frame_indices)
    print(frame_indices)
    
    print(f'Setting {n_frames} frames')
    C.scene.frame_set(start)
    for obj in collection.objects:
        obj.keyframe_insert(data_path='location')
        obj.keyframe_insert(data_path='scale')
    
    amp = 0.5
    scalings = np.sin(np.linspace(0,8*np.pi,n_frames))
    for i, frame in enumerate(frame_indices):
        # Set current time frame
        C.scene.frame_set(frame)
        for obj, loc, scale in zip(collection.objects, original_locs, original_scales):
            obj.location = loc*scalings[i]*np.random.uniform(0.9,1.1,size=1)
            linear = obj.location.length/20
            obj.scale = np.full(3,linear*scale)
            # Update object position in time frame
            obj.keyframe_insert(data_path='location')
            obj.keyframe_insert(data_path='scale')        
    
    C.scene.frame_set(end)
    for obj in collection.objects:
        setlocs(Ctn, original_locs)
        setscales(Ctn, original_scales)
        obj.keyframe_insert(data_path='location')
        obj.keyframe_insert(data_path='scale')

def main():
    original_locs = getlocs(Ctn)
    original_scales = getscales(Ctn) 
    animate(Ctn, original_locs, original_scales)  
    

if __name__ == '__main__':
    main()