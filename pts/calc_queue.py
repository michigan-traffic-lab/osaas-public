# -*- coding: utf-8 -*-
from typing import Callable, List

import numpy as np


def joint_queue_matrix_factory(cycle: int,
                               max_queue: int,
                               a: Callable[[int], float],
                               d: Callable[[int], bool],
                               init_queue: np.ndarray = None) -> List[np.ndarray]:
    if init_queue is None:
        init_queue = np.zeros((1, max_queue, max_queue))
        init_queue[0, 0, 0] = 1
    else:
        pass
        # print(init_queue)
    joint_queue = np.zeros((cycle, max_queue, max_queue))
    d_internal = np.zeros((cycle, 1))
    d_actual = np.zeros((cycle, 1))
    transit = np.zeros((cycle, max_queue))

    for t in range(cycle):
        # residual queue arrival
        for q in range(max_queue):
            for r_q in range(max_queue):
                if t == 0:
                    joint_queue[t, q, r_q] = init_queue[0, q, r_q - 1] * a(t) + init_queue[0, q, r_q] * (1 - a(t))
                else:
                    joint_queue[t, q, r_q] = joint_queue[t - 1, q, r_q - 1] * a(t) + joint_queue[t - 1, q, r_q] * (
                        1 - a(t))
        d_internal[t] = 1 - np.sum(joint_queue[t, :, :], axis=0)[0]
        # residual queue departure and queue arrival (diagonal transit)
        tmp = np.copy(joint_queue[t, :, :])
        transit[t, :] = np.sum(tmp[:, 1:], axis=1)
        joint_queue[t, 1:, 0] = joint_queue[t, 1:, 0] + joint_queue[t, :-1, 1]
        joint_queue[t, :, 1:] = 0
        joint_queue[t, 1:, 1:-1] = tmp[0:-1, 2:]

        # queue departure
        if d(t):
            d_actual[t] = 1 - np.sum(joint_queue[t, :, :], axis=1)[0]
            margin_res_queue = np.sum(joint_queue[t, :, :], axis=0)
            joint_queue[t, 0, :] = joint_queue[t, 0, :] + joint_queue[t, 1, :]
            joint_queue[t, 1:-1, :] = joint_queue[t, 2:, :]
            joint_queue[t, -1, :] = margin_res_queue - np.sum(joint_queue[t, :-1, :], axis=0)

    res_queue = np.sum(joint_queue, axis=1)
    queue = np.sum(joint_queue, axis=2)
    # print(joint_queue)
    return [res_queue, d_internal, transit, queue, d_actual]


def calc_queue_constraint(cycle, upstream_link_length, jam_density, coef: float = 1.1):
    return max(min(int(upstream_link_length / jam_density * coef) + 1, cycle * 2), cycle + 1)



