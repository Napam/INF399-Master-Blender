"""
Used to specifically make LaTeX tables 
"""
import sys
import bpy
import pathlib
import os

dir_ = os.path.dirname(bpy.data.filepath)
if dir_ not in sys.path:
    sys.path.append(dir_)
dirpath = pathlib.Path(dir_)

import pandas as pd
import numpy as np
import blender_config as cng
import blender_utils as utils


def originalsCollectionAttributes():
    fishs = utils.select_collection(cng.SRC_CLTN)

    df = pd.DataFrame(
        {
            "Species": (f.name for f in fishs),
            "$s_x$": (f.dimensions[0] for f in fishs),
            "$s_y$": (f.dimensions[1] for f in fishs),
            "$s_z$": (f.dimensions[2] for f in fishs),
        }
    )

    latex = df.to_latex(index=False, float_format=lambda x: f"{x:.4f}", escape=False)
    print(latex)
    return latex


def lightsAttributes():
    lights = utils.select_collection("Lights")
    lights = tuple(filter(lambda x: "lightpoint_" in x.name, lights))

    # assert isinstance(lights[0].data, bpy.types.Light)

    df = pd.DataFrame(
        {
            "name": (light.name for light in lights),
            "$x$": (light.location[0] for light in lights),
            "$y$": (light.location[1] for light in lights),
            "$z$": (light.location[2] for light in lights),
            "$r$": (light.data.color[0] for light in lights),
            "$g$": (light.data.color[1] for light in lights),
            "$b$": (light.data.color[2] for light in lights),
            "power": (light.data.energy for light in lights),
            "radius": (light.data.shadow_soft_size for light in lights),
        }
    )

    latex = df.to_latex(index=False, float_format=lambda x: f"{round(x,4)}", escape=False)
    print(latex)
    return latex


def cameraAttributes():
    cameras = utils.select_collection("Cameras")
    # cameras = tuple(filter(lambda x: not "_C" in x.name, cameras))

    # assert isinstance(lights[0].data, bpy.types.Light)

    df = pd.DataFrame(
        {
            "name": (cam.name for cam in cameras),
            "$x$": (cam.location[0] for cam in cameras),
            "$y$": (cam.location[1] for cam in cameras),
            "$z$": (cam.location[2] for cam in cameras),
            "$\theta_x$": (cam.rotation_euler[0] for cam in cameras),
            "$\theta_y$": (cam.rotation_euler[1] for cam in cameras),
            "$\theta_z$": (cam.rotation_euler[2] for cam in cameras),
            "fov": (cam.data.angle for cam in cameras),
        }
    )

    latex = df.to_latex(index=False, float_format=lambda x: f"{round(x,4)}", escape=False)
    print(latex)
    return latex


cameraAttributes()
