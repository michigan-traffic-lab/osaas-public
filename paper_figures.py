# -*- coding: utf-8 -*-
from pathlib import Path

from data_io.excel_data_loader import ExcelDataLoader
from plot.plotter import Plotter

figure_data_dir = Path('data/figures')
figure_output_dir = Path('output/figures')


def fig3():
    fig_dl = ExcelDataLoader(figure_data_dir / 'Fig3.xlsx')
    plotter = Plotter(figure_output_dir / 'Fig3', fig_size=(5, 4), fig_format='png', dpi=300)

    # Fig.3a
    fig3a_df_list = fig_dl.load_complex('Fig.3a', ['Signal Bar', 'Trajectories'])
    signal_df, trajs_df = fig3a_df_list
    plotter.plot_no_agg_movement_ts(signal_df, trajs_df, 'Fig3a')

    # Fig.3b
    fig3b_df_list = fig_dl.load_complex('Fig.3b', ['Signal Bar', 'Trajectories'])
    signal_df, trajs_df = fig3b_df_list
    plotter.plot_movement_ts_with_category(signal_df, trajs_df, 'Fig3b')

    # Fig.3c
    fig3c_df_list = fig_dl.load_complex('Fig.3c', ['Signal Bar', 'Number of arrivals and departures'])
    signal_df, hist_df = fig3c_df_list
    plotter.plot_arrival_and_departure_distribution(signal_df, hist_df, 'Fig3c')

    # Fig.3d
    fig3d_df_list = fig_dl.load_complex('Fig.3d', ['Signal Bar',
                                                   'Arrival, departure, and capacity'])
    signal_df, df = fig3d_df_list
    plotter.plot_estimated_arrival_and_departure(signal_df, df, 'Fig3d')

    # Fig.3e
    fig3e_df_list = fig_dl.load_complex('Fig.3e',
                                        ['Constants',
                                         'Model-estimated avg. control delay based on different penetration rates'])
    constants_df, df = fig3e_df_list
    plotter.plot_delay_wrt_penetration_rate(constants_df, df, 'Fig3e')

    plotter.size = (4.5, 5)
    # Fig.3f
    fig3f_df_list = fig_dl.load_complex('Fig.3f', ['Signal Bar', 'PTS Segments'])
    signal_df, pts_df = fig3f_df_list
    plotter.plot_movement_pts(signal_df, pts_df, 'Fig3f')

    # Fig.3g
    fig3g_df_list = fig_dl.load_complex('Fig.3g', ['Signal Bar', 'Trajectories'])
    signal_df, trajs_df = fig3g_df_list
    plotter.plot_movement_ts(signal_df, trajs_df, 'Fig3g')


if __name__ == '__main__':
    fig3()
