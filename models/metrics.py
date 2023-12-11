"""
This file is to derive delay metrics from network & movement
"""


import numpy as np
from models.curve_utils import curve_time_integral


def estimate_movement_volumes(movement_tod, prob=True):
    """
    Traffic volume estimation based on the prob list of arrival

    :param prob:
    :return:
    """
    if prob:
        arrival_per_cycle = sum(movement_tod.arrival_curve.prob_list) *\
                            movement_tod.resolution * movement_tod.equivalent_lane_number
        arrival_rate = arrival_per_cycle / movement_tod.cycle_length
        traffic_volume = 3600 * arrival_rate
        return traffic_volume
    else:
        raise NotImplementedError


def estimate_movement_delay(movement_tod, prob=False,
                            departure_predict=False,
                            arrival_predict=False,
                            disp=False):
    """
    calculating delay from departure arrival curves

    :param prob:
    :param departure_predict:
    :param arrival_predict:
    :param disp:
    :return:
    """
    arrival_list, departure_list, normalize = \
        movement_tod.get_arrival_departure_curves(prob, departure_predict, arrival_predict)

    cumulative_departure = curve_time_integral(departure_list)
    cumulative_arrival = curve_time_integral(arrival_list)
    total_delay = cumulative_departure[-1] - cumulative_arrival[-1]

    total_delay *= movement_tod.resolution
    avg_delay = total_delay / max(normalize, 1)

    if disp:
        print('-------------')
        print(sum(arrival_list) - sum(departure_list), normalize)
        print("Arrival", arrival_list)
        print("Departure", departure_list)
        print("Total_delay", total_delay)
        print("Average delay", avg_delay)
    return avg_delay


def get_movement_calibration_diff(movement_tod, stop_weight=30):
    """
    Calibration error
    Current metric: difference of the control delay + average number of stops * 30

    :return:
    """
    predicted_stop = movement_tod.predicted_stop_ratio
    predicted_delay = movement_tod.predicted_delay
    predicted_val = predicted_stop * stop_weight + predicted_delay
    ground_truth_val = movement_tod.total_control_delay / max(movement_tod.total_trajs, 1)
    ground_truth_val += (movement_tod.total_stopped_trajs * stop_weight) / max(movement_tod.total_trajs, 1)
    residual = predicted_val - ground_truth_val
    return residual
