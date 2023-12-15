# -*- coding: utf-8 -*-
import json
import pickle

from models.net_dict_classes import MovementNetDict


def load_corridor():
    network_filepath = 'data/demo/traffic_network.pickle'
    with open(network_filepath, 'rb') as data_file:
        network = pickle.load(data_file)
    return network.arterials['Adams Rd']


def load_calibrated_movement_curves():
    calibrated_curve_filepath = f'data/demo/MD_calibrated_curves.json'
    with open(calibrated_curve_filepath, 'r') as temp_file:
        calibrated_dict = json.load(temp_file)
    return MovementNetDict().from_dict(calibrated_dict)
