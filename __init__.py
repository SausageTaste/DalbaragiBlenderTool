import importlib

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator

from . import py_module


bl_info = {
    "name": "Dalbaragi Asset Exporter",
    "author": "Sungmin Woo",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "File > Export > Dalbaragi Tools",
    "description": "Export a model file for Dalbargi engine.",
    "warning": "Under development.",
    "wiki_url": "https://github.com/SausageTaste/DalbaragiBlenderTool",
    "category": "Import-Export",
    "tracker_url": "https://github.com/SausageTaste/DalbaragiBlenderTool/issues"
}


class EmportDalModel(Operator, ExportHelper):
    """Export binary map file for Dalbargi engine."""

    bl_idname = "dal_op_export_model.dmd"
    bl_label = "Export model as DMD"

    filename_ext = ".dmd"

    def execute(self, context):
        py_module.blender_interface.parse_blender_scene.parse(bpy.data.collections)

        self.report({'INFO'}, "Export done: dmd")
        return {'FINISHED'}


class DalExportSubMenu(bpy.types.Menu):
    bl_idname = "dal_menu_export"
    bl_label = "Dalbaragi Export Tools"

    def draw(self, context):
        self.layout.operator(EmportDalModel.bl_idname, text="Model (.dmd)")


def menu_func_export(self, context):
    self.layout.menu(DalExportSubMenu.bl_idname)

def register():
    importlib.reload(py_module)
    py_module.refresh_import()

    bpy.utils.register_class(EmportDalModel)
    bpy.utils.register_class(DalExportSubMenu)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(EmportDalModel)
    bpy.utils.unregister_class(DalExportSubMenu)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
    bpy.ops.export_model.dmd('INVOKE_DEFAULT')
