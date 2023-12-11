from copy import deepcopy
from models.curve_classes import ArrivalCurve, DepartureCurve


class MovementTOD(object):
    # todo: we need to separate the spat data from the current class
    def __init__(self):
        # basic information
        self.movement_id = None
        self.movement_index = None
        self.direction = None
        self.junction_id = None
        self.tod_interval = None
        self.tod_name = None
        self.resolution = 3
        self.departure_cycles = None
        self.number_of_dates = None

        self.departure_curve = None
        self.arrival_curve = None

        # spat information
        self.cycle_length = None
        self.offset = None
        self.green_time = None
        self.spat_phase = None

        self.additional_offset = 0
        # self.exceed_cycle = None
        self.green_start_shift = 0
        self.effective_green_change = 0
        self.yellow_change_interval = 0
        self.clearance_interval = 0
        self.binary_green = False

        # basic parameters
        self.sat_flow_per_lane = 1800.0
        self.lane_number = 1
        self.equivalent_lane_number = 1
        self.share_lane_movements = []
        self.share_approach_movements = []
        self.same_approach_through_movement = None
        self.upstream_movement_list = []
        self.upstream_length = None

        # permissive movement parameters
        self.conflicting_movement_list = []
        self.permissive_type = None
        self.gap_acceptance = 10
        self.permissive_capacity_list = None
        self.leftover_capacity_list = None
        # self.permissive_type = None
        # self.gap_acceptance = None

        # traffic signal state & capacity list
        self.signal_state_list = None
        self.capacity_state_list = None

        # ground truth parameters
        self.total_trajs = 0
        self.total_stops = 0
        self.total_stopped_trajs = 0
        self.total_control_delay = 0
        self.total_stop_delay = 0
        self.measured_free_v = 0
        self.hist_avg_delay = 0

        # estimated values
        self.pmf_list = None
        self.capacity_list = None
        self.eff_capacity_list = None
        self.penetration_rate = None
        self.departure_calibration_error = None
        self.arrival_calibration_error = None
        self.hourly_volume = None
        self.predicted_delay = 0
        self.predicted_stop_ratio = 0

        self.origin_diverge_dict = {}       # key: origin_id, val: diverge proportion
        self.origin_shift_dict = {}         # key: origin_id, val: shift value (>0)
        self.origin_error_dict = {}

    def get_arrival_departure_curves(self, prob=True,
                                     departure_predict=False,
                                     arrival_predict=False,
                                     smooth_curve=False,
                                     departure_agg=False,
                                     arrival_breakdown=False):
        """
        choose the different curve to perform the calculation

        :param prob:
        :param departure_predict: whether use predicted departure or not,
                if predicted curve is not available, then output the normal curve
        :param arrival_predict: whether use predicted arrival or not
        :param smooth_curve: (not implemented)
        :param departure_agg: whether to aggregate the departure to the same cycle
        :param arrival_breakdown:
        :return:
        """
        if departure_predict:
            if self.departure_curve.predict_list is None:
                departure_predict = False
        if arrival_predict:
            if self.arrival_curve.predict_list is None:
                arrival_predict = False

        if departure_predict or arrival_predict:
            prob = True

        if not prob:
            if arrival_breakdown:
                arrival_list = self.arrival_curve.origin_curve_dict
            else:
                arrival_list = self.arrival_curve.curve_list
            departure_list = self.departure_curve.curve_list
            normalize = self.total_trajs
        else:
            if departure_predict:
                departure_list = self.departure_curve.predict_list
            else:
                departure_list = self.departure_curve.prob_list

            if arrival_predict:
                if arrival_breakdown:
                    arrival_list = self.arrival_curve.origin_predict_dict
                else:
                    arrival_list = self.arrival_curve.predict_list
            else:
                if arrival_breakdown:
                    arrival_list = self.arrival_curve.origin_prob_dict
                else:
                    arrival_list = self.arrival_curve.prob_list
            normalize = sum(departure_list)

        if smooth_curve:
            # todo: add curve smoothing here, very important
            raise NotImplementedError

        if departure_agg:
            # departure_list = self.agg_departure_curve(departure_list)
            if not prob:
                departure_list = self.departure_curve.agg_curve_list
            elif departure_predict:
                departure_list = self.departure_curve.agg_predict_list
            else:
                departure_list = self.departure_curve.agg_prob_list
        return arrival_list, departure_list, normalize

    def to_dict(self):
        output_dict = deepcopy(self.__dict__)
        output_dict["arrival_curve"] = self.arrival_curve.to_dict()
        output_dict["departure_curve"] = self.departure_curve.to_dict()
        return output_dict

    def from_dict(self, input_dict):
        for k, v in input_dict.items():
            if k == 'arrival_curve':
                v = ArrivalCurve().from_dict(v)
            elif k == 'departure_curve':
                v = DepartureCurve().from_dict(v)
            setattr(self, k, v)
        return self

    def deepcopy(self):
        new_cls = MovementTOD()
        for k, v in self.__dict__.items():
            setattr(new_cls, k, deepcopy(v))
        return new_cls

    def append(self, other, inplace=True):
        """
        This function should be updated whenever a new attribute is added

        :param other:
        :param inplace:
        :return:
        """
        if not inplace:
            new_cls = self.deepcopy()
        else:
            new_cls = self

        total_trajs_number = new_cls.total_trajs + other.total_trajs
        if total_trajs_number > 0:
            new_cls.measured_free_v = (new_cls.total_trajs * new_cls.measured_free_v +
                                       other.total_trajs * other.measured_free_v) / total_trajs_number
        new_cls.number_of_dates += other.number_of_dates
        new_cls.total_trajs += other.total_trajs
        new_cls.total_control_delay += other.total_control_delay
        new_cls.total_stops += other.total_stops
        new_cls.total_stop_delay += other.total_stop_delay
        new_cls.arrival_curve = new_cls.arrival_curve + other.arrival_curve
        new_cls.departure_curve = new_cls.departure_curve + other.departure_curve
        new_cls.total_stopped_trajs = new_cls.total_stopped_trajs + other.total_stopped_trajs

        return new_cls

    def __add__(self, other):
        return self.append(other, inplace=False)


