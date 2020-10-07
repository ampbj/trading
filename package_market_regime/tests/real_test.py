import sys
import os
sys.path.append('../')
from pandas_datareader import DataReader
import pandas as pd
import datetime
from market_regime.market_regime_detection import Market_regime as mrd
from market_regime import config

long_term = False
secs = ['SPY']
#short-term check
if not long_term:
        data = DataReader(secs, "av-intraday", start=str(datetime.date.today() - datetime.timedelta(days=30)),end=str(datetime.date.today()), api_key=config.ALPHAVANTAGE_API_KEY)['close']; data = pd.DataFrame(data)
        MR = mrd(data, data_freq='M').directional_change_fit(dc_offset=[0.01, 0.02])#.markov_switching_regression_fit().hidden_markov_model_fit()
        MR.plot_market_regime(day_interval=1, no_markov=True)

else:
        data = DataReader(secs, 'yahoo', '2017-12-01',str(datetime.date.today()))['Adj Close']
        MR = mrd(data, data_freq='D').directional_change_fit(dc_offset=[0.1, 0.2])#.markov_switching_regression_fit().hidden_markov_model_fit()
        MR.plot_market_regime(day_interval=20, no_markov=True)
