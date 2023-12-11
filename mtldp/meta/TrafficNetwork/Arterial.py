# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, TYPE_CHECKING, List

if TYPE_CHECKING:
    from .Geometry import Geometry
    from .Link import Link
    from .Network import Network
    from .Node import Node
    from .Movement import Movement


class Arterial:
    def __init__(self, arterial_id: str, ref_node: str = None):
        self.arterial_id: str = arterial_id
        self.ref_node: str = ref_node
        self.oneways: Dict[str, OnewayArterial] = {}

    def get_node_list(self, stype='signalized') -> List[Node]:
        node_id_list: List[str] = []
        node_list: List[Node] = []
        for oneway in self.oneways.values():
            oneway_node_list = oneway.node_list
            for node in oneway_node_list:
                if node.type == stype:
                    node_id = str(node)
                    if not (node_id in node_id_list):
                        node_id_list.append(node_id)
                        node_list.append(node)
        return node_list


class Path:
    def __init__(self, path_id=None):
        self.path_id = path_id
        self.origin_node: Node | None = None
        self.destination_node: Node | None = None
        self.network: Network | None = None
        self.node_list: List[Node] = []
        self.link_list: List[Link] = []
        self.movement_list: List[Movement] = []
        self.length: float = 0

        # set geometry
        self.geometry: Geometry | None = None
        self.distance_by_movement: Dict[str, float] = {}
        self.distance_by_link: Dict[str, float] = {}
        self.distance_by_node: Dict[str, float] = {}


class OnewayArterial(Path):
    def __init__(self, sup_arterial: Arterial, direction: str):
        super().__init__()
        self.sup_arterial: Arterial = sup_arterial
        self.direction: str = direction
        self.name = self._set_name(sup_arterial.arterial_id)

    def _set_name(self, name: str) -> str:
        """
        Set name of the OnewayArterial

        """
        if self.direction == "E":
            to_direction = "east"
        elif self.direction == "W":
            to_direction = "west"
        elif self.direction == "S":
            to_direction = "south"
        elif self.direction == "N":
            to_direction = "north"
        else:
            to_direction = "null"
        return f"{name} {to_direction}bound"
