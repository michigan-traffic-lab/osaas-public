# -*- coding: utf-8 -*-
import pandas as pd


def semicolon_separated_string_column_to_lists(column: pd.Series):
    return column.str.split(';').apply(lambda x: [float(_) for _ in x])


def extract_ts_lists_from_df(df: pd.DataFrame, time_column_name: str, distance_column_name: str):
    time_lists = semicolon_separated_string_column_to_lists(df[time_column_name])
    distance_lists = semicolon_separated_string_column_to_lists(df[distance_column_name])
    return time_lists, distance_lists
