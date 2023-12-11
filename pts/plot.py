# -*- coding: utf-8 -*-
from typing import List

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection

LINE_WIDTH = 1.5
SIGNAL_BAR_WIDTH = 5


def plot_pts(x_origin: int,
             duration: int,
             time_step: int,
             y_origin: float,
             jam_density: float,
             speed: float,
             upstream_link_length: float,
             downstream_link_length: float,
             h_grid_mat: np.ndarray,
             v_grid_mat: np.ndarray,
             green_split: float = None,
             direction: int = 1,
             lines: List[List[float]] = None,
             dryrun: bool = False,
             debug: bool = False,
             file_path: str = None):
    def n_to_y(_n: float):
        return y_origin + direction * jam_density * _n

    def t_to_x(_t: int, _n: float):
        return x_origin + time_step * _t - jam_density * _n / speed

    cycle, max_queue = h_grid_mat.shape

    h_segments = []
    v_segments = []
    h_alphas = []
    v_alphas = []
    # Deal with middle part
    real_max_queue = max_queue - 1
    for n in range(max_queue):
        if (n + 1) * jam_density > upstream_link_length:
            real_max_queue = n
            break
        for t in range(cycle):
            y_s, y_e = n_to_y(n), n_to_y(n + 1)
            x_s, x_e = t_to_x(t, n), t_to_x(t + 1, n)
            x_sye = t_to_x(t, n + 1)
            if h_grid_mat[t, n] >= 1 / 256:
                h_segments.append([[x_s, y_s], [x_e, y_s]])
                h_alphas.append(h_grid_mat[t, n])

            if v_grid_mat[t, n] >= 1 / 256:
                v_segments.append([[x_s, y_s], [x_sye, y_e]])
                v_alphas.append(v_grid_mat[t, n])

    # Deal with upstream to middle part
    n = min(max_queue - 1, real_max_queue)
    for t in range(cycle):
        if v_grid_mat[t, n] < 1 / 256:
            continue
        equivalent_queue = upstream_link_length / jam_density
        y_s, y_e = n_to_y(real_max_queue), n_to_y(equivalent_queue)
        x_s, x_e = t_to_x(t, real_max_queue), t_to_x(t, equivalent_queue)
        v_segments.append([[x_s, y_s], [x_e, y_e]])
        v_alphas.append(v_grid_mat[t, n])

    # Deal with middle to downstream part
    for t in range(cycle):
        if v_grid_mat[t, 0] < 1 / 256:
            continue
        equivalent_queue = -downstream_link_length / jam_density
        y_s, y_e = n_to_y(0), n_to_y(equivalent_queue)
        x_s, x_e = t_to_x(t, 0), t_to_x(t, equivalent_queue)
        v_segments.append([[x_s, y_s], [x_e, y_e]])
        v_alphas.append(v_grid_mat[t, 0])

    # Repeat num of cycle times
    segments = h_segments + v_segments
    alphas = h_alphas + v_alphas
    one_cycle_segments_num = len(segments)
    total_cycle_num = int(np.ceil(duration / cycle))
    alphas = alphas * total_cycle_num
    for i in range(1, total_cycle_num):
        for idx in range(one_cycle_segments_num):
            s, e = segments[idx]
            segments.append([[s[0] + i * cycle * time_step, s[1]], [e[0] + i * cycle * time_step, e[1]]])

    # Ensure the color correct
    segments.extend([[[0, 0], [0, 0]]] * 2)
    alphas.extend([0, 1])

    # Build lines of the expectation of the queue
    if lines is not None:
        exp_queue_lines = [[[t_to_x(s[0], s[1]), n_to_y(s[1])],
                            [t_to_x(e[0], e[1]), n_to_y(e[1])]]
                           for s, e in lines if
                           n_to_y(e[1]) < y_origin + upstream_link_length and n_to_y(
                               s[1]) < y_origin + upstream_link_length]

        one_cycle_lines_num = len(exp_queue_lines)
        for i in range(1, total_cycle_num):
            for idx in range(one_cycle_lines_num):
                s, e = exp_queue_lines[idx]
                exp_queue_lines.append([[s[0] + i * cycle * time_step, s[1]], [e[0] + i * cycle * time_step, e[1]]])

        points = [[], []]
        for s, e in exp_queue_lines:
            points[0].append(s[0])
            points[1].append(s[1])
            points[0].append(e[0])
            points[1].append(e[1])

    if green_split is not None:
        green = int(round(cycle * green_split))
        red = cycle - green
        red_bars = []
        green_bars = []
        for idx in range(total_cycle_num):
            red_bars.append([[t_to_x(idx * cycle, 0), n_to_y(-1)], [t_to_x(red + idx * cycle, 0), n_to_y(-1)]])
            green_bars.append([[t_to_x(idx * cycle + red, 0), n_to_y(-1)], [t_to_x((idx + 1) * cycle, 0), n_to_y(-1)]])

    if not dryrun:
        fig = plt.figure(figsize=(9, 4))
        ax = fig.add_subplot(1, 1, 1)
        ax.set_xlim([t_to_x(0, max_queue), x_origin + duration])
        if direction == 1:
            ax.set_ylim([-(downstream_link_length + jam_density * 2) + y_origin,
                         (upstream_link_length + jam_density * 2) + y_origin])
        else:
            ax.set_ylim([-(upstream_link_length + jam_density * 2) + y_origin,
                         (downstream_link_length + jam_density * 2) + y_origin])
        # Add ts to the diagram
        colors = [(0, 0, 0, alpha) for alpha in alphas]
        trajs = LineCollection(segments, linewidths=LINE_WIDTH, color=colors, capstyle='butt')
        ax.add_collection(trajs)

        # Add queue expectation lines to diagram
        if lines is not None:
            exp_queue = LineCollection(exp_queue_lines, linewidths=LINE_WIDTH // 2, color='purple')
            ax.add_collection(exp_queue)
            ax.scatter(points[0], points[1], color='purple')

        # Add signal bars to diagram
        if green_split is not None:
            signal_red = LineCollection(red_bars, linewidths=SIGNAL_BAR_WIDTH, color='r')
            signal_green = LineCollection(green_bars, linewidths=SIGNAL_BAR_WIDTH, color='lime')
            ax.add_collection(signal_red)
            ax.add_collection(signal_green)

        if debug:
            for segment, alpha in zip(h_segments, h_alphas):
                [x_s, y_s], _ = segment
                ax.text(x_s + 0.25 * time_step, y_s, f'{alpha:0.3f}', color='b')
            for segment, alpha in zip(v_segments, v_alphas):
                [x_s, y_s], _ = segment
                ax.text(x_s - 0.25 * time_step, y_s + 0.5 * jam_density, f'{alpha:0.3f}', color='b')
            if lines is not None:
                for s, e in exp_queue_lines:
                    ax.text(s[0] + 0.1 * time_step,
                            s[1] - 0.1 * jam_density, f'{s[1] - y_origin:0.3f}', color='r') if s[1] else 1
                    ax.text(e[0] + 0.1 * time_step,
                            e[1] - 0.1 * jam_density, f'{e[1] - y_origin:0.3f}', color='r') if e[1] else 1

        ax.grid(True)
        ax.set_xlabel('Time in cycle (s)')
        ax.set_xlim([-15, 270])
        ax.set_ylabel('Distance to intersection (m)')
        # ax.set_title('probabilistic time-space diagram')
        fig.tight_layout()
        if not file_path:
            file_path = 'pts.png'
        fig.savefig(file_path, dpi=200)
        plt.close()

    return segments, np.clip(alphas,0,1)
