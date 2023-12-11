# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import List, TYPE_CHECKING, Dict, Any

from .constants import MPH_TO_METERS_PER_SEC

if TYPE_CHECKING:
    from .Node import Node
    from .Geometry import Geometry


class OsmWay:
    """
    OsmWay corresponds to the "way" in the original osm data

    **Main attributes**
        - ``.osm_tags`` a dictionary contains all the tags in the original osm data.
        - ``.osm_attrib`` a dictionary contains all the attributes in the original osm data.
        - ``.way_id`` an integer for OSM way ID
        - ``.node_list`` a list of nodes on the way
        - ``.length`` length of the way in meters
        - ``.geometry`` the GPS coordinates along the way
        - ``.forward_heading`` the heading angle at the start of the way (range: (-180,180]))
        - ``.backward_heading`` the heading angle at the end of the way (range: (-180,180]))
        - ``.lane_number`` number of lanes
        - ``.forward_lanes`` number of lanes from the start of the way to the end of the way
        - ``.backward_lanes`` number of lanes from the end of the way to the start of the way
        - ``.name`` name of the way
        - ``.speed_limit`` speed limit of the way in m/s

    """

    def __init__(self, way_id: str = None, node_list=None, osm_attrib=None, osm_tags=None):
        # original info from osm (xml) data
        self.osm_tags: Dict[str, Any] = osm_tags
        self.osm_attrib: Dict[str, Any] = osm_attrib

        self.way_id: str = way_id

        self.node_list: List[Node | str] = node_list
        # self.lane_sets = {}
        # self.lanes = {}

        self.length: float | None = None  # unit: meters
        self.geometry: Geometry | None = None  # cores.utils.Geometry
        self.forward_heading: float | None = None
        self.weighted_forward_heading: float | None = None
        self.backward_heading: float | None = None
        self.weighted_backward_heading: float | None = None

        self.lane_number: int | None = None  # fixme:

        self.forward_lanes: int | None = None
        self.backward_lanes: int | None = None

        self.forward_lane_assignment = None
        self.backward_lane_assignment = None

        self.directed: bool = False  # fixme: I think all the ways are undirected.
        self.name: str | None = None
        self.speed_limit: float | None = None

        if (self.way_id is not None) and (self.osm_attrib is not None) and (self.osm_tags is not None):
            self.generate_basic_info()

    def generate_basic_info(self):
        """
        extract useful information from the osm attrib and tags

        current extracted information includes:
            - lane information (# and assignment)
            - speed limit (25mph if null)
            - name

        :return:
        """
        if "maxspeed" in self.osm_tags.keys():
            speed_limit = self.osm_tags["maxspeed"]
        else:
            if "maxspeed:forward" in self.osm_tags.keys():
                speed_limit = self.osm_tags["maxspeed:forward"]
            else:
                speed_limit = "25 mph"

        speed = float(speed_limit.split(" ")[0])
        self.speed_limit = speed * MPH_TO_METERS_PER_SEC
        if "oneway" in self.osm_tags.keys():
            if self.osm_tags["oneway"] == "yes":
                self.directed = True
                # fixme: here the backward lane must be -1,
                #  see function generating the segments of the network for details
                self.backward_lanes = -1
            else:
                self.directed = False
        else:
            self.directed = False

        if "name" in self.osm_tags.keys():
            self.name = self.osm_tags["name"]
        else:
            self.name = "null"

        # load lane number and lane assignment
        if "lanes" in self.osm_tags.keys():
            self.lane_number = int(self.osm_tags["lanes"])

            if "lanes:backward" in self.osm_tags.keys():
                self.backward_lanes = int(self.osm_tags["lanes:backward"])
            if "lanes:forward" in self.osm_tags.keys():
                self.forward_lanes = int(self.osm_tags["lanes:forward"])

            if self.directed:
                self.forward_lanes = self.lane_number
            else:
                if self.backward_lanes is None and self.forward_lanes is None:
                    self.forward_lanes = self.lane_number / 2
                    self.backward_lanes = self.lane_number / 2
                if self.backward_lanes is None:
                    self.backward_lanes = self.lane_number - self.forward_lanes
                if self.forward_lanes is None:
                    self.forward_lanes = self.lane_number - self.backward_lanes

            if "turn:lanes" in self.osm_tags.keys():
                self.forward_lane_assignment = self.osm_tags["turn:lanes"]

            if "turn:lanes:backward" in self.osm_tags.keys():
                self.backward_lane_assignment = self.osm_tags["turn:lanes:backward"]
            if "turn:lanes:forward" in self.osm_tags.keys():
                self.forward_lane_assignment = self.osm_tags["turn:lanes:forward"]
        else:
            self.forward_lanes = 1
            self.backward_lanes = 1
            if "oneway" in self.osm_tags.keys():
                if self.osm_tags["oneway"] == "yes":
                    self.directed = True
                    # fixme: here the backward lane must be -1,
                    #  see function generating the segments of the network for details
                    self.backward_lanes = -1
            logging.warning(self.way_id + " does not have lane number!")

    def __str__(self):
        return self.way_id
