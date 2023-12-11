# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING

import numpy as np

from .BoundingBox import BoundingBox
from .Mode import GraphMode

if TYPE_CHECKING:
    from .Arterial import Arterial
    from .LaneSet import LaneSet
    from .Link import Link
    from .Movement import Movement
    from .Node import Node, SignalizedNode, UnSignalizedNode, EndNode
    from .OsmWay import OsmWay
    from .Segment import Segment


class Network:
    """
    Class for the general network

    **Main Attributes**
        Classes for the roads
            - ``.ways``: a dictionary contains all the OpenStreetMap ways (:class:`cores.mtlmap.OsmWay`) in the network.
            - ``.links`` a dictionary contains all the links (:class:`cores.mtlmap.Link`) in the network.
            - ``.segments`` a dictionary contains all the segments (:class:`cores.mtlmap.Segment`) in the network.
            - ``.lanesets`` a dictionary contains all the lanesets (:class:`cores.mtlmap.LaneSet`) in the network.
        Classes for the nodes
            - ``.nodes`` a dictionary contains all the nodes (:py:class:`cores.mtlmap.Node`) in the network
        Others
            - ``.bounds`` the bounding box of the network, `cores.utils.BoundingBox`
            - ``.networkx_graph`` networkx graph
    """

    def __init__(self, region_name: str, city_id: str = ''):
        self.region_name: str = region_name
        self.city_id: str = city_id
        # basic members
        self.segments: Dict[str, Segment] = {}
        self.ways: Dict[str, OsmWay] = {}
        self.nodes: Dict[str, Node] = {}
        self.links: Dict[str, Link] = {}
        self.movements: Dict[str, Movement] = {}
        self.arterials: Dict[str, Arterial] = {}
        # self.lanes = {}

        # the following content is for network modeling
        self.lanesets: Dict[str, LaneSet] = {}
        # self.connectors = {}
        # self.conflict_points = {}
        # self.lane_connectors = {}

        self.signalized_node_list: List[SignalizedNode] = []
        self.unsignalized_node_list: List[UnSignalizedNode] = []
        self.end_node_list: List[EndNode] = []

        self.networkx_mode: GraphMode = GraphMode.SEGMENT
        self.networkx_graph = None
        self.bounds: BoundingBox | None = None

    def add_node(self, node: Node):
        self.nodes[node.node_id] = node

    def add_way(self, osm_way: OsmWay):
        self.ways[osm_way.way_id] = osm_way

    def add_segment(self, segment: Segment):
        self.segments[segment.segment_id] = segment

    def add_link(self, link: Link):
        self.links[link.link_id] = link

    def add_movement(self, movement: Movement):
        self.movements[movement.movement_id] = movement

    def add_laneset(self, laneset: LaneSet):
        self.lanesets[laneset.laneset_id] = laneset

    def add_arterial(self, arterial: Arterial):
        self.arterials[arterial.arterial_id] = arterial

    def reset_bound(self):
        """
        Reset the boundary to be the min and max of the longitudes and latitudes

        :return: None
        """
        lat_list = []
        lon_list = []
        for node_id, node in self.nodes.items():
            lat_list.append(node.latitude)
            lon_list.append(node.longitude)

        self.bounds = BoundingBox(np.round(np.min(lon_list), 5), np.round(np.min(lat_list), 5),
                                  np.round(np.max(lon_list), 5), np.round(np.max(lat_list), 5))
