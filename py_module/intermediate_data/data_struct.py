from typing import List, Tuple, Optional, Dict

from . import linear_algebra as lgb


class Material:
    def __init__(self):
        self.m_roughness = 0.5
        self.m_metallic = 0.0
        self.m_alpha_blend = False

        self.m_albedo_map = ""
        self.m_roughness_map = ""
        self.m_metallic_map = ""
        self.m_normal_map = ""


class Vertex:
    def __init__(self):
        self.m_pos = lgb.Vec3()
        self.m_uv_coord = lgb.Vec2()
        self.m_normal = lgb.Vec3()
        self.m_joints: List[Tuple[float, str]] = []

    def __eq__(self, other: "Vertex") -> bool:
        return (
            self.m_pos == other.m_pos and
            self.m_uv_coord == other.m_uv_coord and
            self.m_normal == other.m_normal and
            self.m_joints == other.m_joints
        )

    def add_joint(self, name: str, weight: float) -> None:
        if 0.0 == weight:
            return

        if self.get_weight_of_joint(name) is not None:
            raise RuntimeError()

        self.m_joints.append((weight, name))
        self.m_joints.sort(reverse=True)

    def get_weight_of_joint(self, name: str) -> Optional[float]:
        """
        returns -1 if given joint is not in the list
        """
        for j_weight, j_name in self.m_joints:
            if j_name == name:
                return j_weight

        return None


class Mesh:
    def __init__(self, skeleton_name: str = ""):
        self.m_vertices: List[Vertex] = []
        self.m_indices: List[int] = []
        self.m_skeleton_name = str(skeleton_name)

    def add_vertex(self, vertex: Vertex) -> None:
        """
        for i, v in enumerate(self.m_vertices):
            if v == vertex:
                self.m_indices.append(i)
                return
        """

        self.m_indices.append(len(self.m_vertices))
        self.m_vertices.append(vertex)


class Model:
    def __init__(self, obj_id: int):
        self.m_id = int(obj_id)
        self.m_ref_count = 0
        self.m_render_units: List[Tuple[Mesh, Material]] = []


class Scene:
    def __init__(self, name: str):
        self.m_name = str(name)
        self.m_models: Dict[int, Model] = {}
