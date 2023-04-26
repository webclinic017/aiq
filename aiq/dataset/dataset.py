import abc
import os
from typing import List

import numpy as np
import pandas as pd

from .loader import DataLoader
from .handler import Alpha101
from .processor import CSFillna, CSNeutralize, CSFilter, CSZScore


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
        handler=None,
        adjust_price=True,
        training=False
    ):
        # feature and label names
        self.feature_names_ = None
        self.label_name_ = None

        # symbol of instruments
        with open(os.path.join(data_dir, 'instruments/%s.txt' % instruments), 'r') as f:
            self.symbols = [line.strip().split()[0] for line in f.readlines()]

        # process per symbol
        dfs = []
        symbols = []
        for symbol in self.symbols:
            df = DataLoader.load(os.path.join(data_dir, 'features'), symbol=symbol, start_time=start_time,
                                 end_time=end_time)

            # skip ticker of non-existed or small periods
            if df is None:
                continue

            # append ticker symbol
            df['Symbol'] = symbol
            symbols.append(symbol)

            # adjust price with factor
            if adjust_price:
                df = self.adjust_price(df)

            # extract ticker factors
            if handler is not None:
                df = handler.fetch(df)

            dfs.append(df)

        # concat dataframes and set index
        self.df = pd.concat(dfs, ignore_index=True)
        self.df = self.df.set_index(['Date', 'Symbol'])

        # assign features and label name
        if handler is not None:
            self.feature_names_ = handler.feature_names
            self.label_name_ = handler.label_name

        # add factor 101
        handler101 = Alpha101()
        self.df = handler101.fetch(self.df)
        self.feature_names_ += handler101.feature_names

        # pre-processors
        if self.feature_names_ is not None and False:
            # fill nan
            fillna = CSFillna(target_cols=self.feature_names_)
            self.df = fillna(self.df)

            # remove outlier
            outlier_filter = CSFilter(target_cols=self.feature_names_)
            self.df = outlier_filter(self.df)

            # factor neutralize
            cs_neut = CSNeutralize(industry_num=110, industry_col='Industry_id', market_cap_col='Total_mv',
                                   target_cols=self.feature_names_)
            self.df = cs_neut(self.df)

            # factor standardization
            cs_score = CSZScore(target_cols=self.feature_names_)
            self.df = cs_score(self.df)

        # reset index
        self.df.reset_index(inplace=True)

        # random shuffle
        if training:
            self.df = self.df.sample(frac=1.0)

        # close warnings
        pd.options.mode.copy_on_write = True

    @staticmethod
    def adjust_price(df):
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            df[col] = df[col] * df['Adj_factor']
        return df

    def to_dataframe(self):
        return self.df

    def add_column(self, name: str, data: np.array):
        self.df[name] = data

    def slice(self, start_time, end_time):
        return self.df[(self.df['Date'] >= start_time) & (self.df['Date'] <= end_time)]

    @property
    def feature_names(self):
        return self.feature_names_

    @property
    def label_name(self):
        return self.label_name_

    def __getitem__(self, index):
        return self.df.iloc[[index]]

    def __len__(self):
        return self.df.shape[0]


class Subset(Dataset):
    def __init__(self, dataset, start_time, end_time):
        self.feature_names_ = dataset.feature_names_
        self.label_name_ = dataset.label_name_
        self.df = dataset.slice(start_time, end_time)


def ts_split(dataset: Dataset, segments: List[List[str]]):
    return [Subset(dataset, segment[0], segment[1]) for segment in segments]
