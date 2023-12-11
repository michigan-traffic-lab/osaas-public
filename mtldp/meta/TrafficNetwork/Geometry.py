# -*- coding: utf-8 -*-
from typing import List


class Geometry:
    """
    Class for longitude and latitude

    **Main Attributes**
        -``.lon``: list of longitudes
        -``.lat``: list of latitudes
    """

    def __init__(self, lon_ls: List[float], lat_ls: List[float]):
        """

        :param lon_ls: list of longitudes
        :param lat_ls: list of latitudes
        """
        self.lon = lon_ls
        self.lat = lat_ls

    def __len__(self) -> int:
        return len(self.lon)

    def __str__(self) -> str:
        """

        :return: str, "lon lat;lon lat; ... ;lon lat"
        """
        return self.to_string()

    def to_string(self) -> str:
        """
        Convert the Geometry object to a string of "lon lat;lon lat; ... ;lon lat"

        :return: str
        """
        output = ""
        for i in range(len(self.lon) - 1):
            output += (str(self.lon[i]) + " " + str(self.lat[i]) + ";")
        output += (str(self.lon[-1]) + " " + str(self.lat[-1]))
        return output

    def to_list(self) -> List[List[float]]:
        """
        Convert the Geometry object to a list of [[lon1, lat1], [lon2, lat2], ...]

        :return: list
        """
        output = []
        for i in range(len(self.lon)):
            output.append([self.lon[i], self.lat[i]])
        return output
