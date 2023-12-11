# -*- coding: utf-8 -*-
from typing import Callable, List

import numpy as np

from .calc_grid import res_queue_mat_to_horizontal_gridlines_mat, queue_mat_to_horizontal_gridlines_mat, \
    res_queue_mat_to_vertical_gridlines_mat, transit_mat_to_vertical_gridlines_mat, update_gridlines
from .calc_queue import joint_queue_matrix_factory, calc_queue_constraint
from .plot import plot_pts


def pts(cycle: int,
        green_split: float,
        arrival_fn: Callable[[int], float],
        departure_fn: Callable[[int], bool],
        green_shift: int,
        time_duration: int,
        time_step: int,
        y_origin: float,
        jam_density: float,
        speed: float,
        upstream_link_length: float,
        downstream_link_length: float,
        max_iteration: int = 5,
        direction: int = 1,
        dryrun: bool = False,
        debug: bool = False):
    cycle = int(cycle / time_step)
    max_queue = calc_queue_constraint(cycle, upstream_link_length, jam_density)
    queue_components = stationary_queue_factory(cycle, max_queue, arrival_fn, departure_fn, max_iteration)
    h_grid_mat, v_grid_mat = lines_factory(queue_components, arrival_fn, cycle, green_split)
    return plot_pts(x_origin=green_shift,
                    duration=time_duration,
                    time_step=time_step,
                    y_origin=y_origin,
                    jam_density=jam_density,
                    speed=speed,
                    upstream_link_length=upstream_link_length,
                    downstream_link_length=downstream_link_length,
                    h_grid_mat=h_grid_mat,
                    v_grid_mat=v_grid_mat,
                    lines=None,
                    green_split=green_split,
                    direction=direction,
                    dryrun=dryrun,
                    debug=debug)


def stationary_queue_factory(cycle, max_queue, a, d, max_iteration, threshold=1e-4):
    r_q_mat = np.zeros((cycle, max_queue))
    r_q_d = np.zeros((cycle, 1))
    transit_mat = np.zeros((cycle, max_queue))
    q_mat = np.zeros((cycle, max_queue))
    d_actual = np.zeros((cycle, 1))
    init_queue = np.zeros((1, max_queue, max_queue))
    init_queue[0, 0, 0] = 1

    converge = False
    for i in range(max_iteration):
        if i:
            init_queue = np.zeros((1, max_queue, max_queue))
            init_queue[0, 0, :] = q_mat[-1, :]
        r_q_mat, r_q_d, transit_mat, q_mat, d_actual = joint_queue_matrix_factory(cycle, max_queue, a, d, init_queue)

        init_diff = q_mat[-1, :] - init_queue[0, 0, :]
        diff = np.sum(init_diff ** 2) ** 0.5
        if diff < threshold:
            converge = True
            break
    # print('queue_matrix', q_mat)
    # print(f'Converged: {converge}, stop at round {i}')
    return [r_q_mat, r_q_d, transit_mat, q_mat, d_actual]


def lines_factory(queue_components: List[np.ndarray], a, cycle, green_split):
    r_q_mat, r_q_d, transit_mat, q_mat, d_actual = queue_components
    res_h_grid_mat = res_queue_mat_to_horizontal_gridlines_mat(r_q_mat, cycle)
    h_grid_mat = queue_mat_to_horizontal_gridlines_mat(q_mat, cycle, green_split)
    init_res_queue = q_mat[-1, :]
    res_v_grid_mat = res_queue_mat_to_vertical_gridlines_mat(r_q_mat,
                                                             r_q_d,
                                                             a,
                                                             cycle,
                                                             init_res_queue)
    v_grid_mat = transit_mat_to_vertical_gridlines_mat(transit_mat,
                                                       d_actual,
                                                       cycle,
                                                       green_split)
    update_gridlines(cycle, green_split, h_grid_mat, v_grid_mat, res_h_grid_mat, res_v_grid_mat)

    return h_grid_mat, v_grid_mat
