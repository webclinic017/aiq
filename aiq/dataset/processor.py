import os
import abc
import pickle
from typing import Union, Text

import pandas as pd
import numpy as np


class Processor(abc.ABC):
    def fit(self, df: pd.DataFrame = None):
        """
        Learn data processing parameters

        Args:
            df (pd.DataFrame): When we fit and process data with processor one by one. The fit function reiles on the output of previous
            processor, i.e. `df`.

        """

    def transform(self, df: pd.DataFrame):
        """
        Process the data
        NOTE: **The processor could change the content of `df` inplace !!!!! **
        User should keep a copy of data outside

        Args:
            df (pd.DataFrame): The raw_df of handler or result from previous processor.
        """


class CSZScoreNorm(Processor):
    """Cross Sectional ZScore Normalization

     Use robust statistics for Z-Score normalization:
        mean(x) = median(x)
        std(x) = MAD(x) * 1.4826
    """
    def __init__(self, cols=None, clip_outlier=True):
        self.cols = cols
        self.clip_outlier = clip_outlier

    def fit(self, df):
        X = df[self.cols].values
        self.mean_train = np.nanmedian(X, axis=0)
        self.std_train = np.nanmedian(np.abs(X - self.mean_train), axis=0)
        self.std_train += 1e-12
        self.std_train *= 1.4826

    def transform(self, df):
        X = df[self.cols]
        X -= self.mean_train
        X /= self.std_train
        if self.clip_outlier:
            X = np.clip(X, -3, 3)
        df[self.cols] = X
        return df

    def save(self, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        processor_params = {
            'cols': self.cols,
            'mean_train': self.mean_train,
            'std_train': self.std_train
        }
        with open(os.path.join(output_dir, 'processor.pkl'), 'wb') as f:
            pickle.dump(processor_params, f)

    def load(self, output_dir):
        with open(os.path.join(output_dir, 'processor.pkl'), 'rb') as f:
            processor_params = pickle.load(f)
            self.cols = processor_params['cols']
            self.mean_train = processor_params['mean_train']
            self.std_train = processor_params['std_train']
