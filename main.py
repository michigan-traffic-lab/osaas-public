# -*- coding: utf-8 -*-
import json
import pickle
from pathlib import Path

from models.net_dict_classes import MovementNetDict
from models.net_model import update_network_prediction
from plot.draw_ts import corridor_time_space_diagram


def load_corridor(corridor_name: str = 'Adams Rd'):
    network_filepath = 'data/traffic_network.pickle'
    with open(network_filepath, 'rb') as data_file:
        network = pickle.load(data_file)
    return network.arterials[corridor_name]


def load_calibrated_movement_curves(tod_name: str):
    calibrated_curve_filepath = f'data/{tod_name}_calibrated_curves.json'
    with open(calibrated_curve_filepath, 'r') as temp_file:
        calibrated_dict = json.load(temp_file)
    return MovementNetDict().from_dict(calibrated_dict)


def main():
    task_id = 'adams'
    tod_name = 'MD'
    output_path = Path(f'output/{task_id}')
    output_path.mkdir(parents=True, exist_ok=True)

    # Load data
    corridor = load_corridor()
    movement_curve_dict = load_calibrated_movement_curves(tod_name)

    # Draw probabilistic time-space diagram before optimization
    corridor_time_space_diagram(movement_curve_dict, tod_name, corridor,
                                output_path=output_path, prefix='before')

    # Apply optimal offsets
    offset_dict = {'61950324': 22, '62300620': -22, '62183487': 0,
                   '62344947': -20, '62344935': -20, '62355467': 0}
    update_network_prediction(movement_curve_dict, tod_name=tod_name,
                              offset_dict=offset_dict)

    # Draw probabilistic time-space diagram after optimization
    corridor_time_space_diagram(movement_curve_dict, tod_name, corridor,
                                output_path=output_path, prefix='after')


if __name__ == '__main__':
    main()
