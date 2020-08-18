# image-simulator.rar
Just a copy of my image-simulator git repository forked from ketils image-simulator:
https://github.com/ToreAad/image-simulator
My inf368 report is:
https://github.com/ToreAad/image-simulator/blob/master/HM_train_fish_2404.ipynb
It contains most of the results.

To generate synthetic images run:
python imagesim.py -n 10 -b "../source_data/Backgrounds" -c "../source_data/Classes" -o "../simulated_data" 
This is the same as Ketils original repository. Obviously you would have to unpack one of the source_data_*.rar archives for the command to make sense.

# source_data_from_ketil.rar
This is the original fish cut outs that Ketil gave us.

# source_data_from_blender.rar
This is synthetic fish cut outs I generated with blender.

# CycleGAN-Keras.rar
I tried to use cycle-gan to transform the composite images I made with image-simuluator using the synthetic source data to be indistinguishable from those made by using ketils source data. Could be intersting way to bridge any gaps between the real and the syntethic data so I add it here.

# blender_files.rar
This archive contains the blender project I used to generate the synthetic cut outs. I used blender 2.78, but the most recent version is 2.83 and it is a lot more user friendly. I would use the most recent version of blender, but there might be some small issues upgrading my project to this newer version. My python script seems a bit funny... 

Now, to get started:
1. Install blender. 
2. Watch a getting started tutorial. Blender is quite a heavy package to learn, so it is worth finding a tutorial or two on youtube to get the basic ideas.
3. unzip blender_files.rar
4. Start blender with the console open. Add -con to the startup command. This keeps the console window open, when you print to stdout in your python scripts it will be printed in this external console.
5. In blender open .blender_files/cod/animate_fishes.blend
6. After the project loads press f12, hopefully a fish picture will render.

The basic workflow I used when I generated the synthetic fish images was this:
1. Find some fish models from the internet.
2. Load them into blender.
3. Apply some deformations to them.
4. Run a python script that randomly rotated, translated, scaled and applied deformations to the fish. Additionally it also changed the properties of the light sources in the scene. Each fish state is saved as a keyframe in the scene.
5. Render the whole scene and export each keyframe to a png in some output folder.
6. Run imagemagick to clip unused edges from the images.
See source_data_fromm_blender.rar for an example of output from this workflow.

See .blender_files/cod/animate.py for the script I used to randomize the fish properties. It almost works in blender 2.83, but it seems like it is having some problems with light intensites and some weird translation of the origin of the herring fish... Unsure what the problem is and I didnt really look into it. Anyways it should be plenty to get started...

# Getting models of fishes:
I just found them online from this source https://sketchfab.com/amyscottmurray . If you wanted to make your own models maybe consider agisoft photoscan. I have previously been impressed with the models it generates.

