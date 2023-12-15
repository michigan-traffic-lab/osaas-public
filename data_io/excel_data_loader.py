# -*- coding: utf-8 -*-
from pathlib import Path
from typing import List

import pandas as pd


class ExcelDataLoader:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def load_simple(self, sheet_name: str, index_col: int = None):
        df = pd.read_excel(self.file_path, sheet_name=sheet_name, index_col=index_col)
        return df

    def load_complex(self, sheet_name: str, title_list: List[str]):
        skip_rows_list = []
        for title in title_list:
            skip_rows_list.append(self._find_title_row(title, sheet_name=sheet_name))

        df_list = []
        for idx, skip_rows in enumerate(skip_rows_list):
            start_row = skip_rows + 1
            rows = skip_rows_list[idx + 1] - start_row - 2 if idx < len(skip_rows_list) - 1 else None
            df = pd.read_excel(self.file_path, sheet_name=sheet_name,
                               skiprows=start_row, nrows=rows).dropna(axis=1, how='all')
            df_list.append(df)
        return df_list

    def _find_title_row(self, title: str, sheet_name: str):
        df = pd.read_excel(self.file_path, sheet_name=sheet_name, header=None)
        _ = df.index[df[0].str.contains(title, na=False)].tolist()
        if _:
            return _[0]
        else:
            return None


if __name__ == '__main__':
    data_dir = Path('data/figures')
    fig3_dl = ExcelDataLoader(data_dir / 'Fig3.xlsx')
    fig3a_df_list = fig3_dl.load_complex('Fig.3a', ['Signal Bar', 'Trajectories'])
    print()
