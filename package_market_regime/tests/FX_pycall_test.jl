using DataFrames
using CSV
using PyCall
import Conda
@pyimport importlib.machinery as machinery
@pyimport pandas as pd
loader = machinery.SourceFileLoader("MRD", "/Users/ryanjadidi/Dev/trading/package_market_regime/market_regime/market_regime_detection.py")
mrd = loader[:load_module]("MRD")
df = pd.read_csv("../data/fx_usd_jpy/fx_usd_jpy_close_only/all.csv")
df.set_index("Timestamp", inplace=true)
@time MR = mrd.Market_regime(df, data_freq="m").directional_change_fit(dc_offset=PyVector([0.01, 0.02]))
println(MR.data.info())