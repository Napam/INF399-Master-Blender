import numpy as np
import sys
import os
from PIL import Image, ImageFilter, ImageDraw
from math import floor, ceil

def initialize(backgrounds_dir, classes_dir):
	# Loading data
	backgrounds = os.listdir(backgrounds_dir)
	class_names = os.listdir(classes_dir)
	classes_dict = {class_name: idx for class_name, idx in zip(class_names, range(1, 1 + len(class_names)))}
	bgs = [os.path.join(backgrounds_dir,b).replace("\\","/") for b in backgrounds]
	objs = {}
	print("\nTreating background as 0")
	for key in classes_dict.keys():
		print('Loading ' + key + ' as ' + str(classes_dict[key]))
		objects = os.listdir(os.path.join(classes_dir,key).replace("\\","/"))
		objs[key] = [os.path.join(classes_dir, key, obj).replace("\\","/") for obj in objects]
	print("--------------------------------------------------------------------------------")
	return objs, classes_dict, bgs

def find_top_bottom_bounding_box(cutout):
	M = np.size(cutout, 0)
	N = np.size(cutout, 1)
	cutout_mask = cutout[0:,0:,3]
	if np.sum(cutout_mask[0,0:]) > 0:
		cutout = np.concatenate((np.uint8(np.zeros((1, N, 4))), cutout), axis=0)
		M += 1
	if np.sum(cutout_mask[-1,0:]) > 0:
		cutout = np.concatenate((cutout, np.uint8(np.zeros((1, N, 4)))), axis=0)
		M += 1
	cutout_mask = cutout[0:,0:,3]
	top_bounding_box = -1
	bottom_bounding_box = 0
	mask_is_1_rows = []
	for m in range(M):
		mask_is_1_current_row = False
		for n in range(N):
			if cutout_mask[m,n] > 0:
				if top_bounding_box < 0:
					top_bounding_box = m - 1
				if mask_is_1_current_row == False:
					mask_is_1_current_row = True
		mask_is_1_rows.append(mask_is_1_current_row)
	bottom_bounding_box = np.nonzero(mask_is_1_rows)[0][-1] + 1
	return cutout, top_bounding_box, bottom_bounding_box

def refine_cutout(cutout, classe_idx):
	cutout = np.array(cutout)
	cutout, top_bounding_box, bottom_bounding_box = find_top_bottom_bounding_box(cutout)
	cutout_rotated = np.rot90(cutout, k=1, axes=(1,0))
	cutout_rotated, left_bounding_box, right_bounding_box = find_top_bottom_bounding_box(cutout_rotated)
	cutout = np.rot90(cutout_rotated, k=1, axes=(0,1))
	cutout = cutout[top_bounding_box:bottom_bounding_box+1, left_bounding_box:right_bounding_box+1, 0:]
	cutout_mask = cutout[0:, 0:, 3]
	one_mat = np.ones((np.size(cutout_mask, 0), np.size(cutout_mask, 1)))
	cutout_mask = (cutout_mask > 0).astype(int) * classe_idx
	cutout_mask = Image.fromarray(np.uint8(cutout_mask))
	cutout = Image.fromarray(np.uint8(cutout))
	return cutout, cutout_mask

# Simulate an image
def mkimage(filename, objs, classes_dict, bgs, output_dir, maxobjs=6, seed=None, single=False):
	seeded_random = np.random.RandomState(seed)
	im = Image.open(seeded_random.choice(bgs))
	imx, imy = im.size
	# Careful here ! Row first in numpy, col first in PIL:
	im_mask = np.zeros((imy, imx))
	im_mask = Image.fromarray(np.uint8(im_mask))
	cls0 = seeded_random.choice(list(classes_dict.keys()))
	texts_folder = os.path.join(output_dir, "texts").replace("\\","/")
	if not os.path.exists(texts_folder):
		os.makedirs(texts_folder)
	with open(os.path.join(texts_folder, filename + '.txt').replace("\\","/"),'w+') as f:
		# Number of fish follows a uniform distribution in [|1, maxobjs|]:
		gamma_num_objs = 1 + seeded_random.randint(maxobjs)
		for _ in range(gamma_num_objs):
			log = ""
			if single: 
				cls = cls0
			else: 
				cls = seeded_random.choice(list(classes_dict.keys()))
			obj = Image.open(seeded_random.choice(objs[cls]))
			# Scale factor follows a uniform distribution in {0.8, 0.9, 1.0, 1.1, 1.2}:
			scale_factors = [0.8, 0.9, 1.0, 1.1, 1.2]
			uniform_scale_factor = seeded_random.choice(scale_factors)
			sizex, sizey = obj.size
			sizex = floor(uniform_scale_factor * sizex)
			sizey = floor(uniform_scale_factor * sizey)
			obj = obj.resize(size=(sizex, sizey), resample=Image.BILINEAR)
			# Rotation parameter follows a uniform distribution in {-135, -90, -45, 0, 45, 90, 135, 180}:
			rotations = [-135, -90, -45, 0, 45, 90, 135, 180]
			uniform_rotation = seeded_random.choice(rotations)
			obj = obj.rotate(angle=uniform_rotation, expand=True)
			obj, obj_mask = refine_cutout(obj, classe_idx=classes_dict[cls])
			sizex, sizey = obj.size
			startx = -floor(sizex / 2)
			starty = -floor(sizey / 2) 
			posx = seeded_random.randint(startx, imx + startx)
			posy = seeded_random.randint(starty, imy + starty)
			im.paste(obj, (posx, posy), obj)
			im_mask.paste(obj_mask, (posx, posy), obj)
			obj.close()
			### For testing:
			# draw = ImageDraw.Draw(im)
			# draw.line([(posx, posy), (posx+sizex-1, posy)]  , fill=(255, 0, 0), width=1)
			# draw.line([(posx+sizex-1, posy), (posx+sizex-1, posy+sizey-1)]  , fill=(255, 0, 0), width=1)
			# draw.line([(posx+sizex-1, posy+sizey-1), (posx, posy+sizey-1)]  , fill=(255, 0, 0), width=1)
			# draw.line([(posx, posy+sizey-1), (posx, posy)]  , fill=(255, 0, 0), width=1)
			log += cls + " " + str(classes_dict[cls]) + " " + str(posx) + " " + str(posy) + " " + str(sizex) + " " + str(sizey)
			f.write(log + "\n")
	images_folder = os.path.join(output_dir, "images").replace("\\","/")
	if not os.path.exists(images_folder):
		os.makedirs(images_folder)
	im.save(os.path.join(images_folder, filename + '.png').replace("\\","/"))
	masks_folder = os.path.join(output_dir, "masks").replace("\\","/")
	if not os.path.exists(masks_folder):
		os.makedirs(masks_folder)
	im_mask.save(os.path.join(masks_folder, filename + '_mask.png').replace("\\","/"))
	im.close()
	im_mask.close()

