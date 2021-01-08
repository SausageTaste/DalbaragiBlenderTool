import importlib

from . import linear_algebra
from . import data_struct


def refresh_import():
    importlib.reload(linear_algebra)
    importlib.reload(data_struct)
