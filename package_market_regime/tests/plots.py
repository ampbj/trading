import sys
sys.path.append('../')
import pickle
import matplotlib.pyplot as plt
from pathlib import Path

file = Path('/Users/ryanjadidi/Dev/trading/package_market_regime/data/fx_euro_chf/fx_euro_chf_close_only/0.pickle')

fig = pickle.load(open(file,'rb'))
fig.show()