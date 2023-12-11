"""
Utility functions for operating list (arrival & departure curves)

"""

import numpy as np
from scipy.integrate import quad
import math


def curve_time_integral(curve_list):
    """
    Get the cumulative summation of a list.

    :param curve_list:
    :return:
    """
    total_integral = 0
    integral_list = []
    for idx in range(len(curve_list)):
        total_integral += (idx + 1) * curve_list[idx]
        integral_list.append(total_integral)
    return integral_list


def get_optimal_shift(target_list, est_list, accurate_mode=False):
    """
    Get the optimal shift between two list

    :param target_list:
    :param est_list:
    :param accurate_mode:
    :return:
    """
    shift_start = 0
    shift_end = len(target_list) - 1
    optimal_shift, error = _get_optimal_shift(target_list, est_list, shift_start, shift_end, resolution=1)
    if accurate_mode:
        optimal_shift, error = _get_optimal_shift(target_list, est_list,
                                                  optimal_shift - 1, optimal_shift + 1, resolution=0.2)
    return optimal_shift, error


def _get_optimal_shift(target_list, moving_list,
                       shift_start, shift_end, resolution):
    test_shift_list = np.arange(shift_start, shift_end, resolution)
    error_list = []
    for test_shift in test_shift_list:
        new_curve = shift_list_by_val(moving_list, test_shift)
        local_error = np.array(new_curve) - np.array(target_list)
        local_error = np.sum(np.sqrt(np.square(local_error)))
        error_list.append(local_error / sum(target_list))
    min_error_index = int(np.argmin(error_list))
    best_shift = test_shift_list[min_error_index]
    minimum_cost = error_list[min_error_index]
    return best_shift, minimum_cost


def shift_list_by_val(input_list, shift_interval=0.0):
    """
    Shift a list by certain value

    :param input_list:
    :param shift_interval:
    :return:
    """
    shift_interval %= len(input_list)
    integer_part = int(shift_interval)
    proportion_part = shift_interval - integer_part
    list1 = input_list[- integer_part:] + input_list[:- integer_part]
    list2 = input_list[- integer_part - 1:] + input_list[:- integer_part - 1]

    new_list = np.array(list1) * (1 - proportion_part) + np.array(list2) * proportion_part
    new_list = new_list.tolist()
    return new_list


def gaussian_cdf(x, mu=2.5, var=1):
    erf = (x - mu) / (var * math.sqrt(2))
    cd = 1 / 2 * (1 + math.erf(erf))
    return cd


DEFAULT_GREEN_START_MU = 2.5
DEFAULT_GREEN_START_VAR = 1


def cum_normal_green_start(green_start, time, resolution,
                           mu=DEFAULT_GREEN_START_MU, var=DEFAULT_GREEN_START_VAR):
    green_start = green_start * resolution
    green_start_time = time - green_start
    green_end_time = green_start_time + resolution
    if green_start_time == 0:
        green_start_time -= 1
    prob = quad(gaussian_cdf, green_start_time, green_end_time, args=(mu, var))
    return prob[0] / resolution


def cum_normal_abnormal_green_start(difference, resolution,
                                    mu=DEFAULT_GREEN_START_MU,
                                    var=DEFAULT_GREEN_START_VAR):
    prob = quad(gaussian_cdf, -1, difference, args=(mu, var))
    return prob[0] / resolution


def agg_curves(curve_list, dimension, extend_cycles):
    """
    aggregate the departure curve to the first cycle

    :param curve_list:
    :param dimension:
    :param extend_cycles:
    :return:
    """
    dim1 = int(dimension / extend_cycles)
    repeat = extend_cycles
    agg_array = None
    for i_p in range(int(repeat)):
        local_array = np.array(curve_list[i_p * dim1: i_p * dim1 + dim1]).astype(np.float64)
        if agg_array is None:
            agg_array = local_array
        else:
            agg_array += local_array
    return agg_array.tolist()


def lane_and_sat_depart_adjustment(adjust_curve, adjust_departure):
    adjustment_factor = (adjust_curve.sat_flow_per_lane / 1800) * \
                        (adjust_curve.equivalent_lane_number / 1)
    adjust_departure = [i * adjustment_factor for i in adjust_departure]
    return adjust_departure
