# -*- coding: utf-8 -*-
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection

from data_io.converter import extract_ts_lists_from_df

SIGNAL_TO_COLOR = {'green': 'lime', 'yellow': 'yellow', 'red': 'r', 'red clearance': '#7F0000'}
STOP_CAT_TO_COLOR = {'No stop': 'g', 'Stop once': 'orange', 'Stop more than once': 'purple'}


class Plotter:
    def __init__(self, output_dir, fig_size, fig_format, dpi):
        self.output_dir = output_dir
        self.size = fig_size
        self.format = fig_format
        self.dpi = dpi

        self.default_line_width = 1

        self.ts_line_width = 0.8

        self.color_arrival = 'r'
        self.color_departure = 'b'

        self.label_font_size = 14

    def _create_plot(self):
        fig, ax = plt.subplots(figsize=self.size)
        return fig, ax

    def _save_figure(self, fig, name_prefix):
        fig_path = self.output_dir / f'{name_prefix}.{self.format}'
        fig_path.parent.mkdir(parents=True, exist_ok=True)

        fig.tight_layout()
        fig.savefig(fig_path, dpi=self.dpi)
        print(f'Saved to `{fig_path}`')
        plt.close()

    @staticmethod
    def _set_limit(ax, x_limit, y_limit):
        if x_limit:
            ax.set_xlim(x_limit)
        if y_limit:
            ax.set_ylim(y_limit)

    @staticmethod
    def _set_xticks(ax, pos_list, label_list=None):
        ax.set_xticks(pos_list)
        ax.set_xticklabels(label_list)

    @staticmethod
    def _set_yticks(ax, pos_list, label_list=None):
        ax.set_yticks(pos_list)
        ax.set_yticklabels(label_list)

    def _set_annotation(self, ax, xlabel, ylabel, legend=False, grid=True):
        ax.set_xlabel(xlabel, fontsize=self.label_font_size)
        ax.set_ylabel(ylabel, fontsize=self.label_font_size)
        if grid:
            ax.grid(linestyle='--', which='major', alpha=0.3)
        if legend:
            legend_obj = ax.legend()
            for text in legend_obj.get_texts():
                text_str = text.get_text()
                text.set_text(text_str[0:1].upper() + text_str[1:])

    def _plot_no_agg_ts(self, ax, x_lists, y_lists):
        for x_list, y_list in zip(x_lists, y_lists):
            ax.plot(x_list, y_list, 'k.-', lw=self.ts_line_width)

    def _plot_ts(self, ax, x_lists, y_lists, color, alpha):
        if isinstance(color, str):
            for x_list, y_list in zip(x_lists, y_lists):
                ax.plot(x_list, y_list, color=color, lw=self.ts_line_width, alpha=alpha)
        elif isinstance(color, list):
            color_list = color
            for x_list, y_list, color in zip(x_lists, y_lists, color_list):
                ax.plot(x_list, y_list, color=color, lw=self.ts_line_width, alpha=alpha)

    @staticmethod
    def _plot_signal_bar(ax, pos, signal_list, color_list, lw=3):
        for i in range(len(signal_list)):
            ax.plot(signal_list[i], [pos, pos], color=color_list[i], lw=lw)

    @staticmethod
    def _plot_hist(ax, x_list, value_list, color):
        ax.bar(x_list, value_list, color=color, alpha=0.3, width=3, edgecolor='k')

    def plot_no_agg_movement_ts(self, signal_df, trajs_df, name_prefix):
        x_lists, y_lists = extract_ts_lists_from_df(trajs_df, 'time (sec)', 'distance (meter)')
        signal_list = signal_df[['start', 'end']].to_numpy().tolist()

        fig, ax = self._create_plot()
        self._plot_no_agg_ts(ax, x_lists, y_lists)
        self._plot_signal_bar(ax, pos=0, signal_list=signal_list,
                              color_list=signal_df['signal'].map(SIGNAL_TO_COLOR).tolist())
        self._set_limit(ax, x_limit=(0, 270), y_limit=(-300, 20))
        self._set_annotation(ax, 'Time (s)', 'Distance (m)')
        self._save_figure(fig, name_prefix)

    def plot_movement_ts_with_category(self, signal_df, trajs_df, name_prefix):
        x_lists, y_lists = extract_ts_lists_from_df(trajs_df, 'time (sec)', 'distance (meter)')
        trajs_color_list = trajs_df['stop category'].map(STOP_CAT_TO_COLOR).tolist()
        signal_list = signal_df[['start', 'end']].to_numpy().tolist()

        fig, ax = self._create_plot()
        self._plot_ts(ax, x_lists, y_lists, color=trajs_color_list, alpha=0.3)
        self._plot_signal_bar(ax, pos=0, signal_list=signal_list,
                              color_list=signal_df['signal'].map(SIGNAL_TO_COLOR).tolist())
        self._set_limit(ax, x_limit=(-45, 180), y_limit=(-300, 20))
        self._set_annotation(ax, 'Time in cycle(s)', 'Distance (m)')
        self._save_figure(fig, name_prefix)

    def plot_arrival_and_departure_distribution(self, signal_df, hist_df, name_prefix):
        x_list = hist_df['time (s)'].tolist()
        arrival_list = hist_df['# of arrival'].tolist()
        departure_list = hist_df['# of departure'].tolist()

        signal_list = signal_df[['start', 'end']].to_numpy().tolist()

        fig, ax = self._create_plot()
        self._plot_hist(ax, x_list, arrival_list, self.color_arrival)
        self._plot_hist(ax, x_list, departure_list, self.color_departure)
        for s, e in signal_list:
            ax.axvspan(s, e, color='g', alpha=0.1)
        self._set_limit(ax, x_limit=(0, 180), y_limit=None)
        self._set_annotation(ax, 'Time in cycle (s)', 'Number of trajectories')
        self._save_figure(fig, name_prefix)

    def plot_estimated_arrival_and_departure(self, signal_df, df, name_prefix):
        x_list = df['time (s)'].tolist()
        scaled_departure_list = df['scaled departure'].tolist()
        scaled_arrival_list = df['scaled arrival'].tolist()
        capacity_list = df['capacity'].tolist()
        predicted_arrival_list = df['predicted arrival'].tolist()
        predicted_departure_list = df['predicted departure'].tolist()

        signal_list = signal_df[['start', 'end']].to_numpy().tolist()

        fig, ax = self._create_plot()
        self._plot_hist(ax, x_list, scaled_arrival_list, self.color_arrival)
        self._plot_hist(ax, x_list, scaled_departure_list, self.color_departure)
        ax.plot(x_list, predicted_arrival_list,
                color=self.color_arrival, linestyle='--', marker='.', lw=self.default_line_width)
        ax.plot(x_list, predicted_departure_list,
                color=self.color_departure, linestyle='--', marker='.', lw=self.default_line_width)
        ax.plot(x_list, capacity_list,
                color='g', alpha=0.3, linestyle='--', lw=self.default_line_width)
        ax.fill_between(x_list, 0, capacity_list, color='g', alpha=0.1)
        self._plot_signal_bar(ax, pos=0, signal_list=signal_list,
                              color_list=signal_df['signal'].map(SIGNAL_TO_COLOR).tolist())
        ax.axhline(1.0, color='r', linestyle='dashed', lw=1)
        self._set_limit(ax, x_limit=(0, 180), y_limit=(0, 1.1))
        self._set_annotation(ax, 'Time in cycle (s)', 'Probability')
        self._save_figure(fig, name_prefix)

    def plot_delay_wrt_penetration_rate(self, constants_df, df, name_prefix):
        penetration_rate_list = df['penetration rate (%)'].tolist()
        delay_list = df['model-estimated avg. control delay'].tolist()
        constants = constants_df.iloc[0].to_dict()

        fig, ax = self._create_plot()
        ax.plot(penetration_rate_list, delay_list, color='b', linestyle='-.', lw=self.default_line_width)
        ax.axvline(constants['example penetration rate'], color='k', linestyle='--', lw=self.default_line_width)
        ax.axvline(constants['estimated penetration rate (%)'], color='r', linestyle='--')
        ax.axhline(constants['observed avg. control delay'],
                   color='m', alpha=0.7, linestyle='--', lw=self.default_line_width)
        self._set_annotation(ax, 'Penetration rate (%)', 'Avg. control delay (s)')
        self._save_figure(fig, name_prefix)

    def plot_movement_pts(self, signal_df, pts_df, name_prefix):
        alphas = pts_df['probability'].to_numpy().clip(0, 1).tolist()
        segments = list(zip(pts_df[['t1', 's1']].to_numpy().tolist(), pts_df[['t2', 's2']].to_numpy().tolist()))
        signal_list = signal_df[['start', 'end']].to_numpy().tolist()

        fig, ax = self._create_plot()
        ax.add_collection(LineCollection(segments, linewidths=self.default_line_width,
                                         color=[(0, 0, 0, _) for _ in alphas]))
        self._plot_signal_bar(ax, pos=0, signal_list=signal_list,
                              color_list=signal_df['signal'].map(SIGNAL_TO_COLOR).tolist())
        self._set_limit(ax, x_limit=(0, 90), y_limit=(-200, 20))
        self._set_annotation(ax, 'Time in cycle (s)', 'Distance (m)', grid=False)
        self._save_figure(fig, name_prefix)

    def plot_movement_ts(self, signal_df, trajs_df, name_prefix):
        x_lists, y_lists = extract_ts_lists_from_df(trajs_df, 'time (sec)', 'distance (meter)')
        signal_list = signal_df[['start', 'end']].to_numpy().tolist()

        fig, ax = self._create_plot()
        self._plot_ts(ax, x_lists, y_lists, color='k', alpha=0.03)
        self._plot_signal_bar(ax, pos=0, signal_list=signal_list,
                              color_list=signal_df['signal'].map(SIGNAL_TO_COLOR).tolist())
        self._set_limit(ax, x_limit=(0, 90), y_limit=(-200, 20))
        self._set_annotation(ax, 'Time in cycle (s)', 'Distance (m)', grid=False)
        self._save_figure(fig, name_prefix)
