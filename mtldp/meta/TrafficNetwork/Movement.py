# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, List, Dict, Any

import pandas as pd

from .Geometry import Geometry

if TYPE_CHECKING:
    from .types import Turn
    from .Arterial import Arterial
    from .LaneSet import LaneSet
    from .Link import Link
    from .Node import Node


class Movement:
    """
     A movement reflects the user perspective and is defined by the user type and the action that is taken (e.g.
     through, right turn, left turn)

     **Main Attributes**
        -``index``: phase id
        -``movement_id``: movement id
        -``upstream_link``: upstream link
        -``downstream_link``: downstream link
        -``node``: center node
        -``direction``: moving direction
        -``upstream_length``: upstream length
        -``protected``:
        -``geometry``:
        -``belonged_arterial``: belonged arterial object
    """

    def __init__(self):
        self.index: str | None = None
        self.movement_id: str | None = None
        self.upstream_link: Link | None = None
        self.buffer_length: float | None = None
        self.downstream_link: Link | None = None
        self.node: Node | None = None

        self.direction: Turn | None = None
        self.upstream_length: float | None = None
        self.protected: bool = False
        self.geometry: Geometry | None = None
        self.laneset_list: List[LaneSet] = []
        self.lane_number: int | None = None

        self.belonged_arterial: List[Arterial] = []
        self.conflicting_movements: List[Movement] | None = None
        self.share_lane_movements: List[Movement] | None = None
        self.share_approach_movements: List[Movement] | None = None
        self.same_approach_through_movement: List[Movement] | None = None

    def __str__(self) -> str:
        return self.movement_id

    def set_basic_info(self, upstream_link: Link, downstream_link: Link, node: Node):
        self.upstream_link = upstream_link
        self.downstream_link = downstream_link
        self.node = node

    def get_geometry(self) -> Geometry:
        upstream_geometry = self.upstream_link.geometry
        downstream_geometry = self.downstream_link.geometry
        return Geometry(upstream_geometry.lon + downstream_geometry.lon,
                        upstream_geometry.lat + downstream_geometry.lat)

    def to_dict(self, attr="all") -> Dict[str, Any]:
        movement_dict = {}
        all_dict = self.__dict__
        if attr == "all":
            movement_dict = all_dict.copy()
            attr = all_dict.keys()
        else:
            for one_attr in attr:
                movement_dict[one_attr] = all_dict[one_attr]
        for link_info in {"upstream_link", "downstream_link", "node", "geometry"}.intersection(set(attr)):
            movement_dict[link_info] = str(all_dict[link_info])
        if "belonged_arterial" in attr:
            movement_dict["belonged_arterial"] = []
            for arterial in self.belonged_arterial:
                movement_dict["belonged_arterial"].append(str(arterial))

        return movement_dict

    def to_df(self, attr: str = "all") -> pd.DataFrame:
        movement_dict = self.to_dict(attr=attr)
        return pd.DataFrame(movement_dict, index=[0])
