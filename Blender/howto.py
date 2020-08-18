# To get collections 
bpy.data.collections
# Get objects in a collection 
bpy.data.collections.objects
# To get context
bpy.context
# Get active object
bpy.context.active_object
# Get scene
bpy.data.scenes['Scene']
# When adding physics (for example rigidbody) you have to
scene.rigidbody_world.collection.objects.link(obj)

# Setup
Ctn = bpy.data.collections['CollectionName']
Objs = Ctn.objects
Scene = bpy.data.scenes['SceneName']
C = bpy.context

# Copy light (to have a master light to control everything)
for y in np.linspace(-30,30,5):
    master_light = Ctn.objects['point_master']
    obj = master_light.copy()
    obj.location = (8,y,2)
    Ctn.objects.link(obj)

# Remove all in collection
[bpy.data.objects.remove(c) for c in collection.objects]

# Add random balls in collection
scale = np.full(3, 0.3)
locs = (np.random.rand(20,3)-0.5)*3
for i, loc in enumerate(locs):
    # Doing this will automatically set the C.active_object pointer to 
    # the newly made thing 
    bpy.ops.mesh.primitive_uv_sphere_add(
    location=loc, 
    enter_editmode=False
    )
    # Get current active object 
    obj = C.active_object
    obj.scale = scale
    # Unlink active object from wherever it was linked to
    bpy.ops.collection.objects_remove_all()
    # Link to target collection
    collection.objects.link(obj)

# Removes shit
def unused_remover(block):
    for obj in block:
        if obj.users == 0:
            block.remove(obj)

def rm(collection):
    '''Remove objects'''
    [bpy.data.objects.remove(c, do_unlink=True) for c in collection.objects]    
    unused_remover(Mats)
    unused_remover(Meshes)
    unused_remover(Lights)

# Enables relative imports
def setup_environment():
    dir_ = os.path.dirname(bpy.data.filepath)
    if not dir_ in sys.path:
        sys.path.append(dir_)