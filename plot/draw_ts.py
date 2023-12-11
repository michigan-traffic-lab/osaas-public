from pathlib import Path
from typing import Literal, Dict

from matplotlib import pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from mtldp.meta.TrafficNetwork import Arterial

from models.net_dict_classes import MovementNetDict
from pts import pts
from models.movement_tod_classes import MovementTOD

Direction = Literal[-1, 1]


def corridor_time_space_diagram(movement_dict: MovementNetDict, tod_name: str,
                                corridor: Arterial, output_path: Path, prefix: str):
    for direction, oneway in corridor.oneways.items():
        if direction in ["N", "n", "E", "e"]:
            plot_dir: Direction = -1
        else:
            plot_dir: Direction = 1
        movement_dict.direction = direction

        fig, ax = plt.subplots(figsize=(6, 5))
        draw_movement_list_time_space(ax, movement_dict, tod_name,
                                      movement_dis_dict=oneway.distance_by_movement,
                                      direction=plot_dir,
                                      last_downstream_length=35)
        plt.tight_layout()

        fig_path = output_path / f'{prefix}_ts_dir_{direction}.png'
        plt.savefig(fig_path, dpi=300)
        print(f'Saved to `{fig_path}`')
        plt.close()


def draw_movement_list_time_space(ax, movement_dict: MovementNetDict, tod_name: str,
                                  movement_dis_dict: Dict[str, float], direction: Direction,
                                  repeat_cycles: int = 3, last_downstream_length: float = 80):
    prv_distance = 0
    movement_nums = 0
    for movement_id, local_y_distance in movement_dis_dict.items():
        movement_nums += 1
        movement_curve = movement_dict.get_movement_tod_curve(movement_id, tod_name)
        if movement_curve is None:
            continue

        upstream_length = local_y_distance - prv_distance
        upstream_length = max(upstream_length, 20)
        prv_distance = local_y_distance
        if movement_nums == len(movement_dis_dict.keys()):
            downstream_length = last_downstream_length
        else:
            downstream_length = 0

        draw_movement_pts(ax,
                          linewidth=1.5,
                          movement_curve=movement_curve,
                          y_location=local_y_distance * -direction,
                          upstream_length=upstream_length,
                          downstream_length=downstream_length,
                          jam_density=7,
                          repeat_cycles=repeat_cycles,
                          direction=direction,
                          stop_bar_distance=3,
                          upstream_prediction=True)

    y_limit = int(round((prv_distance + last_downstream_length) / 200) * 200)
    if direction == -1:
        ax.set_ylim([0, y_limit])
    else:
        ax.set_ylim([-y_limit, 0])
    ax.set_xlabel('Time (s)', fontsize=14)
    ax.set_ylabel('Distance (m)', fontsize=14)


def draw_movement_pts(ax, linewidth: float,
                      movement_curve: MovementTOD, direction: Literal[1, -1],
                      y_location: float, jam_density: float, repeat_cycles: int,
                      upstream_length: float, downstream_length: float,
                      stop_bar_distance: float, upstream_prediction: bool):
    # Extract data
    segments, alphas = get_pts_components(movement_curve,
                                          upstream_prediction=upstream_prediction,
                                          y_location=y_location,
                                          stop_bar_distance=stop_bar_distance,
                                          jam_density=jam_density,
                                          upstream_length=upstream_length,
                                          downstream_length=downstream_length,
                                          repeat_cycles=repeat_cycles,
                                          direction=direction)
    cycle, offset, green_start, green_end, yellow, red_clearance, red_start = get_signal_info(movement_curve)

    # plot pts
    colors = [(0, 0, 0, _) for _ in alphas]
    trajs = LineCollection(segments, linewidths=linewidth, color=colors)
    ax.add_collection(trajs)

    # plot signal bar
    for i_cycle in range(-2, repeat_cycles + 1):
        zero_shift = offset + movement_curve.additional_offset + i_cycle * cycle
        # Red before green
        ax.plot([zero_shift, zero_shift + green_start], [y_location] * 2, color='r', zorder=3)
        # Green
        ax.plot([zero_shift + green_start, zero_shift + green_end], [y_location] * 2, color='g', zorder=3)
        # Yellow
        ax.plot([zero_shift + green_end, zero_shift + green_end + yellow], [y_location] * 2, color='yellow', zorder=3)
        # Red after yellow
        ax.plot([zero_shift + red_start - red_clearance, zero_shift + cycle], [y_location] * 2, color='r',
                zorder=3)
        # cycle line
        ax.axvline(i_cycle * cycle, color='k', linestyle="--", lw=1, alpha=0.05)

    # set x and y limit
    if direction == 1:
        ax.set_ylim([-downstream_length, upstream_length])
    else:
        ax.set_ylim([-upstream_length, downstream_length])
    ax.set_xlim([0, repeat_cycles * movement_curve.cycle_length])


def get_pts_components(movement_curve: MovementTOD,
                       stop_bar_distance: float,
                       upstream_prediction: bool,
                       y_location: float,
                       jam_density: float,
                       upstream_length: float,
                       downstream_length: float,
                       repeat_cycles: int,
                       direction: Direction):
    # time step
    jam_equivalent_lane_num = 1
    time_step = int(movement_curve.resolution)

    # cycle
    cycle = movement_curve.cycle_length

    # jam density
    jam_density = jam_density * movement_curve.sat_flow_per_lane / 3600 * time_step / jam_equivalent_lane_num
    jam_density = np.round(jam_density, 3)
    cycle_steps = int(cycle // time_step)

    # green split
    reaction_time = 2.5
    green_start, green = movement_curve.green_time[0]
    green_start += reaction_time
    green = green - reaction_time - movement_curve.clearance_interval - movement_curve.yellow_change_interval / 2
    r_s = int(round((green_start + green) / time_step))
    green_split = green / cycle

    # arrival function
    if upstream_prediction:
        arrival = movement_curve.arrival_curve.predict_list
    else:
        arrival = movement_curve.arrival_curve.prob_list
    offset_diff = int(round(movement_curve.additional_offset / time_step))
    a = lambda _t: arrival[(_t + r_s + cycle_steps + offset_diff) % cycle_steps]

    # departure function
    r = cycle_steps - int(round(cycle_steps * green_split))
    d = lambda _t: (_t % cycle_steps) >= r

    # green shift
    red_start_abs_time = movement_curve.offset + movement_curve.additional_offset + green + green_start + movement_curve.green_start_shift
    green_shift = red_start_abs_time % cycle - cycle

    # y axis origin
    y_origin = y_location - stop_bar_distance
    return pts(cycle=cycle,
               green_split=green_split,
               arrival_fn=a,
               departure_fn=d,
               green_shift=green_shift,
               time_duration=cycle * repeat_cycles,
               time_step=time_step,
               y_origin=y_origin,
               jam_density=jam_density,
               speed=movement_curve.measured_free_v,
               upstream_link_length=upstream_length,
               downstream_link_length=downstream_length,
               direction=direction,
               max_iteration=20,
               dryrun=True,
               debug=False)


def get_signal_info(movement_curve):
    cycle = movement_curve.cycle_length
    offset = movement_curve.offset
    green_time = movement_curve.green_time
    green_loss_adjustment = 2
    green_start, green = green_time[0][0] + green_loss_adjustment, green_time[0][1]
    red_start = green_start + green
    red_clearance, yellow = movement_curve.clearance_interval, movement_curve.yellow_change_interval
    green = green - yellow - red_clearance
    green_end = green_start + green
    return cycle, offset, green_start, green_end, yellow, red_clearance, red_start
