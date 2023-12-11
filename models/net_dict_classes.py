import numpy as np
import pandas as pd

from models.movement_tod_classes import MovementTOD


class MovementNetDict(object):
    """
    A network in this project is defined by a collection of movements
    """
    def __init__(self):
        self.dict = {}
        self.resolution = None
        self.departure_repeats = None
        self.date_list = []
        self.tod_dict = {}

    def add_movement_tod_curve(self, movement_tod_curve):
        """

        :param movement_tod_curve:
        :return:
        """
        movement_id = movement_tod_curve.movement_id
        tod_name = movement_tod_curve.tod_name
        if not (movement_id in self.dict.keys()):
            self.dict[movement_id] = {}
        self.dict[movement_id][tod_name] = movement_tod_curve

    def get_movement_tod_curve(self, movement_id, tod_name):
        if not (movement_id in self.dict.keys()):
            return None
        if not (tod_name in self.dict[movement_id].keys()):
            return None
        return self.dict[movement_id][tod_name]

    def to_dict(self):
        overall_output_dict = {}
        for movement_id, movement_dict in self.dict.items():
            overall_output_dict[movement_id] = {}
            for tod_id, movement_tod_curve in movement_dict.items():
                overall_output_dict[movement_id][tod_id] = movement_tod_curve.to_dict()
        overall_output_dict = {"date_list": self.date_list, "movements": overall_output_dict,
                               "resolution": self.resolution, "repeats": self.departure_repeats,
                               "tod_dict": self.tod_dict}
        return overall_output_dict

    def to_df(self, attributes, tod_list=None):
        """

        :param attributes: do not include movement id & tod name
        :param tod_list:
        :return:
        """
        essential_attributes = ["movement_id", "tod_name"]
        all_attributes = essential_attributes + attributes
        overall_dict = {}
        for attr in all_attributes:
            overall_dict[attr] = []

        for movement_id, movement_curve_dict in self.dict.items():
            for tod_name, movement_curve in movement_curve_dict.items():
                if tod_list is not None:
                    if not (tod_name in tod_list):
                        continue
                for attr in all_attributes:
                    overall_dict[attr].append(getattr(movement_curve, attr))
        return pd.DataFrame(overall_dict)

    def from_dict(self, input_dict):
        self.date_list = input_dict['date_list']
        self.resolution = input_dict['resolution']
        self.departure_repeats = input_dict['repeats']
        self.tod_dict = input_dict['tod_dict']
        overall_movements_dict = input_dict['movements']
        for movement_id, movement_dict in overall_movements_dict.items():
            for tod, movement_curve_dict in movement_dict.items():
                movement_curve = MovementTOD().from_dict(movement_curve_dict)
                self.add_movement_tod_curve(movement_curve)
        return self

    def update_movement(self, other):
        """
        update movement

        :param other: other same class with
        :return:
        """
        self.dict.update(other.dict)
        return self

    def aggregate(self, other):
        """
        aggregate this class from different dates!

        :param other: the same dict with different dates
        :return:
        """
        new_cls = MovementNetDict()
        new_cls.date_list = self.date_list + other.date_list
        if self.resolution != other.resolution:
            raise ValueError(f"Two dict should have the same resolution:"
                             f" {self.date_list} with {self.resolution} and"
                             f" {other.date_list} with {other.resolution}")
        new_cls.resolution = self.resolution
        new_cls.departure_repeats = self.departure_repeats
        new_cls.tod_dict = self.tod_dict
        for movement_id, movement_tod_dict in self.dict.items():
            for tod_id in movement_tod_dict.keys():
                local_curve = self.get_movement_tod_curve(movement_id, tod_id)
                other_curve = other.get_movement_tod_curve(movement_id, tod_id)
                new_curve = local_curve + other_curve
                new_cls.add_movement_tod_curve(new_curve)
        return new_cls

    def merge_minor_origins(self, movement_curve, min_prop=0.05):
        """
        Merge the uncoordinated origins into others
        apply to all the curves including curve list, prob list and predicted list (if existing)

        :param movement_curve:
        :param min_prop:
        :return:
        """
        tod_name = movement_curve.tod_name
        total_trajs = movement_curve.total_trajs

        uncoord_array = None
        uncoord_predict_array = None
        uncoord_prob_array = None
        new_origin_dict = {}
        new_origin_prob_dict = {}
        new_origin_predict_dict = {}
        for origin_movement_id in movement_curve.arrival_curve.origin_curve_dict.keys():
            curve_list = movement_curve.arrival_curve.origin_curve_dict[origin_movement_id]
            origin_trajs = sum(curve_list)
            origin_proportion = origin_trajs / total_trajs
            upstream_movement_curve = self.get_movement_tod_curve(origin_movement_id, tod_name)
            if (upstream_movement_curve is None) or (origin_proportion <= min_prop):
                if uncoord_array is None:
                    uncoord_array = np.array(curve_list)
                else:
                    uncoord_array += np.array(curve_list)

                if origin_movement_id in movement_curve.arrival_curve.origin_prob_dict.keys():
                    local_array = np.array(movement_curve.arrival_curve.origin_prob_dict[origin_movement_id])
                    if uncoord_prob_array is None:
                        uncoord_prob_array = local_array
                    else:
                        uncoord_prob_array += local_array

                if origin_movement_id in movement_curve.arrival_curve.origin_predict_dict.keys():
                    local_array = np.array(movement_curve.arrival_curve.origin_predict_dict[origin_movement_id])
                    if uncoord_predict_array is None:
                        uncoord_predict_array = local_array
                    else:
                        uncoord_predict_array += local_array
            else:
                new_origin_dict[origin_movement_id] = curve_list
                if origin_movement_id in movement_curve.arrival_curve.origin_prob_dict.keys():
                    new_origin_prob_dict[origin_movement_id] = \
                        movement_curve.arrival_curve.origin_prob_dict[origin_movement_id]
                if origin_movement_id in movement_curve.arrival_curve.origin_predict_dict.keys():
                    new_origin_predict_dict[origin_movement_id] = \
                        movement_curve.arrival_curve.origin_predict_dict[origin_movement_id]

        if uncoord_prob_array is not None:
            new_origin_prob_dict['null'] = uncoord_prob_array.tolist()
        if uncoord_array is not None:
            new_origin_dict['null'] = uncoord_array.tolist()
        if uncoord_predict_array is not None:
            new_origin_predict_dict['null'] = uncoord_predict_array.tolist()

        movement_curve.arrival_curve.origin_curve_dict = new_origin_dict
        new_movement_list = []
        for movement_id in new_origin_dict.keys():
            if movement_id == "null":
                continue
            new_movement_list.append(movement_id)
        movement_curve.upstream_movement_list = new_movement_list
        movement_curve.arrival_curve.origin_predict_dict = new_origin_predict_dict
        movement_curve.arrival_curve.origin_prob_dict = new_origin_prob_dict

    def check_network_topology(self):
        """
        Update all the dependencies among movements,
           including upstream movements, conflicting movements, etc.

        :return:
        """
        for movement_id, movement_dict in self.dict.items():
            for tod_name, movement_curve in movement_dict.items():
                # update the upstream movement by the following function
                self.merge_minor_origins(movement_curve, min_prop=0.001)

                # change other dependencies
                conflicting_movement_list = movement_curve.conflicting_movement_list
                if conflicting_movement_list is not None:
                    new_conflicting_movement_list = []
                    for ym in conflicting_movement_list:
                        conflicting_movement = self.get_movement_tod_curve(ym, tod_name)
                        if conflicting_movement is not None:
                            new_conflicting_movement_list.append(ym)
                    movement_curve.conflicting_movement_list = new_conflicting_movement_list

    def __add__(self, other):
        return self.aggregate(other)