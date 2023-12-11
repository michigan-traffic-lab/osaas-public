import numpy as np
from models.metrics import estimate_movement_volumes, \
    estimate_movement_delay
from models.spat_utils import update_movement_capacity_state
from models.pmf_utils import SingleQueuePmf


def update_movement_model(movement_tod, penetration_rate=None,
                          offset=None,
                          resolution=None,
                          departure_cycles=None,
                          permissive_capacity_list=None,
                          num_of_dates=None, lane_number=None,
                          saturation_flow_rate=None,
                          green_time=None,
                          yellow_time=None,
                          clearance_time=None,
                          green_start_shift=None,
                          green_loss=None,
                          cycle_length=None,
                          use_predicted_arrival=False,
                          additional_offset=None,
                          departure_prediction=True,
                          update_prediction=False,
                          binary=False):
    update_hist = False
    update_prob = False

    if additional_offset is not None:
        if additional_offset != movement_tod.additional_offset:
            movement_tod.additional_offset = additional_offset
            update_prediction = True

    if permissive_capacity_list is not None:
        if permissive_capacity_list != movement_tod.permissive_capacity_list:
            movement_tod.permissive_capacity_list = permissive_capacity_list
            update_prediction = True

    if green_start_shift is not None:
        if green_start_shift != movement_tod.green_start_shift:
            movement_tod.green_start_shift = green_start_shift
            update_prediction = True

    if green_loss is not None:
        if green_loss != movement_tod.effective_green_change:
            movement_tod.effective_green_change = green_loss
            update_prediction = True

    if departure_cycles is not None:
        if departure_cycles != movement_tod.departure_cycles:
            movement_tod.departure_cycles = departure_cycles
            update_hist = True
    if offset is not None:
        if offset != movement_tod.offset:
            movement_tod.offset = offset
            update_hist = True
    if resolution is not None:
        if resolution != movement_tod.resolution:
            movement_tod.resolution = resolution
            update_hist = True
    if cycle_length is not None:
        if cycle_length != movement_tod.cycle_length:
            movement_tod.cycle_length = cycle_length
            update_hist = True
    if penetration_rate is not None:
        if penetration_rate != movement_tod.penetration_rate:
            movement_tod.penetration_rate = penetration_rate
            update_prob = True
    if num_of_dates is not None:
        if num_of_dates != movement_tod.number_of_dates:
            movement_tod.number_of_dates = num_of_dates
            update_prob = True
    if lane_number is not None:
        if lane_number != movement_tod.equivalent_lane_number:
            movement_tod.equivalent_lane_number = lane_number
            update_prob = True
    if saturation_flow_rate is not None:
        if saturation_flow_rate != movement_tod.sat_flow_per_lane:
            movement_tod.sat_flow_per_lane = saturation_flow_rate
            update_prob = True
    if green_time is not None:
        if green_time != movement_tod.green_time:
            movement_tod.green_time = green_time
            update_prediction = True
    if yellow_time is not None:
        if yellow_time != movement_tod.yellow_change_interval:
            movement_tod.yellow_change_interval = yellow_time
            update_prediction = True
    if clearance_time is not None:
        if clearance_time != movement_tod.clearance_interval:
            movement_tod.clearance_interval = clearance_time
            update_prediction = True

    if use_predicted_arrival:
        update_prediction = True

    if update_hist:
        _update_movement_hist_curves(movement_tod)

    if update_hist or update_prob:
        _update_movement_prob_curves(movement_tod)

    if binary:
        movement_tod.binary_green = True
        update_prediction = True

    if update_hist or update_prob or update_prediction:
        if movement_tod.penetration_rate is not None:
            if departure_prediction:
                _departure_curve_prediction(movement_tod,
                                            use_predicted_arrival=use_predicted_arrival)
    return movement_tod.predicted_delay


def _departure_curve_prediction(movement_tod, maximum_steps=15,
                                stopping_criteria=1e-6,
                                use_predicted_arrival=False):
    """
    departure curve models given the arrival curve

    :param maximum_steps:
    :param use_predicted_arrival:
    :return:
    """
    update_movement_capacity_state(movement_tod)
    # predict the departure curve given the current
    departure_dim = movement_tod.departure_curve.dimension
    predict_departure_list = [0 for _ in range(departure_dim)]

    prv_metric = None
    for i_step in range(maximum_steps):
        predict_departure_list = \
            _departure_prediction_step(movement_tod, predict_departure_list,
                                       use_predicted_arrival=use_predicted_arrival)
        current_metric = movement_tod.predicted_delay
        if prv_metric is not None:
            if abs(current_metric - prv_metric) / max(prv_metric, 1) <= stopping_criteria:
                break
        prv_metric = current_metric

    movement_tod.departure_curve.agg_curves()
    movement_tod.hourly_volume = estimate_movement_volumes(movement_tod, prob=True)


def _get_occupied_probability(departure_list,
                              current_index,
                              cycle_counts):
    max_repeat = 3
    occupied_prob = 0
    for i_r in range(max_repeat):
        cursor_index = (i_r + 1) * cycle_counts + current_index
        if cursor_index < len(departure_list):
            occupied_prob += departure_list[cursor_index]
    return occupied_prob


def _departure_prediction_step(movement_tod, previous_departure_list,
                               use_predicted_arrival=False,
                               stop_min_residual=3):
    """

    :param previous_departure_list:
    :param use_predicted_arrival:
    :param stop_min_residual:
    :return:
    """
    departure_dim = movement_tod.departure_curve.dimension
    arrival_dim = movement_tod.arrival_curve.dimension

    if use_predicted_arrival:
        arrival_prob_list = movement_tod.arrival_curve.predict_list
        if arrival_prob_list is None:
            arrival_prob_list = movement_tod.arrival_curve.prob_list
    else:
        arrival_prob_list = movement_tod.arrival_curve.prob_list
    predict_departure_list = []

    total_stops = 0
    cum_arrival_pmf = SingleQueuePmf()
    pmf_list = []
    capacity_state_list = movement_tod.capacity_state_list

    eff_capacity_list = []
    for i_step in range(departure_dim):
        # this is the maximum capacity allowed at this timestep
        capacity_state = capacity_state_list[i_step]

        # probability that there are some residual vehicles
        residual_prob = cum_arrival_pmf.get_prob(stop_min_residual)
        # probability that there is not occupied by the vehicle from previous cycle departing
        occupied_prob = _get_occupied_probability(previous_departure_list, i_step, arrival_dim)
        release_capacity = capacity_state - occupied_prob
        eff_capacity_list.append(release_capacity)

        # new arrival
        if i_step < arrival_dim:
            arrival_rate = arrival_prob_list[i_step]
            # probability that this arrival can directly pass: no residual and not occupied
            direct_pass_prob = release_capacity * (1 - residual_prob)
            stop_prob = arrival_rate * (1 - direct_pass_prob)
            total_stops += stop_prob
            cum_arrival_pmf.arrival_step(arrival_rate)

        # new departure
        if capacity_state > 0:
            new_departure_prob = cum_arrival_pmf.departure_step(release_capacity)
            predict_departure_list.append(new_departure_prob)
        else:
            predict_departure_list.append(0)
        pmf_list.append(cum_arrival_pmf.pmf_list)
    movement_tod.eff_capacity_list = eff_capacity_list

    # put the not served to the end
    not_served = sum(arrival_prob_list) - sum(predict_departure_list)
    predict_departure_list[-1] += not_served

    # update the results
    movement_tod.predicted_stop_ratio = total_stops / max(sum(arrival_prob_list) * 1.0, 0.0001)
    movement_tod.departure_curve.predict_list = predict_departure_list
    movement_tod.predicted_delay = estimate_movement_delay(movement_tod, departure_predict=True,
                                                           arrival_predict=use_predicted_arrival)

    movement_tod.pmf_list = pmf_list
    movement_tod.departure_calibration_error = movement_tod.departure_curve.get_prediction_error(norm=2)
    return predict_departure_list


def _update_movement_hist_curves(movement_tod):
    """
    Update the histograms given spat information (offset & cycle length)

    :return:
    """
    movement_tod.arrival_curve.dimension = int(np.ceil(movement_tod.cycle_length / movement_tod.resolution))
    movement_tod.departure_curve.dimension = movement_tod.arrival_curve.dimension * movement_tod.departure_cycles
    movement_tod.departure_curve.extend_cycles = movement_tod.departure_cycles
    origin_curve_dict = {}
    for origin_id, time_list in movement_tod.arrival_curve.raw_data_dict.items():
        curve_list = [0 for _ in range(movement_tod.arrival_curve.dimension)]
        for arrival_time in time_list:
            arrival_time -= movement_tod.offset
            time_in_cycle = arrival_time % movement_tod.cycle_length
            cycle_index = int(time_in_cycle / movement_tod.resolution)
            if cycle_index >= movement_tod.arrival_curve.dimension:
                cycle_index = movement_tod.arrival_curve.dimension - 1
            curve_list[cycle_index] += 1
        origin_curve_dict[origin_id] = curve_list
    movement_tod.arrival_curve.origin_curve_dict = origin_curve_dict

    arrival_curve_list = [0 for _ in range(movement_tod.arrival_curve.dimension)]
    departure_curve_list = [0 for _ in range(movement_tod.departure_curve.dimension)]
    for idx in range(len(movement_tod.arrival_curve.raw_data_list)):
        arrival_time = movement_tod.arrival_curve.raw_data_list[idx]
        departure_time = movement_tod.departure_curve.raw_data_list[idx]
        arrival_time -= movement_tod.offset
        arrival_time_in_cycle = arrival_time % movement_tod.cycle_length
        shift_time = arrival_time - arrival_time_in_cycle
        departure_time_in_cycle = departure_time - shift_time - movement_tod.offset
        arrival_index = int(arrival_time_in_cycle / movement_tod.resolution)
        if arrival_index >= movement_tod.arrival_curve.dimension:
            arrival_index = movement_tod.arrival_curve.dimension - 1
        arrival_curve_list[arrival_index] += 1

        departure_index = int(departure_time_in_cycle / movement_tod.resolution)
        if departure_index >= movement_tod.departure_curve.dimension:
            departure_index = movement_tod.departure_curve.dimension - 1
        departure_curve_list[departure_index] += 1

    movement_tod.arrival_curve.curve_list = arrival_curve_list
    movement_tod.departure_curve.curve_list = departure_curve_list
    movement_tod.hist_avg_delay = estimate_movement_delay(movement_tod, prob=False)
    movement_tod.departure_curve.agg_curves()


def _update_movement_prob_curves(self):
    """
    update the scaled probability given the number of date, penetration rate and lane number
    This function should be called once the following parameters changed:
       cycle length, number of dates, lane number, sat flow, penetration

    :return:
    """
    penetration_rate = self.penetration_rate
    if penetration_rate is None:
        return
    lane_number = self.equivalent_lane_number
    sat_flow_per_lane = self.sat_flow_per_lane

    total_cycles_daily = (self.tod_interval[-1] - self.tod_interval[0]) * 3600 / self.cycle_length
    overall_cycles = total_cycles_daily * self.number_of_dates * self.resolution
    interval_max_arrival = sat_flow_per_lane * lane_number / 3600
    scale_coefficient = 1 / max(penetration_rate * overall_cycles * interval_max_arrival, 1e-3)
    self.arrival_curve.update_prob_curve(scale_coefficient)
    self.departure_curve.update_prob_curve(scale_coefficient)
