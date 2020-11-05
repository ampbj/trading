using DataFrames

function directional_change_init(data, dc_offset)
    if ncol(data) > 2
        error("data contains more than 2 columns")
    end
    rename!(data,[:Timestamp, :Price])
    init(data,dc_offset)
end

function init(data, dc_offset)
    # initializing directional change fit
    sort!(dc_offset, rev=true)
    insertcols!(data,:BBTheta => false)
    insertcols!(data, :OSV => 0.0)
    dc_offset_length = length(dc_offset)
    last_round = dc_offset_length
    for item_number in 1:dc_offset_length
        current_offset_value = dc_offset[item_number]
        curent_offset_column = "Event_$(current_offset_value)"
        insertcols!(data,curent_offset_column => "")
        DC_event = "init"
        DC_highest_price = data[1,:Price]
        DC_lowest_price = data[1,:Price]
        DC_highest_price_index = data[1, :Timestamp]
        DC_lowest_price_index = data[1, :Timestamp]
        isLastRound = item_number == last_round
        println("isLastRound = $(isLastRound)")
        println(first(data,50))
        fit()
    end
end

function fit()

end