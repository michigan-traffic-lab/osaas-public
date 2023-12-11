"""
Classes for arrival and departure curves

"""

import numpy as np
from copy import deepcopy


class DistributionCurve(object):
    def __init__(self):
        self.raw_data_list = []  # raw data, time within the tod
        self.curve_list = []  # histogram, # of trajectory
        self.prob_list = None  # scaled probability
        self.predict_list = None  # predicted list (departure/arrival prediction)
        self.dimension = None  # length of list

    # def update_prob_curve(self, coefficient):
    #     self.prob_list = coefficient * np.array(self.curve_list)
    #     self.prob_list = self.prob_list.tolist()
    #     # self.prob_list = [val * coefficient for val in self.curve_list]

    def get_prediction_error(self, norm=2):
        error = np.sum(np.abs((np.array(self.prob_list) - np.array(self.predict_list)) ** norm)) ** (1 / norm)
        return error

    def from_dict(self, input_dict):
        for k, v in input_dict.items():
            setattr(self, k, v)
        return self

    # def deepcopy(self, other):
    #     for k, v in other.__dict__.items():
    #         setattr(self, k, deepcopy(v))
    #     return self
    #
    # def append(self, other):
    #     raise NotImplementedError
    #
    # def __add__(self, other):
    #     return self.append(other)


class ArrivalCurve(DistributionCurve):
    def __init__(self):
        super().__init__()
        self.raw_data_dict = {}
        self.origin_curve_dict = {}
        self.origin_prob_dict = {}
        self.origin_predict_dict = {}


class DepartureCurve(DistributionCurve):
    def __init__(self):
        super().__init__()
        self.extend_cycles = None
        self.agg_curve_list = None
        self.agg_prob_list = None
        self.agg_predict_list = None

    def agg_curves(self):
        if self.prob_list is not None:
            if len(self.prob_list) == self.dimension:
                self.agg_prob_list = self._agg_curves(self.prob_list)
        if self.curve_list is not None:
            if len(self.curve_list) == self.dimension:
                self.agg_curve_list = self._agg_curves(self.curve_list)
        if self.predict_list is not None:
            if len(self.predict_list) == self.dimension:
                self.agg_predict_list = self._agg_curves(self.predict_list)

    def _agg_curves(self, curve_list):
        """
        aggregate the departure curve to the first cycle

        :param curve_list:
        :return:
        """
        dim1 = int(self.dimension / self.extend_cycles)
        repeat = self.extend_cycles
        agg_array = None
        for i_p in range(int(repeat)):
            local_array = np.array(curve_list[i_p * dim1: i_p * dim1 + dim1]).astype(np.float64)
            if agg_array is None:
                agg_array = local_array
            else:
                agg_array += local_array
        return agg_array.tolist()
