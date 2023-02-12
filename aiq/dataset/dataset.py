import abc
import os

import numpy as np
import pandas as pd

from .loader import DataLoader
from .processor import CSZScoreNorm


class Dataset(abc.ABC):
    """
    Preparing data for model training and inference.
    """

    def __init__(
        self,
        data_dir,
        instruments,
        start_time=None,
        end_time=None,
        min_periods=30,
        handler=None,
        shuffle=False
    ):
        with open(os.path.join(data_dir, 'instruments/%s.txt' % instruments), 'r') as f:
            self.symbols = [line.strip().split()[0] for line in f.readlines()]

        df_list = []
        for symbol in self.symbols:
            df = DataLoader.load(os.path.join(data_dir, 'features'), symbol=symbol, start_time=start_time,
                                 end_time=end_time)

            # skip ticker of non-existed or small periods
            if df is None or df.shape[0] < min_periods:
                continue

            # append ticker symbol
            df['Symbol'] = symbol

            # extract ticker factors
            if handler is not None:
                df = handler.fetch(df)

            df_list.append(df)
        # concat and reset index
        self.df = pd.concat(df_list)
        self.df.reset_index(inplace=True)
        print('Loaded %d symbols to build dataset' % len(df_list))

        # processors
        self.processors = []
        if handler is not None and handler.label_name is not None:
            processor = CSZScoreNorm(fields_group=handler.label_name)
            self.processors.append(processor)

        for processor in self.processors:
            self.df = processor(self.df)

        # random shuffle
        if shuffle:
            self.df = self.df.sample(frac=1)

    def to_dataframe(self):
        return self.df

    def add_column(self, name: str, data: np.array):
        self.df[name] = data

    def dump(self, output_dir: str = None):
        if output_dir is None:
            return

        if not os.path.exists(path=output_dir):
            os.makedirs(output_dir)

        for symbol in self.symbols:
            df_symbol = self.df[self.df['Symbol'] == symbol]
            if df_symbol.shape[0] > 0:
                df_symbol.to_csv(os.path.join(output_dir, symbol + '.csv'), na_rep='NaN', index=False)

    def __getitem__(self, index):
        return self.df.iloc[[index]]

    def __len__(self):
        return self.df.shape[0]
