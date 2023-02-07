import abc

import numpy as np
import pandas as pd
import talib as ta


class DataHandler(abc.ABC):
    def __init__(self):
        pass

    def fetch(self, df: pd.DataFrame = None) -> pd.DataFrame:
        pass


class Alpha100(DataHandler):
    def __init__(self, test_mode=False):
        self.test_mode = test_mode

    def fetch(self, df: pd.DataFrame = None) -> pd.DataFrame:
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']

        momentum_1d = ta.MOM(close, timeperiod=1)
        momentum_3d = ta.MOM(close, timeperiod=3)
        momentum_5d = ta.MOM(close, timeperiod=5)
        momentum_15d = ta.MOM(close, timeperiod=15)
        momentum_30d = ta.MOM(close, timeperiod=30)
        df['momentum_1d'] = momentum_1d
        df['momentum_3d'] = momentum_3d
        df['momentum_5d'] = momentum_5d
        df['momentum_15d'] = momentum_15d
        df['momentum_30d'] = momentum_30d

        highlow_1d = close.rolling(window=1).max() / close.rolling(window=1).min()
        highlow_3d = close.rolling(window=3).max() / close.rolling(window=3).min()
        highlow_5d = close.rolling(window=5).max() / close.rolling(window=5).min()
        highlow_15d = close.rolling(window=15).max() / close.rolling(window=15).min()
        highlow_30d = close.rolling(window=30).max() / close.rolling(window=30).min()
        df['highlow_1d'] = highlow_1d
        df['highlow_3d'] = highlow_3d
        df['highlow_5d'] = highlow_5d
        df['highlow_15d'] = highlow_15d
        df['highlow_30d'] = highlow_30d

        vstd_1d = volume.rolling(window=1).std()
        vstd_3d = volume.rolling(window=3).std()
        vstd_5d = volume.rolling(window=5).std()
        vstd_15d = volume.rolling(window=15).std()
        vstd_30d = volume.rolling(window=30).std()
        df['vstd_1d'] = vstd_1d
        df['vstd_3d'] = vstd_3d
        df['vstd_5d'] = vstd_5d
        df['vstd_15d'] = vstd_15d
        df['vstd_30d'] = vstd_30d

        sobv = ta.OBV(close, volume)
        df['sobv'] = sobv

        rsi = ta.RSI(close, timeperiod=14)
        df['rsi'] = rsi

        dif, dea, macd = ta.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        df['dif'] = dif
        df['dea'] = dea
        df['macd'] = macd

        kdj_k, kdj_d = ta.STOCH(high, low, close, fastk_period=9, slowk_period=3, slowk_matype=0, slowd_period=3,
                                slowd_matype=0)
        kdj_j = 3 * kdj_k - 2 * kdj_d
        df['kdj_k'] = kdj_k
        df['kdj_d'] = kdj_d
        df['kdj_j'] = kdj_j

        if not self.test_mode:
            # regression target
            label_reg = np.ones(close.shape[0]) * np.NaN
            for i in range(0, label_reg.shape[0] - 2):
                label_reg[i] = (close[i + 2] / close[i + 1] - 1)
            df['label_reg'] = label_reg
            df = df.dropna(subset=['label_reg'])

        return df
