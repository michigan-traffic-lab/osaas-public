# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import NodeType
    from .LaneSet import LaneSet
    from .Link import Link
    from .Movement import Movement
    from .Segment import Segment


class Node:
    """
    Node corresponds to the node in osm (xml) data,

    Node is also the father class for the following classes:
        - :class:`MTTTrajectoryData.mimap.SignalizedNode`
        - :class:`MTTTrajectoryData.mimap.SignalizedNode`
        - :class:`MTTTrajectoryData.mimap.UnSignalizedNode`
        - :class:`MTTTrajectoryData.mimap.EndNode`

    **Main attributes**
        - ``.node_id`` unique id of the node.
        - ``.osm_attrib`` attributes of the node in the original osm data (dict)
        - ``.osm_tags`` tags of the node in the original osm data (dict)
        - ``.type`` type of the node ("ordinary", "connector", "signalized", "unsignalized", "end")
        - ``.latitude`` and ``.longitude`` node GPS coordinate
        - ``.upstream_segments`` upstream segments of this node (list of str)
        - ``.downstream_segments`` downstream segments of this node (list of str)

    """

    def __init__(self, node_id: str = None, osm_attrib=None, osm_tags=None):
        # original osm data (essential components)
        self.node_id: str = node_id
        self.osm_attrib = osm_attrib
        self.osm_tags = osm_tags
        self.name: str | None = None

        self.type: NodeType = "ordinary"

        self.latitude: float | None = None
        self.longitude: float | None = None

        self.connector_list = []

        # upstream and downstream segments
        self.upstream_segments: List[Segment] = []
        self.downstream_segments: List[Segment] = []

        # upstream and downstream links
        self.upstream_links: List[Link] = []
        self.downstream_links: List[Link] = []

        # upstream and downstream lanesets
        self.upstream_lanesets: List[LaneSet] = []
        self.downstream_lanesets: List[LaneSet] = []

        self.upstream_lanes = []
        self.downstream_lanes = []
        self.movement_list: List[Movement] = []
        self.belonged_sup_arterial = []

        # osm way id that starts/ends at this node
        self.od_ways: List[str] = []
        # in original osm data, some segments might directly traverse the node, this is
        # invalid, we need to filter this condition out by splitting the traversing segments
        self.traverse_ways: List[str] = []

        self.v_c_ratio: float = 1

        if self.node_id is not None and self.osm_attrib is not None and self.osm_tags is not None:
            self.generate_basic_info()

    @classmethod
    def init_from_node(cls, node: Node):
        """
        Initialize a node from the input node

        :param node: `cores.mtlmap.Node`
        :return: `cores.mtlmap.Node`
        """
        new_node = cls()
        for k, v in node.__dict__.items():
            setattr(new_node, k, v)
        return new_node

    def is_intersection(self) -> bool:
        """
        Check if a node is an intersection

        :return: True if this node is an intersection
        """
        intersection_flag = (self.type == "signalized") or (self.type == "unsignalized")
        return intersection_flag

    def is_ordinary_node(self) -> bool:
        """
        Check if a node is an ordinary node

        :return: True if this node is an ordinary node
        """
        return self.type == "ordinary"

    def generate_basic_info(self):
        """
        Add latitude and longitude attributes

        :return: None
        """
        self.latitude = float(self.osm_attrib["lat"])
        self.longitude = float(self.osm_attrib["lon"])

    def add_connector(self, connector):
        """
        Add connector to the node

        :param connector: `cores.mtlmap.Connector`
        :return: None
        """
        exist_connector_id_list = [con.connector_id for con in self.connector_list]
        if not (connector.connector_id in exist_connector_id_list):
            self.connector_list.append(connector)

    def add_movement(self, movement: Movement):
        """
        Add a movement to the node

        :param movement: `cores.mtlmap.Movement`
        :return:
        """
        movement_id_list = [mov.movement_id for mov in self.movement_list]
        if movement.movement_id not in movement_id_list:
            self.movement_list.append(movement)

    def get_upstream_junctions(self) -> List[Node]:
        junction_list = []
        for upstream_link in self.upstream_links:
            upstream_junction = upstream_link.upstream_node
            junction_list.append(upstream_junction)
        return junction_list

    def __str__(self) -> str:
        return self.node_id


# TODO: Eliminate all the init_from_node class method
class SegmentConnectionNode(Node):
    """
    The node that connects the segments (all through, no left/right turn)
    """

    def __init__(self):
        super().__init__()
        self.type: NodeType = "connector"

    @classmethod
    def init_from_node(cls, node: Node):
        segment_connector = cls()
        for k, v in node.__dict__.items():
            setattr(segment_connector, k, v)
        segment_connector.type = "connector"
        return segment_connector


# TODO: Eliminate all the init_from_node class method
class SignalizedNode(Node):
    """
    Class for signalized intersection

    Inherit from :py:class:`MTTTrajectoryData.mimap.Node`

    **Additional Attributes**

        - ``.timing_plan`` the signal controller of this node, :py:class:`mimap.SignalTimingPlan`.
    """

    def __init__(self):
        super().__init__()
        self.type: NodeType = "signalized"
        self.timing_plan = None

    @classmethod
    def init_from_node(cls, node):
        signalized_node = cls()
        for k, v in node.__dict__.items():
            setattr(signalized_node, k, v)
        signalized_node.type = "signalized"
        return signalized_node


# TODO: Eliminate all the init_from_node class method
class UnSignalizedNode(Node):
    """
    Class for unsignalized node

    Inherit from :py:class:`MTTTrajectoryData.mimap.Node`

    **Additional Attributes**
    """

    def __init__(self):
        super().__init__()
        self.type: NodeType = "unsignalized"

    @classmethod
    def init_from_node(cls, node):
        unsignalized_node = cls()
        for k, v in node.__dict__.items():
            setattr(unsignalized_node, k, v)
        unsignalized_node.type = "unsignalized"
        return unsignalized_node


# TODO: Eliminate all the init_from_node class method
class EndNode(Node):
    def __init__(self):
        super().__init__()
        self.type: NodeType = "end"

    @classmethod
    def init_from_node(cls, node):
        end_node = cls()
        for k, v in node.__dict__.items():
            setattr(end_node, k, v)
        end_node.type = "end"
        return end_node
