# -*- coding: utf-8 -*-
from typing import Callable

import numpy as np


def queue_mat_to_horizontal_gridlines_mat(queue_matrix: np.ndarray, cycle: int, green_split: float) -> np.ndarray:
    horizontal_gridlines = _queue_matrix_to_horizontal_matrix(queue_matrix)
    # Do the shift along shockwave and fill zero below the shockwave
    total_time, max_queue = queue_matrix.shape
    red = cycle - int(round(cycle * green_split))
    for t in range(total_time):
        t_in_c = t % cycle
        if t_in_c >= red:
            horizontal_gridlines[t, t_in_c - red + 1:] = horizontal_gridlines[t, 0:max_queue - (t_in_c - red + 1)]
            horizontal_gridlines[t, 0:t_in_c - red + 1] = 0
    return horizontal_gridlines


def res_queue_mat_to_horizontal_gridlines_mat(res_queue_matrix: np.ndarray, cycle: int) -> np.ndarray:
    total_time, max_queue = res_queue_matrix.shape
    horizontal_gridlines = _queue_matrix_to_horizontal_matrix(res_queue_matrix)
    # Do the shift along shockwave and fill zero below the shockwave
    for t in range(total_time):
        t_in_cycle = t % cycle
        # For the residual queue, the only difference is the shift is from the beginning
        horizontal_gridlines[t, t_in_cycle + 1:] = horizontal_gridlines[t, 0:max_queue - t_in_cycle - 1]
        horizontal_gridlines[t, 0: t_in_cycle + 1] = 0
    return horizontal_gridlines


def res_queue_mat_to_vertical_gridlines_mat(res_queue_matrix: np.ndarray,
                                            res_queue_dep: np.ndarray,
                                            a: Callable[[int], float],
                                            cycle: int,
                                            init_queue: np.ndarray = None) -> np.ndarray:
    total_time, max_queue = res_queue_matrix.shape
    vertical_gridlines = _queue_matrix_to_vertical_matrix(res_queue_matrix, init_queue, a)
    # Do the shift along shockwave and fill actual departure below the shockwave
    for t in range(total_time):
        t_in_cycle = t % cycle
        # For the residual queue, the only difference is the shift is from the beginning
        vertical_gridlines[t, t_in_cycle + 1:] = vertical_gridlines[t, 1:max_queue - t_in_cycle]
        vertical_gridlines[t, 0:t_in_cycle + 1] = res_queue_dep[t]
    return vertical_gridlines


def _queue_matrix_to_horizontal_matrix(queue_matrix: np.ndarray) -> np.ndarray:
    # This is not the complete conversion, it is lack of shifting along the shockwave
    # and setting zero below the shockwave
    # Update equation: horizontal_gridlines[t,n] = sum(queue[t, n:])
    horizontal_gridlines = np.rot90(np.cumsum(np.rot90(queue_matrix, k=2), axis=1), k=2)
    horizontal_gridlines[:, 0] = 0
    return horizontal_gridlines


def _queue_matrix_to_vertical_matrix(queue_matrix: np.ndarray,
                                     init_queue: np.ndarray,
                                     a: Callable[[int], float]) -> np.ndarray:
    # This is not the complete conversion, it is lack of shifting along the shockwave
    # and setting actual departure below the shockwave

    # Update equation: vertical_gridlines[t,n] = sum(queue[t-1,0:n]) * a(t)
    total_time, max_queue = queue_matrix.shape
    if init_queue is None:
        init_queue = np.zeros((1, max_queue))
        init_queue[0, 0] = 1
    # Update equation: vertical_gridlines[t,n] = sum(queue[t-1,0:n]) * a(t)
    vertical_gridlines = np.cumsum(np.vstack([init_queue, queue_matrix]), axis=1)[:total_time, :max_queue]
    vertical_gridlines = np.hstack([np.zeros((total_time, 1)), vertical_gridlines])[:total_time, :max_queue]
    vertical_gridlines = vertical_gridlines * np.array([[a(t) for t in range(total_time)]]).T
    return vertical_gridlines


def transit_mat_to_vertical_gridlines_mat(transit: np.ndarray,
                                          d_actual: np.ndarray,
                                          cycle: int,
                                          green_split: float) -> np.ndarray:
    vertical_gridlines = _transit_matrix_to_vertical_matrix(transit)
    # print(vertical_gridlines)
    # Do the shift along shockwave and fill actual departure below the shockwave
    total_time, max_queue = transit.shape
    red = cycle - int(round(cycle * green_split))
    for t in range(total_time):
        t_in_c = t % cycle
        # When green light
        if t_in_c >= red:
            # Point queue need a shift along shockwave to become spatial queue
            vertical_gridlines[t, t_in_c - red + 1:] = vertical_gridlines[t, 1:max_queue - (t_in_c - red + 1) + 1]
            # Below the shockwave, is the actual departure
            vertical_gridlines[t, 0: t_in_c - red + 1] = d_actual[t]
    return vertical_gridlines


def _transit_matrix_to_vertical_matrix(transit: np.ndarray) -> np.ndarray:
    # This is not the complete conversion, it is lack of shifting along the shockwave
    # and setting actual departure below the shockwave

    total_time, max_queue = transit.shape
    vertical_gridlines = np.hstack([np.zeros((total_time, 1)), transit])[:total_time, :max_queue]
    vertical_gridlines = np.cumsum(vertical_gridlines, axis=1)
    return vertical_gridlines


def update_gridlines(cycle: int,
                     green_split: float,
                     h_grid_mat: np.ndarray,
                     v_grid_mat: np.ndarray,
                     res_h_grid_mat: np.ndarray,
                     res_v_grid_mat: np.ndarray):
    green = int(round(cycle * green_split))
    total_time, max_queue = h_grid_mat.shape
    for t in range(total_time):
        t_in_cycle = t % cycle
        h_grid_mat[t, green + t_in_cycle:] = res_h_grid_mat[t, t_in_cycle: max_queue - green]
    # print('h_grid_mat', h_grid_mat)
    for t in range(total_time):
        t_in_cycle = t % cycle
        v_grid_mat[t, green + t_in_cycle:] = res_v_grid_mat[t, t_in_cycle: max_queue - green]
    # print('v_grid_mat', v_grid_mat)

