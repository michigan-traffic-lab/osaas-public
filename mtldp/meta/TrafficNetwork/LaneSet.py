# -*- coding: utf-8 -*-

"""
This file is to generate the lane information from the osm map.
This part is hard to explain, although I have tried here.
If you feel confused, contact: xingminw@umich.edu

The lane information is highly relied on the following osm tags:

"lanes:forward/backward/null"
"turn:lanes:forward/backward/null"

Here is the rule:
* If there is no lane assignment information, then we infer the lane assignment (check the code):
    - If there is a through movement
        - If the lane number >=2, assign a dedicated left
        - If the left-over lane number is still larger than 2, assign a dedicated right

        example:
        lanes=2: left|through;right, through|right
        lanes=3: left|through|right, left|through|through, through|through|right
    - If there is not a through movement
        - left and right share the lane evenly (left turn has a higher priority)
* If there is lane assignment information:
    - assignment == "|": all movements share the lane
    - assignment == "left|through;right"
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .types import Direction, Turn
    from .Geometry import Geometry
    from .Link import Link
    from .Node import Node
    from .Segment import Segment


class LaneSet(object):
    def __init__(self):
        self.laneset_id: str | None = None
        self.type: str | None = None  # "internal", "source", "destination"

        # segment id of this pipeline
        self.belonged_segment: Segment | None = None
        self.belonged_link: Link | None = None
        # Unused attributes
        self.lane_list = []

        self.turning_direction: Turn | None = None  # "l", "r", "s", or their combination
        self.length: float | None = None  # unit: meters
        self.speed_limit: float | None = None  # unit: meters / sec
        self.lane_number: int | None = None

        self.heading: float | None = None  # (-180,180]
        self.from_direction: Direction | None = None  # 'E', 'W', 'N', 'S'

        # Unused attributes
        self.downstream_connector = None
        # Unused attributes
        self.upstream_connectors = []
        self.geometry: Geometry | None = None

        # offset: 0 - through   1 - left   -1  -  right
        self.insegment_offset: int | None = None  # fixme

        self.downstream_lanesets: List[LaneSet] = []  # downstream pipeline id list
        # Unused attributes
        self.turning_ratio_list = None  # turning ratio list

        self.upstream_node: Node | None = None
        self.downstream_node: Node | None = None

        # traffic signal attributes
        self.phase_id: str | None = None
        # Unused attributes
        self.movement_list = []

        # self.travel_time = None
        self.free_travel_time: float | None = None
        # self.capacity = None
        # self.belonged_path = []
        # self.laneset_flow = None

        # user equilibrium
        # self.laneset_previous_flow = None

    def __str__(self) -> str:
        return self.laneset_id
