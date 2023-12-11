# -*- coding: utf-8 -*-
from typing import List, Any, Dict


class BoundingBox:
    """
    Class for a region bounded by a given pair of geometric coordinates

    **Main Attributes**
        - ``.min_lon``: float, minimum longitude of the BoundingBox
        - ``.max_lon``: float, maximum longitude of the BoundingBox
        - ``.min_lat``: float, minimum latitude of the BoundingBox
        - ``.max_lon``: float, maximum latitude of the BoundingBox
    """

    def __init__(self, lon_1, lat_1, lon_2, lat_2, data_type=float):
        """

        :param data_type: target data type of the attributes
        """
        lon_1, lon_2 = data_type(lon_1), data_type(lon_2)
        lat_1, lat_2 = data_type(lat_1), data_type(lat_2)
        self.min_lon = min(lon_1, lon_2)
        self.max_lon = max(lon_1, lon_2)
        self.min_lat = min(lat_1, lat_2)
        self.max_lat = max(lat_1, lat_2)

    def to_list(self) -> List[float]:
        """
        Convert the BoundingBox object to a list [min_lon, min_lat, max_lon, max_lat]

        :return: list
        """
        return [self.min_lon, self.min_lat, self.max_lon, self.max_lat]

    def get_bound_dict(self, value_type=float) -> Dict[str, Any]:
        """
        Convert the BoundingBox object to a dictionary
        Note that the keys are "maxlon", "minlon", "maxlat", and "minlat", the values are the corresponding attributes

        :param value_type: data type of the values of the returned dictionary
        :return: dict
        """
        return {"maxlon": value_type(self.max_lon), "minlon": value_type(self.min_lon),
                "maxlat": value_type(self.max_lat), "minlat": value_type(self.min_lat)}
