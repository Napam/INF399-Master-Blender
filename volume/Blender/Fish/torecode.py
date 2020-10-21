import bpy
import numpy as np

scene = bpy.context.scene

fish_names = ['herring', 'mackerel']
shapekey_names = ['SimpleDeform','SimpleDeform.001','SimpleDeform.002','SimpleDeform.003']

def randomizeObjectInCamera(start, end, name, others):
    fish = scene.objects[name]
    for i in range(start, end):
        print(name, i)
        scene.frame_set(i)
        new_scale = max(min(0.9*(1 + ( np.random.random() - 0.5 )),1.1), 0.3)
        new_rx =  3.14159/2+(np.random.random()-0.5)*3.14159/2#np.random.random()*3.14159
        new_ry = (np.random.random()-0.5)*3.14159/3#3.14159
        new_rz = (np.random.random()-0.5)*3.14159/3#np.random.random()*3.14159
        for shapekey in shapekey_names:
            fish.data.shape_keys.key_blocks[shapekey].value = 0
            fish.data.shape_keys.key_blocks[shapekey].keyframe_insert("value",frame=i)
        
        new_key = np.random.choice(shapekey_names)
        new_val = np.random.random()
        fish.data.shape_keys.key_blocks[new_key].value = new_val
        fish.scale = (new_scale if np.random.random() > 0.95 else -new_scale, 
                      -new_scale if np.random.random() > 0.95 else new_scale,
                      -new_scale if np.random.random() > 0.95 else new_scale)
        fish.rotation_euler = (new_rx, new_ry, new_rz)
        fish.location = (0,0,0)
        
        fish.keyframe_insert(data_path="location", index=-1)
        fish.keyframe_insert(data_path="rotation_euler", index=-1)
        fish.keyframe_insert(data_path="scale", index=-1)
        fish.data.shape_keys.key_blocks[new_key].keyframe_insert("value",frame=i)
        
        for other_name in others:
            if other_name is name: continue
            other_fish = scene.objects[other_name]
            other_fish.location = (10,10,10)
            other_fish.keyframe_insert(data_path="location", index=-1)

lamp = scene.objects["Sun"]
for i in range(0, 20):
    print('lamp',i)
    scene.frame_set(i)
    lamp.data.node_tree.nodes['Emission'].inputs['Strength'].default_value = 400.0
    lamp.data.node_tree.nodes['Emission'].inputs['Strength'].keyframe_insert("default_value",frame=i)

randomizeObjectInCamera(0, 10, "herring", fish_names)
randomizeObjectInCamera(10, 20, "mackerel", fish_names)