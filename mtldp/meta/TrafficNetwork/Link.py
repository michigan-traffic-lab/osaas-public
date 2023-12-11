# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, TYPE_CHECKING, Any, Dict

import pandas as pd


if TYPE_CHECKING:
    from .types import Direction
    from .Arterial import Arterial
    from .Geometry import Geometry
    from .Node import Node
    from .Segment import Segment


class Link:
    """
    A link connects two signalized/unsignalized/origin/destination nodes. It might contain multiple segments


    **Main attributes**
        - ``.link_id`` a integer for link ID. It has the format: number1_number2. The first number is the original node
          of the link. The second number is the destination node of the link.
        - ``.segment_list`` the list of segments that belong to the link
        - ``.geometry`` the GPS coordinates along the link
        - ``.node_list`` a list of nodes on the link
        - ``.upstream_node`` the upstream node of the link
        - ``.downstream_node`` the downstream node of the link
        - ``.heading`` the heading angle of the link (range: (-180,180]))
        - ``.from_direction`` the direction from which the segment originates. For example, if the segment originates
          from south, this value is "S".
        - ``.length`` float, length of the link in meters
    """

    def __init__(self):
        self.link_id: str | None = None
        self.segment_list: List[Segment] = []
        self.geometry: Geometry | None = None
        self.node_list: List[Node] = []

        self.upstream_node: Node | None = None
        self.downstream_node: Node | None = None

        self.heading: float | None = None  # (-180,180]
        self.from_direction: Direction | None = None  # 'E', 'W', 'N', 'S'

        self.speed_limit: float | None = None
        self.length: float | None = None

        # buffer segments: segments before the buffer (only 1 laneset)
        self.buffer_segments: List[Segment] = []  # fixme
        self.buffer_length: float | None = None  # fixme

        # stop bar and clearance time
        self.downstream_stopbar = None
        self.downstream_stopbar_detail = None

        self.upstream_clearance = None
        self.upstream_clearance_detail = None
        # user equilibrium

        self.belonged_arterial: List[Arterial] = []

    def to_dict(self, attr="all") -> Dict[str, Any]:
        all_dict = self.__dict__
        link_dict = {}
        if attr == "all":
            link_dict = all_dict.copy()
            attr = all_dict.keys()
        else:
            for one_attr in attr:
                link_dict[one_attr] = all_dict[one_attr]
        for link_attr in {"geometry", "upstream_node", "downstream_node"}.intersection(set(attr)):
            link_dict[link_attr] = str(link_dict[link_attr])
        for link_attr in {"segment_list", "node_list", "buffer_segments", "belonged_arterial"}.intersection(set(attr)):
            link_dict[link_attr] = [str(item) for item in link_dict[link_attr]]

        return link_dict

    def to_df(self, attr="all") -> pd.DataFrame:
        link_dict = self.to_dict(attr=attr)
        return pd.DataFrame(link_dict, index=[0])

    def __str__(self) -> str:
        return self.link_id
