import importlib

from . import parse_blender_scene


def refresh_import():
    importlib.reload(parse_blender_scene)
