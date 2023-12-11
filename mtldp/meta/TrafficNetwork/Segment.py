# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from .types import OsmDirection, Direction
    from .Geometry import Geometry
    from .LaneSet import LaneSet
    from .Link import Link
    from .Node import Node
    from .OsmWay import OsmWay


class Segment:
    """
    A segment is a proportion of a link that share the same number of lanes.

    **Main attributes**
        - ``.segment_id`` an integer for segment ID. 0 or 1 (denotes the direction ) is added at the end of the
          ``.osm_way`` as the ``.segment_id``
        - ``.osm_way`` an integer for the original OSM way ID
        - ``.osm_tags`` a dictionary contains all the tags in the original osm data.
        - ``.osm_attrib`` a dictionary contains all the attributes in the original osm data.
        - ``.belonged_link`` the link ID that the segment belongs to
        - ``.laneset_list`` the list of lane sets that belong to the segment
        - ``.laneset_num`` the number of lane sets that belong to the segment
        - ``.speed_limit`` speed limit of the segment in m/s
        - ``.length`` length of the segment in meters
        - ``.geometry`` the GPS coordinates along the segment
        - ``.lane_number`` number of lanes of the segment
        - ``.lane_assignment`` the assignment of the lanes of the segment. For example, "all_through" means all lanes on
          the segment are through movements. "left|through;right" means the segments include both left turn movement
          through (right turn) movement. If unavailable, this value is null.
        - ``.heading`` the heading angle of the segment (range: (-180,180]))
        - ``.from_direction`` the direction from which the segment originates. For example, if the segment originates
          from south, this value is "S".
        - ``.node_list`` a list of nodes on the segment
        - ``.upstream_node`` the upstream node of the segment
        - ``.downstream_node`` the downstream node of the segment
        - ``.upstream_segment`` a list of the upstream segment ID of this segment
        - ``.downstream_segment`` a list of the downstream segment ID of this segment
        - ``.downstream_direction_info`` a dictionary that represents the direction of the downstream segments.
          For example, ``{'l': '4116329441', 'r': '4126838890', 's': '87279680'}`` means left turn downstream segment is
          ``4116329441``. Through movement downstream segment is ``87279680``, and right turn downstream segment is
          ``4126838890``

    """

    def __init__(self):
        self.segment_id: str | None = None
        self.osm_way: OsmWay | None = None

        self.osm_tags: Dict[str, Any] | None = None
        self.osm_attrib: Dict[str, Any] | None = None

        self.belonged_link: Link | None = None

        self.laneset_list: List[LaneSet] = []
        # self.lane_list = []
        self.laneset_num: int | None = None

        self.osm_direction_flag: OsmDirection | None = None  # "backward" or "forward"

        self.speed_limit: float | None = None
        self.length: float | None = None  # unit: meters
        self.geometry: Geometry | None = None  # `cores.utils.Geometry`
        self.lane_number: int | None = None
        self.lane_assignment = None

        self.heading: float | None = None
        # self.weighted_heading = None
        self.from_direction: Direction | None = None

        self.node_list: List[Node] | None = None
        # self.downstream_node_type = None            # "end", "ordinary", "signalized", "unsignalized"
        # self.upstream_node_type = None

        # network topology
        self.upstream_node: Node | None = None
        self.downstream_node: Node | None = None

        self.downstream_connectors = []
        self.upstream_connectors = []

        self.upstream_segments: List[Segment] = []
        self.downstream_segments: List[Segment] = []
        self.downstream_directions_info = {}
        self.downstream_directions = ""

    def __str__(self) -> str:
        return self.segment_id
