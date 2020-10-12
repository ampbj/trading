import pandas as pd
import sys
sys.path.append('../')
from market_regime.market_regime_detection import Market_regime as mrd

# fx_eur_chf_2013 = pd.read_csv(f"data/fx_gbp_chf/fx_gbp_chf_close_only/{index}.csv",
#                                 delimiter=';', names=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
# fx_eur_chf_2013.set_index('Timestamp', inplace=True)
# close_data = fx_eur_chf_2013.loc[:,['Close']]
# close_data.to_csv('data/fx_eur_chf_M1_2013.csv')
#MR = mrd(close_data, data_freq='m').directional_change_fit(dc_offset=[0.01, 0.02])#.markov_switching_regression_fit().hidden_markov_model_fit()
#MR.plot_market_regime(day_interval=1, no_markov=True, plot_hmm=False)


for index in range(0,3):
        file = pd.read_csv(f"data/fx_usd_jpy/fx_usd_jpy_close_only/{index}.csv",
                                delimiter=';', names=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        file.set_index('Timestamp', inplace=True)
        close_data = file.loc[:,['Close']]
        close_data.to_csv(f"data/fx_usd_jpy/fx_usd_jpy_close_only/{index}_close.csv")
        MR = mrd(close_data, data_freq='m').directional_change_fit(dc_offset=[0.01, 0.02])
        MR.plot_market_regime(day_interval=1, no_markov=True, plot_hmm=False, save_pic=f'data/fx_usd_jpy/fx_usd_jpy_close_only/{index}')
