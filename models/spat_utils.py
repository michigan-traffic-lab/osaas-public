"""
This file contains utility function of spat & departure capacity of movements

Basically, to
- fetch traffic signal state from SPaT data
- update the departure capacity for permissive movements
"""

import numpy as np
from models.curve_utils import shift_list_by_val, cum_normal_green_start, cum_normal_abnormal_green_start, \
    DEFAULT_GREEN_START_MU


def update_movement_capacity_state(movement_tod, permissive=1.0):
    """
    This is to get the actual capacity list given the traffic signal state & permissive capacity

    :param movement_tod:
    :param permissive:
    :return:
    """
    update_movement_signal_state(movement_tod)

    departure_dim = movement_tod.departure_curve.dimension
    if movement_tod.permissive_capacity_list is None:
        conflicting_capacity_list = [0 for _ in range(departure_dim)]
    else:
        conflicting_capacity_list = movement_tod.permissive_capacity_list

    capacity_state_list = []
    for i_step in range(departure_dim):
        signal_state = movement_tod.signal_state_list[i_step]
        conflicting_state = conflicting_capacity_list[i_step]

        # determine the capacity state based on the permissive type
        # will need to add logic for lt_protected_permissive
        if movement_tod.permissive_type == 'lt_turn_permissive':
            # fixme: this is more complicated than we thought, for the left-turn, there are many cases:
            #  1) protected green time
            #  2) permissive green time
            #  3) "red time" in SPaT but essentially permissive green

            if signal_state > 0:
                capacity_state = conflicting_state * permissive
            else:
                capacity_state = signal_state
        else:
            capacity_state = max(conflicting_state, signal_state)

        # this is the maximum capacity allowed at this timestep
        capacity_state_list.append(capacity_state)
    movement_tod.capacity_state_list = capacity_state_list


def update_movement_signal_state(movement_tod):
    signal_state_list = []
    for i_t in range(movement_tod.departure_curve.dimension):
        signal_state = _get_signal_state(movement_tod, i_t * movement_tod.resolution)
        signal_state_list.append(signal_state)
    # shift signal state according to the distance to the center of the intersection
    # the shift will round down to the nearest integer after converting to resolution
    # todo shifting twice right now
    signal_state_list = shift_list_by_val(signal_state_list,
                                          (movement_tod.additional_offset +
                                           movement_tod.green_start_shift) / movement_tod.resolution)
    movement_tod.signal_state_list = signal_state_list
    return signal_state_list


def _get_signal_state(movement_tod, t, lost_time_shift=1):
    """
    t can only be integer number of resolutions

    :param t
    :param lost_time_shift todo what is this?
    :return:
    """
    interval_in_cycle = t % movement_tod.cycle_length / movement_tod.resolution
    time_in_cycle = interval_in_cycle * movement_tod.resolution
    for green in movement_tod.green_time:
        if movement_tod.binary_green:
            # only use for paper figure
            if green[0] + DEFAULT_GREEN_START_MU <= time_in_cycle < \
                    green[0] + green[1] - (movement_tod.yellow_change_interval / 2):
                return 1
            else:
                return 0
        green_start = (green[0] + movement_tod.green_start_shift) / movement_tod.resolution
        green_end = (green[0] + green[1] + movement_tod.effective_green_change +
                     movement_tod.green_start_shift) / movement_tod.resolution
        # exceed_cycle = green_end - self.cycle_length
        # if exceed_cycle > 0:

        green_start_ceil = np.ceil(green_start)
        # green_end_floor = np.floor(green_end)
        lost_time_start = green_end - (movement_tod.yellow_change_interval +
                                       movement_tod.clearance_interval) / movement_tod.resolution
        lost_time_start = lost_time_start + lost_time_shift / movement_tod.resolution
        # calculate during the yellow at all red when interval is abnormal
        if interval_in_cycle + 1 > lost_time_start > interval_in_cycle:
            return 1 - cum_normal_abnormal_green_start((interval_in_cycle + 1 - lost_time_start) * movement_tod.resolution,
                                                       movement_tod.resolution, mu=movement_tod.yellow_change_interval / 2)

        # calculate start when interval in cycle = lost_time_start
        if green_start_ceil <= interval_in_cycle < lost_time_start:
            # no start up loss time needed for protected left turn after permissive movement
            if movement_tod.permissive_type == 'lt_turn_protected':
                return 1
            return cum_normal_green_start(green_start, time_in_cycle, movement_tod.resolution)

        # calculate start when interval is abnormal
        if interval_in_cycle + 1 > green_start > interval_in_cycle:
            # no start up loss time needed for protected left turn after permissive movement
            if movement_tod.permissive_type == 'lt_turn_protected':
                return 1
            return cum_normal_abnormal_green_start((interval_in_cycle + 1 - green_start) * movement_tod.resolution,
                                                   movement_tod.resolution)
        # calculate during the yellow and all red with interval in cycle = lost_time_start
        if lost_time_start <= interval_in_cycle < green_end:
            return 1 - cum_normal_green_start(lost_time_start, time_in_cycle, movement_tod.resolution,
                                              mu=movement_tod.yellow_change_interval / 2)

        # not sure about this
        if interval_in_cycle < green_end < interval_in_cycle + 1:
            return green_end - interval_in_cycle
    return 0
