import pandas as pd
import sys
sys.path.append('../')
from market_regime.market_regime_detection import Market_regime as mrd
from timeit import default_timer as timer

close_data = pd.read_csv('data/fx_usd_jpy/fx_usd_jpy_close_only/all.csv')
close_data.set_index('Timestamp', inplace=True)
start = timer()
MR = mrd(close_data, data_freq='m').directional_change_fit(dc_offset=[0.01, 0.02])
end = timer()
print(f"Elapsed time = {end - start}")
MR.plot_market_regime(day_interval=1, no_markov=True, plot_hmm=False)
