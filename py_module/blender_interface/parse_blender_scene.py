from typing import List, Tuple, Optional

import bpy

from ..intermediate_data import data_struct
from ..intermediate_data import linear_algebra


BLENDER_OBJ_TYPE_MESH        = "MESH"
BLENDER_OBJ_TYPE_CURVE       = "CURVE"
BLENDER_OBJ_TYPE_SURFACE     = "SURFACE"
BLENDER_OBJ_TYPE_META        = "META"
BLENDER_OBJ_TYPE_FONT        = "FONT"
BLENDER_OBJ_TYPE_ARMATURE    = "ARMATURE"
BLENDER_OBJ_TYPE_LATTICE     = "LATTICE"
BLENDER_OBJ_TYPE_EMPTY       = "EMPTY"
BLENDER_OBJ_TYPE_GPENCIL     = "GPENCIL"
BLENDER_OBJ_TYPE_CAMERA      = "CAMERA"
BLENDER_OBJ_TYPE_LIGHT       = "LIGHT"
BLENDER_OBJ_TYPE_SPEAKER     = "SPEAKER"
BLENDER_OBJ_TYPE_LIGHT_PROBE = "LIGHT_PROBE"

BLENDER_MATERIAL_BLEND_OPAQUE = "OPAQUE"
BLENDER_MATERIAL_BLEND_CLIP   = "CLIP"
BLENDER_MATERIAL_BLEND_HASHED = "HASHED"
BLENDER_MATERIAL_BLEND_BLEND  = "BLEND"


def _make_vec3(blender_vec3):
    return linear_algebra.Vec3(blender_vec3[0], blender_vec3[1], blender_vec3[2])


class _MaterialParser:
    NODE_BSDF = "ShaderNodeBsdfPrincipled"
    NODE_HOLDOUT = "ShaderNodeHoldout"
    NODE_MATERIAL_OUTPUT = "ShaderNodeOutputMaterial"
    NODE_TEX_IMAGE = "ShaderNodeTexImage"

    @classmethod
    def parse(cls, blender_material) -> Optional[data_struct.Material]:
        assert blender_material is not None

        shader_output = cls.__find_node_named(cls.NODE_MATERIAL_OUTPUT, blender_material.node_tree.nodes)
        linked_shader = shader_output.inputs["Surface"].links[0].from_node

        if cls.NODE_BSDF == linked_shader.bl_idname:
            pass
        elif cls.NODE_HOLDOUT == linked_shader.bl_idname:
            return None
        else:
            raise RuntimeError("[DAL] Only Principled BSDF, Holdout are supported: {}".format(linked_shader.bl_idname))

        bsdf = linked_shader
        material = data_struct.Material()

        node_base_color = bsdf.inputs["Base Color"]
        node_metallic = bsdf.inputs["Metallic"]
        node_roughness = bsdf.inputs["Roughness"]
        node_normal = bsdf.inputs["Normal"]

        material.m_alphaBlend = True if blender_material.blend_method != BLENDER_MATERIAL_BLEND_OPAQUE else False
        material.m_roughness = node_roughness.default_value
        material.m_metallic = node_metallic.default_value

        image_node = cls.__find_node_recur_named(cls.NODE_TEX_IMAGE, node_base_color)
        if image_node is not None:
            material.m_albedoMap = image_node.image.name

        image_node = cls.__find_node_recur_named(cls.NODE_TEX_IMAGE, node_metallic)
        if image_node is not None:
            material.m_metallicMap = image_node.image.name

        image_node = cls.__find_node_recur_named(cls.NODE_TEX_IMAGE, node_roughness)
        if image_node is not None:
            material.m_roughnessMap = image_node.image.name

        image_node = cls.__find_node_recur_named(cls.NODE_TEX_IMAGE, node_normal)
        if image_node is not None:
            material.m_normalMap = image_node.image.name

        return material

    @staticmethod
    def __find_node_named(name: str, nodes):
        for node in nodes:
            if name == node.bl_idname:
                return node
        return None

    @classmethod
    def __find_node_recur_named(cls, name, parent_node):
        if hasattr(parent_node, "links"):
            for linked in parent_node.links:
                node = linked.from_node
                if name == node.bl_idname:
                    return node
                else:
                    res = cls.__find_node_recur_named(name, node)
                    if res is not None:
                        return res
        if hasattr(parent_node, "inputs"):
            for nodeinput in parent_node.inputs:
                res = cls.__find_node_recur_named(name, nodeinput)
                if res is not None:
                    return res

        return None


def _parse_model(obj, data_id) -> data_struct.Model:
    assert isinstance(obj.data, bpy.types.Mesh)

    armature = obj.find_armature()
    armature_name = "" if armature is None else armature.name
    del armature

    units: List[Tuple[data_struct.Mesh, data_struct.Material]] = []

    # Materials
    for i in range(len(obj.data.materials)):
        material = _MaterialParser.parse(obj.data.materials[i])
        if material is None:
            material = data_struct.Material()
        units.append((data_struct.Mesh(armature_name), material))

    # Vertices
    obj.data.calc_loop_triangles()
    for triangle in obj.data.loop_triangles:
        material_index = int(triangle.material_index)

        assert 3 == len(triangle.vertices)
        for i, vert_index in enumerate(triangle.vertices):
            vertex_data = data_struct.Vertex()

            # Vertex
            vertex_data.m_pos = _make_vec3(obj.data.vertices[vert_index].co)

            # UV coord
            loop_index: int = triangle.loops[i]
            if obj.data.uv_layers.active is not None and len(obj.data.uv_layers.active.data):
                uv_data = obj.data.uv_layers.active.data[loop_index].uv
            else:
                uv_data = (0.0, 0.0)
            vertex_data.m_uv_coord = linear_algebra.Vec2(uv_data[0], uv_data[1])

            # Normal
            if triangle.use_smooth:
                vertex_data.m_normal = _make_vec3(obj.data.vertices[vert_index].normal)
            else:
                vertex_data.m_normal = _make_vec3(triangle.normal)

            # Rest
            units[material_index][0].add_vertex(vertex_data)

    # Model
    model = data_struct.Model(data_id)
    model.m_render_units = units

    return model


def _parse_object_and_fill_scene(obj, scene: data_struct.Scene) -> None:
    obj_name = str(obj.name)
    obj_type = str(obj.type)

    if BLENDER_OBJ_TYPE_MESH == obj_type:
        data_id = id(obj.data)
        if data_id not in scene.m_models.keys():
            scene.m_models[data_id] = _parse_model(obj, data_id)
        print("[DAL] Done with object:", obj_name)
    else:
        print("[DAL] skipped object:", obj_name)


def parse(collections):
    scene_list = []

    for x in collections:
        scene = data_struct.Scene(x.name)
        print("[DAL] Scene", scene.m_name)

        for obj in x.all_objects:
            _parse_object_and_fill_scene(obj, scene)

        scene_list.append(scene)

    return scene_list
