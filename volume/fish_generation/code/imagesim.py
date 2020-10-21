import numpy as np
seed = None
seed = 666
np.random.seed(seed)
import sys
import os
import argparse
from tqdm import tqdm
from math import ceil
from generate import mkimage, initialize

p = argparse.ArgumentParser(description='Generate images from background and elements.')
p.add_argument('-b', '--backgrounds'
			   , help='directory containing background images')
p.add_argument('-c', '--classes'
			   , help='directory containing element images, one subdirectory per class')
p.add_argument('-s', '--single', action='store_true'
			   , help='generate images containing one class elements only')
p.add_argument('-n'
			   , help='number of images to generate')
p.add_argument('-e'
			   , help='max number of elements per image')
p.add_argument('-o'
			   , help='directory to store generated images')

args = p.parse_args()
print(args)

if not os.path.exists(args.o):
	os.makedirs(args.o)

objects, classes_dict, backgrounds = initialize(backgrounds_dir=args.backgrounds, classes_dir=args.classes)

n = int(args.n)
assert(n > 0)

if args.e == None: e=6
else: e=int(args.e)
assert(e > 0)

split_dict = {"train": ceil(0.8 * n), "val": ceil(0.1 * n), "test": ceil(0.1 * n)}
seeds_dict = {"train": np.random.randint(10000000, size=split_dict["train"]), 
			  "val": np.random.randint(10000000, size=split_dict["val"]), 
			  "test": np.random.randint(10000000, size=split_dict["test"])}

for key in split_dict.keys():
	print("Generating " + key + " dataset")
	num_images = split_dict[key]
	output_dir = os.path.join(args.o, key).replace("\\","/")
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	for i in tqdm(range(num_images)):
		mosaic_name = key + "_mosaic_" + str(i)
		mkimage(mosaic_name, objects, classes_dict, backgrounds, 
				output_dir, maxobjs=e, seed=seeds_dict[key][i], single=args.single)
	print("Done")

	
