import numpy as np
from models.curve_utils import get_optimal_shift, shift_list_by_val


def arrival_curve_calibration(curve_dict, tod_name=None):
    """
    Arrival curve calibration:

    :param curve_dict:
    :param tod_name:
    :return:
    """
    for movement_id, movement_curve_dict in curve_dict.dict.items():
        for local_tod, movement_curve in movement_curve_dict.items():
            if tod_name is not None:
                if local_tod != tod_name:
                    continue
            movement_arrival_calibration(curve_dict, movement_curve, debug_mode=False)
    return curve_dict


def movement_arrival_calibration(net_dict, movement_curve, debug_mode=False,
                                 use_prob=True, upstream_predict=False,
                                 output_path=None):
    """
    Arrival parameter calibration, get the upstream list

    :param net_dict:
    :param movement_curve:
    :param debug_mode:
    :param use_prob:
    :param upstream_predict:
    :param output_path:
    :return:
    """
    net_dict.merge_minor_origins(movement_curve)
    tod_name = movement_curve.tod_name

    for origin_movement_id in movement_curve.arrival_curve.origin_curve_dict.keys():
        if origin_movement_id == "null":
            continue
        upstream_movement_curve = net_dict.get_movement_tod_curve(movement_id=origin_movement_id,
                                                                  tod_name=tod_name)
        if not use_prob:
            upstream_departure_list = upstream_movement_curve.departure_curve.agg_curve_list
            downstream_arrival_list = movement_curve.arrival_curve.origin_curve_dict[origin_movement_id]
        else:
            upstream_departure_list = upstream_movement_curve.departure_curve.agg_prob_list
            downstream_arrival_list = movement_curve.arrival_curve.origin_prob_dict[origin_movement_id]

        if upstream_predict:
            upstream_departure_list = upstream_movement_curve.departure_curve.agg_predict_list
            if upstream_departure_list is None:
                upstream_departure_list = upstream_movement_curve.departure_curve.agg_prob_list

        diverge_proportion = sum(downstream_arrival_list) / max(sum(upstream_departure_list), 0.1)
        diverge_proportion = min(max(diverge_proportion, 0), 1)

        scaled_upstream_departure = np.array(upstream_departure_list) * diverge_proportion
        scaled_upstream_departure = scaled_upstream_departure.tolist()
        optimal_shift, error = get_optimal_shift(downstream_arrival_list, scaled_upstream_departure)
        predicted_arrival_list = shift_list_by_val(scaled_upstream_departure, optimal_shift)

        movement_curve.origin_diverge_dict[origin_movement_id] = float(diverge_proportion)
        movement_curve.origin_shift_dict[origin_movement_id] = int(optimal_shift)
        movement_curve.origin_error_dict[origin_movement_id] = float(error)

        # movement_curve.arrival_curve.origin_prob_dict[origin_movement_id] = predicted_arrival_list
        if debug_mode:
            import matplotlib.pyplot as plt
            plt.figure(figsize=[5, 4])
            # plt.plot(movement_curve.arrival_curve.prob_list, label="Overall prob")
            plt.bar([val * movement_curve.resolution for val in range(len(downstream_arrival_list))],
                    downstream_arrival_list,
                    width=movement_curve.resolution,
                    edgecolor="k",
                    color="r", label="Downstream arrival", alpha=0.3)
            plt.bar([val * movement_curve.resolution for val in range(len(downstream_arrival_list))]
                    , upstream_departure_list,
                    edgecolor="k",
                    width=movement_curve.resolution,
                    color="b", label="Upstream departure", alpha=0.3)
            # plt.plot(scaled_upstream_departure, "g.--", label="Scaled upstream departure")
            plt.plot([val * movement_curve.resolution for val in range(len(downstream_arrival_list))],
                     predicted_arrival_list, "r.--", label="Transformed curve")

            # plt.plot([], [], alpha=0, label=f"Upstream: {origin_movement_id}\n"
            #                                 f"Downstream: {movement_curve.movement_id}")
            # plt.plot(est_arrival_curve, "b.--", label='Estimation')

            print(f"Prop={np.round(diverge_proportion, 3)}, "
                  f"shift={optimal_shift}, error={np.round(error, 3)}")
            plt.xlabel("Time in a cycle (s)", fontsize=14)
            plt.ylabel("Number of trajectories", fontsize=14)
            plt.grid()
            plt.legend()
            plt.tight_layout()
            if output_path is not None:
                plt.savefig(output_path / f"arrival_calibration_{origin_movement_id}.svg")
            plt.show()

