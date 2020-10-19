import pandas as pd


class directional_change:

    def __init__(self, data, dc_offset):
        # initializing directional change fit
        dc_offset.sort()
        dc_offset.reverse()
        self.dc_offset = dc_offset
        self.data = data
        self.data['BBTheta'] = pd.Series('bool')
        self.data['OSV'] = pd.Series('float')
        dc_offset_length = len(self.dc_offset)
        last_round = dc_offset_length - 1
        for item_number in range(dc_offset_length):
            self.current_offset_value = self.dc_offset[item_number]
            self.curent_offset_column = f"Event_{self.current_offset_value}"
            self.data[self.curent_offset_column] = pd.Series('string')
            self.DC_event = 'init'
            self.DC_highest_price = self.data.iloc[0]['Price']
            self.DC_lowest_price = self.data.iloc[0]['Price']
            self.DC_highest_price_index = self.data.iloc[0].index
            self.DC_lowest_price_index = self.data.iloc[0].index
            self.is_last_round = item_number == last_round
            self.init()

    def init(self):
        _ = [self.fit(index, price) for index, price in zip(
            self.data.index, self.data['Price'])]

    def fit(self, index, price):
        if self.DC_event == 'downtrend' or self.DC_event == 'init':
            if price >= (self.DC_lowest_price * (1 + self.current_offset_value)):
                self.DC_event = 'uptrend'
                self.data.loc[index, self.curent_offset_column] = 'Up'
                check_null_value = self.data.isnull(
                ).loc[self.DC_lowest_price_index][self.curent_offset_column]
                if check_null_value:
                    self.data.loc[self.DC_lowest_price_index,
                                  self.curent_offset_column] = 'DXP'
                else:
                    self.data.loc[self.DC_lowest_price_index,
                                  self.curent_offset_column] = 'Down+DXP'

                if self.is_last_round:
                    # OSV discovery
                    osv_value = self.OSV(
                        price, self.DC_lowest_price_index, self.dc_offset[0], 'Down')
                    self.data.loc[index, 'OSV'] = osv_value
                    # BBTheta boolean value discovery
                    dc_current_lowest_price = self.data.loc[
                        self.DC_lowest_price_index][f"Event_{self.dc_offset[0]}"]
                    if dc_current_lowest_price == 'DXP' or dc_current_lowest_price == 'Down+DXP':
                        self.data.loc[index, 'BBTheta'] = True
                    else:
                        self.data.loc[index, 'BBTheta'] = False

                self.DC_highest_price = price
                self.DC_highest_price_index = index

            if price <= self.DC_lowest_price:
                self.DC_lowest_price = price
                self.DC_lowest_price_index = index
        if self.DC_event == 'uptrend' or self.DC_event == 'init':
            if price <= (self.DC_highest_price * (1 - self.current_offset_value)):
                self.DC_event = 'downtrend'
                self.data.loc[index, self.curent_offset_column] = 'Down'
                check_null_value = self.data.isnull(
                ).loc[self.DC_highest_price_index][self.curent_offset_column]
                if check_null_value:
                    self.data.loc[self.DC_highest_price_index,
                                  self.curent_offset_column] = 'UXP'
                else:
                    self.data.loc[self.DC_highest_price_index,
                                  self.curent_offset_column] = 'Up+UXP'

                if self.is_last_round:
                    # OSV discovery
                    osv_value = self.OSV(
                        price, self.DC_highest_price_index, self.dc_offset[0], 'Up')
                    self.data.loc[index, 'OSV'] = osv_value
                    # BBTheta boolean value discovery
                    dc_current_highest_price = self.data.loc[
                        self.DC_highest_price_index][f"Event_{self.dc_offset[0]}"]
                    if dc_current_highest_price == 'UXP' or dc_current_highest_price == 'Up+UXP':
                        self.data.loc[index, 'BBTheta'] = True
                    else:
                        self.data.loc[index, 'BBTheta'] = False

                self.DC_lowest_price = price
                self.DC_lowest_price_index = index

            if price >= self.DC_highest_price:
                self.DC_highest_price = price
                self.DC_highest_price_index = index

    # Calculating OSV value as an independent variable used for prediction according to the paper
    def OSV(self, price, STheta_extreme_index, BTheta, direction):
        def calculate_OSV_value(index, row):
            if row == direction or row == alternate_direction_value:
                PDCC_BTheta = self.data.loc[index]['Price']
                OSV_value = ((price - PDCC_BTheta) /
                            PDCC_BTheta) / BTheta
                return OSV_value

        if direction == 'Down':
            alternate_direction_value = 'Down+DXP'
        if direction == 'Up':
            alternate_direction_value = 'Up+UXP'
        BTheta_column = f"Event_{BTheta}"
        BTheta_rows = self.data[self.data.index <= STheta_extreme_index]
        BTheta_rows = BTheta_rows[BTheta_rows[BTheta_column].notnull(
        )][BTheta_column]
        BTheta_rows = BTheta_rows[::-1]
        if not BTheta_rows.empty:
            returned_list = [calculate_OSV_value(index, row) for index, row in zip(
                BTheta_rows.index, BTheta_rows.values)]
        OSV_value = next((item for item in returned_list if item is not None), None)
        if OSV_value is not None:
            return OSV_value