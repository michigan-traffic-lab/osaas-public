"""
This file is for the overall prediction of a network
"""
from __future__ import annotations
from time import time
import numpy as np
from models.movement_model import update_movement_model
from models.net_calibration import arrival_curve_calibration
from models.curve_utils import shift_list_by_val, agg_curves, lane_and_sat_depart_adjustment
from models.metrics import get_movement_calibration_diff

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .net_dict_classes import MovementNetDict


def update_network_prediction(curve_dict: MovementNetDict,
                              tod_name: str,
                              offset_dict: dict = None,
                              green_dict: dict | None = None,
                              cycle_dict: dict = None,
                              global_cycle=None,
                              global_p=None,
                              p_dict=None,
                              through_cost_only=False,
                              dependency_loop=False,
                              use_predicted_arrival=True,
                              max_super_iterations=5,
                              super_stopping_criteria=1e-8,
                              retry_with_loop=True,
                              disp=False):
    """
    Update the overall prediction results.
    todo: this is not finished yet

    :param curve_dict:
    :param tod_name:
    :param offset_dict: {"junction_id": additional_offsets, ...}
    :param green_dict: {"movement_id": green_list}
    :param cycle_dict: {"junction_id": cycle_length}, has higher priority than global_cycle
    :param global_cycle:
    :param global_p: global penetration rate
    :param p_dict: {"movement_id": penetration_rate}, has higher priority than global_p
    :param through_cost_only:
    :param dependency_loop:
    :param use_predicted_arrival:
    :param max_super_iterations:
    :param super_stopping_criteria:
    :param retry_with_loop
    :param disp: display the information
    :return: overall calibration difference (predicted stop/delay minus ground truth)
    """
    start_time = time()
    # If the dependency loop is already set as True, no need to retry
    sup_separate = "=" * 100
    separate = "~" * 100
    sub_separate = "-" * 100

    overall_movements_number = len(curve_dict.dict.keys())
    if disp:
        print(sup_separate)
        print("Overall network prediction program start...")
        print(f"Overall number of movements: {overall_movements_number}")
        print(f"Through cost only: {through_cost_only}")
        print(f"Dependency loop mode: {dependency_loop}")
        if not dependency_loop:
            print(f"Retry if there is a dependency loop: {retry_with_loop}")

    if dependency_loop:
        retry_with_loop = False

    if offset_dict is None:
        offset_dict = {}
    if green_dict is None:
        green_dict = {}
    if cycle_dict is None:
        cycle_dict = {}

    # Set the penetration first to scale the prob curve,
    # we need to set the arrival calibration as True
    # since the penetration rate will influence the diverge proportion
    _set_penetration_rate(curve_dict, tod_name, global_p, p_dict,
                          arrival_calibration=True)

    augment_processed_list = []
    if dependency_loop:
        augment_processed_list = _through_movements_update(curve_dict, tod_name)
        if disp:
            print(f"Use dependency loop mode, augmented processed movements: {augment_processed_list}")

    total_calibration_diff = 0
    prv_movement_metric_dict = {}

    for super_iter in range(max_super_iterations):
        if disp:
            print(separate)
            print(f"Super iteration {super_iter}")
        processed_movement_list = []  # list for processed movement list
        total_calibration_diff = 0
        remaining_movements = len(curve_dict.dict)
        movement_metric_dict = {}
        use_prv_conflicting = False
        unprocessed_movement_dict = {}

        for _ in range(overall_movements_number):
            unprocessed_movement_dict = {}
            remaining_movements = 0
            processed_this_round = []
            for movement_id, movement_curve_dict in curve_dict.dict.items():
                if movement_id in processed_movement_list:
                    continue
                remaining_movements += 1
                for local_tod, movement_curve in movement_curve_dict.items():
                    if local_tod != tod_name:
                        continue

                    upstream_movement_list = movement_curve.upstream_movement_list
                    conflicting_movement_list = movement_curve.conflicting_movement_list
                    upstream_ready = _isin(upstream_movement_list, processed_movement_list)
                    conflicting_ready = _isin(conflicting_movement_list, processed_movement_list)
                    conflicting_augment_ready = _isin(conflicting_movement_list,
                                                      processed_movement_list + augment_processed_list)
                    if movement_curve.movement_index % 2 == 1:
                        upstream_augment_ready = _isin(upstream_movement_list,
                                                       processed_movement_list + augment_processed_list)
                    else:
                        upstream_augment_ready = upstream_ready

                    if use_prv_conflicting:
                        _proceed_to_calculate = (upstream_augment_ready and conflicting_augment_ready)
                    else:
                        _proceed_to_calculate = (upstream_ready and conflicting_ready)
                    if not _proceed_to_calculate:
                        unprocessed_movement_dict[movement_id] = {}
                        if not upstream_ready:
                            unprocessed_movement_dict[movement_id]["upstream"] = upstream_movement_list
                        if not conflicting_ready:
                            unprocessed_movement_dict[movement_id]["conflicting"] = conflicting_movement_list
                    else:
                        if movement_curve.junction_id in offset_dict.keys():
                            movement_curve.additional_offset = offset_dict[movement_curve.junction_id]

                        new_cycle_length = global_cycle
                        if movement_curve.junction_id in cycle_dict.keys():
                            new_cycle_length = cycle_dict[movement_curve.junction_id]

                        new_green_info = None
                        if movement_id in green_dict.keys():
                            new_green_info = green_dict[movement_id]

                        # get the arrival from the upstream
                        # todo we need to be able to adjust cycle length here
                        # todo have to be careful about cycle lengths from upstream (TODs from upstream)
                        if use_predicted_arrival:
                            _movement_arrival_prediction(curve_dict, movement_curve, from_upstream=True,
                                                         from_upstream_prediction=True)
                        # get the permissive capacity from the conflicted movements
                        _update_movement_permissive_capacity_list(curve_dict, movement_curve,
                                                                  use_prediction=True,
                                                                  debug=False)

                        # departure prediction
                        update_movement_model(movement_curve, green_time=new_green_info,
                                              cycle_length=new_cycle_length,
                                              use_predicted_arrival=use_predicted_arrival)
                        processed_movement_list.append(movement_id)
                        processed_this_round.append(movement_id)

                        if through_cost_only:
                            if not (movement_curve.movement_index in [2, 4, 6, 8]):
                                continue
                        # local_calibration_diff = movement_curve.get_calibration_diff() * movement_curve.hourly_volume
                        local_calibration_diff = get_movement_calibration_diff(movement_curve) * \
                                                 movement_curve.total_trajs
                        local_calibration_diff /= 3600  # convert second to hour

                        local_delay_metric = movement_curve.predicted_delay + \
                                             movement_curve.predicted_stop_ratio * 30
                        local_delay_metric *= movement_curve.total_trajs
                        movement_metric_dict[movement_id] = local_delay_metric

                        # attention: here is how we set the objective function
                        if local_calibration_diff >= 0:
                            total_calibration_diff += local_calibration_diff * local_calibration_diff
                        else:
                            # a higher penalty is set here
                            total_calibration_diff += local_calibration_diff * local_calibration_diff * 4

            use_prv_conflicting = False
            if remaining_movements == 0:
                break

            if len(processed_this_round) == 0:
                if dependency_loop:
                    if not use_prv_conflicting:
                        if disp:
                            print('[WARNING] remaining movements not reduced, use the'
                                  ' previous conflicting prediction to proceed...')
                        use_prv_conflicting = True
                    else:
                        print('[ERROR] remaining movements not reduced, there is a dead loop '
                              'in the movement dependency...')
                        break
                else:
                    break
                # else:
                if disp:
                    print(sub_separate)
                    print(f"Sub iteration number {_}")
                    print(f"Processed movements this round: {processed_this_round}")
                    processed_number = len(processed_movement_list)
                    print(f"Overall processed movements {processed_number}, "
                          f"unprocessed movements {overall_movements_number - processed_number}")
                    print(f"Use conflicting info from previous iteration {use_prv_conflicting}")

        if remaining_movements > 0:
            if (not retry_with_loop) and dependency_loop:
                print(separate)
                print("Network update error report")

                print(f"Processed {len(processed_movement_list)} v.s. "
                      f"unprocessed {overall_movements_number - len(processed_movement_list)}")
                print(f"Augment processed movements:", augment_processed_list)
                print("Processed movements:", processed_movement_list)
                print("Unprocessed movements and the their dependencies:")
                sscount = 0
                for k, v in unprocessed_movement_dict.items():
                    print(f"Movement {sscount}: {k}, dependencies: {v}")
                    sscount += 1

                print(f"retry_with_loop is set as {retry_with_loop}")
                print(f"dependency_loop is set as {dependency_loop}")
                raise ValueError("Input network topology not correct, some movements are not processed...\n"
                                 "You can set retry_with_loop as True or "
                                 "call .check_network_topology() before running this function")
            else:
                if disp:
                    print("[WARNING] we will retry by setting dependency_loop as True")
                update_network_prediction(curve_dict=curve_dict, tod_name=tod_name,
                                          offset_dict=offset_dict, green_dict=green_dict,
                                          cycle_dict=cycle_dict, global_cycle=global_cycle,
                                          global_p=global_p,
                                          p_dict=p_dict,
                                          through_cost_only=through_cost_only,
                                          dependency_loop=True,
                                          disp=disp)

        metric_diff_ratio = _get_cali_diff(metric_dict1=prv_movement_metric_dict,
                                           metric_dict2=movement_metric_dict,
                                           disp=disp)
        if disp:
            print(f"End of super iteration {super_iter}")
            print(separate)

        if metric_diff_ratio <= super_stopping_criteria:
            if disp:
                print("Terminated super iteration in advance.")
            break
        prv_movement_metric_dict = movement_metric_dict

    if disp:
        print(f"Overall running time: {np.round(time() - start_time, 3)} secs")
        print("End of the overall network prediction")
        print(sup_separate)
    return total_calibration_diff


def _get_cali_diff(metric_dict1, metric_dict2, disp=False):
    if len(metric_dict1) != len(metric_dict2):
        if disp:
            print("Metric 1", metric_dict1.keys())
            print("Metric 2", metric_dict2.keys())
        return 1e6
    else:
        total_metric = 0
        total_diff = 0
        for mid in metric_dict1.keys():
            metric1 = metric_dict1[mid]
            metric2 = metric_dict2[mid]
            total_metric += metric1 * metric1
            total_diff += (metric2 - metric1) ** 2

        diff_ratio = total_diff / total_metric
        if disp:
            print("Total metric:", total_metric)
            print("Total diff:", total_diff)
            print("Diff ratio", total_diff / total_metric)
        return diff_ratio


def _isin(list1, list2):
    if list1 is None:
        return True
    contained = True
    for val in list1:
        if not (val in list2):
            return False
    return contained


def _set_penetration_rate(curve_dict, tod_name=None,
                          global_penetration_rate=None,
                          penetration_rate_dict=None,
                          arrival_calibration=True):
    """
    Set the global penetration rate & update all curve

    :param curve_dict:
    :param tod_name:
    :param penetration_rate_dict:
    :param global_penetration_rate:
    :param arrival_calibration:
    :return:
    """
    if penetration_rate_dict is None:
        penetration_rate_dict = {}

    for movement_id, movement_curve_dict in curve_dict.dict.items():
        for local_tod, movement_curve in movement_curve_dict.items():
            if tod_name is not None:
                if local_tod != tod_name:
                    continue

            if movement_curve.movement_id in penetration_rate_dict.keys():
                penetration_rate = penetration_rate_dict[movement_curve.movement_id]
            elif global_penetration_rate is not None:
                penetration_rate = global_penetration_rate
            else:
                penetration_rate = movement_curve.penetration_rate
            if penetration_rate is None:
                raise ValueError(f"Penetration rate of movement {movement_id} "
                                 f"at {local_tod} is not set correctly "
                                 f"(movement index: {movement_curve.movement_index})")
            update_movement_model(movement_curve, penetration_rate=penetration_rate,
                                  departure_prediction=False)
    if arrival_calibration:
        arrival_curve_calibration(curve_dict, tod_name=tod_name)


def _through_movements_update(curve_dict, tod_name=None):
    """
    update all through movement

    :param curve_dict:
    :param tod_name:
    :return:
    """
    movement_list = []
    for movement_id, movement_curve_dict in curve_dict.dict.items():
        for local_tod, movement_curve in movement_curve_dict.items():
            if tod_name is not None:
                if local_tod != tod_name:
                    continue
            update_movement_model(movement_curve, update_prediction=True,
                                  use_predicted_arrival=False)
            movement_list.append(movement_id)
    return movement_list


def _movement_arrival_prediction(net_dict, movement_curve,
                                 from_upstream=True,
                                 from_upstream_prediction=False):
    """
    Update the movement arrival models curve
    # todo we need to be able to adjust cycle length here

    :param net_dict:
    :param movement_curve:
    :param from_upstream:
    :param from_upstream_prediction:
    :return:
    """
    overall_predicted_list = None
    origin_prob_dict = movement_curve.arrival_curve.origin_prob_dict
    predicted_prob_dict = {}
    for origin_id, origin_list in origin_prob_dict.items():
        if origin_id == "null":
            local_arrival_array = np.array(origin_list)
            local_arrival_array = np.clip(local_arrival_array, 0, 1)
            predicted_prob_dict[origin_id] = origin_list
        else:
            if from_upstream:
                upstream_movement_curve = \
                    net_dict.get_movement_tod_curve(origin_id, movement_curve.tod_name)
                scale_coefficient = movement_curve.origin_diverge_dict[origin_id]
                shift_val = movement_curve.origin_shift_dict[origin_id]
                upstream_departure_curve = upstream_movement_curve.departure_curve
                if from_upstream_prediction:
                    agg_arrival_list = upstream_departure_curve.agg_predict_list
                else:
                    agg_arrival_list = upstream_departure_curve.agg_prob_list
                transformed_arrival_list = shift_list_by_val(agg_arrival_list, shift_val)
                local_arrival_array = np.array(transformed_arrival_list) * scale_coefficient
                local_arrival_array = np.clip(local_arrival_array, 0, 1)
                predicted_prob_dict[origin_id] = local_arrival_array.tolist()
            else:
                shifted_list = origin_list
                local_arrival_array = np.array(shifted_list)
                local_arrival_array = np.clip(local_arrival_array, 0, 1)
                predicted_prob_dict[origin_id] = local_arrival_array.tolist()
        if overall_predicted_list is None:
            overall_predicted_list = local_arrival_array
        else:
            overall_predicted_list += local_arrival_array

    if overall_predicted_list is not None:
        overall_predicted_list = overall_predicted_list.tolist()
        movement_curve.arrival_curve.predict_list = overall_predicted_list
        movement_curve.arrival_curve.origin_predict_dict = predicted_prob_dict
    return overall_predicted_list


def _update_movement_permissive_capacity_list(net_dict, movement_curve,
                                              use_prediction=True,
                                              debug=False):
    """
    get the permissive capacity list given a certain movement

    :param net_dict:
    :param movement_curve:
    :param use_prediction:
    :param debug:
    :return:
    """
    # list of movements the movement_curve must yield to
    conflicting_movement_list = movement_curve.conflicting_movement_list

    # if list is empty no further action needed
    if conflicting_movement_list is None:
        return

    # collect a list of movement tod curves from conflicting movement list
    conflicting_curve_list = []

    for cmd in conflicting_movement_list:
        local_curve = net_dict.get_movement_tod_curve(cmd, movement_curve.tod_name)
        if local_curve is not None:
            conflicting_curve_list.append(local_curve)
    if len(conflicting_curve_list) == 0:
        return None

    arrival_dim = conflicting_curve_list[0].arrival_curve.dimension
    permissive_capacity_list = []
    leftover_capacity_list = []
    conflict_departure_list = None

    # number of time steps during gap acceptance
    vacant_number = int(np.round(movement_curve.gap_acceptance / net_dict.resolution))
    for i_step in range(arrival_dim):

        # conflict sum departure list
        conflict_sum_departure_list = [0 for _ in range(arrival_dim)]

        permissive_state = [0 for _ in range(arrival_dim)]

        for conflict_curve in conflicting_curve_list:
            # retrieve conflict curve signal state
            conflict_signal_state = conflict_curve.signal_state_list

            if use_prediction:
                # need to get rid of the leftover departure models at the end of the list
                # fixme: I might already have this agg_predict_list, check it out, oh, I see,
                #  you might need a special version of the agg curve, why making the last one 0 is essential?
                conflict_departure_list = conflict_curve.departure_curve.predict_list
                conflict_departure_list[-1] = 0
                conflict_departure_list = agg_curves(conflict_departure_list,
                                                     conflict_curve.departure_curve.dimension,
                                                     conflict_curve.departure_curve.extend_cycles)
            else:
                conflict_departure_list = conflict_curve.departure_curve.agg_prob_list

            # adjust saturation and lane scales
            conflict_departure_list = lane_and_sat_depart_adjustment(conflict_curve, conflict_departure_list)

            for predict_step, predict in enumerate(conflict_departure_list):
                # add conflict sum departure
                conflict_sum_departure_list[predict_step] += predict

                # adjust the permissive state to reflect more departures during conflicting movement's all red time
                if conflict_signal_state[predict_step - 1] > conflict_signal_state[predict_step] > 0.01:
                    permissive_state[predict_step] = 1
                else:
                    permissive_state[predict_step] = conflict_signal_state[predict_step]

        vacant_signal_list = [permissive_state[i_step - iv] for iv in range(vacant_number)]
        vacant_departure_list = [conflict_sum_departure_list[i_step - iv] for iv in range(vacant_number)]

        # get the leftover capacity across the gap
        vacant_list = [max(vacant_signal_list[i] - vacant_departure_list[i], 0)
                       for i, signal in enumerate(vacant_signal_list)]
        vacant_probability = np.prod(vacant_list)

        permissive_capacity_list.append(vacant_probability)
        leftover_capacity_list.append(max(permissive_state[i_step] - conflict_sum_departure_list[i_step], 0))

    # I need to add this line to ensure the data type, int32 cannot be converted to json
    permissive_capacity_list = [float(val) for val in permissive_capacity_list]
    leftover_capacity_list = [float(val) for val in leftover_capacity_list]
    permissive_capacity_list *= net_dict.departure_repeats
    leftover_capacity_list *= net_dict.departure_repeats
    movement_curve.permissive_capacity_list = permissive_capacity_list
    movement_curve.leftover_capacity_list = leftover_capacity_list

    if debug:
        import matplotlib
        import matplotlib.pyplot as plt

        # matplotlib.use('TkAGG')
        plt.figure()
        if conflict_departure_list is not None:
            plt.plot(conflict_departure_list, label="Conflicting departure")
        plt.plot(permissive_capacity_list[:arrival_dim], label="Permissive capacity")
        plt.grid()
        plt.title(f"Movement {movement_curve.movement_id},"
                  f" index: {movement_curve.movement_index}")
        plt.legend()
        plt.show()
