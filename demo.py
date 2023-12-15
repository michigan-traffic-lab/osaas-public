# -*- coding: utf-8 -*-
from pathlib import Path

from data_io.demo_data_loader import load_corridor, load_calibrated_movement_curves
from models.net_model import update_network_prediction
from plot.draw_ts import corridor_time_space_diagram


def main():
    tod_name = 'MD'
    output_path = Path('output/demo')
    output_path.mkdir(parents=True, exist_ok=True)

    # Load data
    corridor = load_corridor()
    movement_curve_dict = load_calibrated_movement_curves()

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
