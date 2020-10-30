using DataFrames
using CSV

df = CSV.read("../data/fx_usd_jpy/fx_usd_jpy_close_only/all.csv", DataFrame)
println(describe(df, :eltype, :nmissing))
