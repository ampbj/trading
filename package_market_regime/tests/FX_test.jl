using DataFrames
using CSV
using Dates
include("../market_regime/Julia/directional_change.jl")

df = CSV.read("../data/fx_usd_jpy/fx_usd_jpy_close_only/all.csv", DataFrame)
df[:Timestamp] = parse.(DateTime, df.Timestamp, dateformat"yyyymmdd\ HHMMSS")
directional_change_init(df, [0.01,0.02])

