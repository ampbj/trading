import sys
sys.path.append('../')
from market_regime import market_regime_detection as mrd
import datetime
from pandas_datareader import DataReader


secs = ['SPY']
data = DataReader(secs, 'yahoo', '2017-01-01',
                  str(datetime.date.today()))['Adj Close']
MR = mrd.Market_regime(data).directional_change_fit(dc_offset=[0.1,0.19]).markov_switching_regression_fit().hidden_markov_model_fit()
MR.plot_market_regime(day_interval=20, plot_hmm=True)

