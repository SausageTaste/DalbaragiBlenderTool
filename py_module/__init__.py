import importlib

from . import blender_interface
from . import intermediate_data


def refresh_import():
    importlib.reload(intermediate_data)
    intermediate_data.refresh_import()

    importlib.reload(blender_interface)
    blender_interface.refresh_import()
