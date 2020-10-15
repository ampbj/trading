def fit(self, row, current_offset_value, curent_offset_column, last_round):
    if self.DC_event == 'downtrend' or self.DC_event == 'init':
        if row['Price'] >= (self.DC_lowest_price['Price'] * (1 + current_offset_value)):
            self.DC_event = 'uptrend'
            self.data.loc[row.index, curent_offset_column] = 'Up'
            check_null_value = self.data.isnull(
            ).loc[self.DC_lowest_price.name][curent_offset_column]
            if check_null_value:
                self.data.loc[self.DC_lowest_price.name,
                              curent_offset_column] = 'DXP'
            else:
                self.data.loc[self.DC_lowest_price.name,
                              curent_offset_column] = 'Down+DXP'

            if last_round:
                # OSV discovery
                osv_value = OSV(self,
                    self.DC_lowest_price.name, dc_offset[0], 'Down')
                self.data.loc[row.index, 'OSV'] = osv_value
                # BBTheta boolean value discovery
                dc_current_lowest_price = self.data.loc[
                    self.DC_lowest_price.name][f"Event_{dc_offset[0]}"]
                if dc_current_lowest_price == 'DXP' or dc_current_lowest_price == 'Down+DXP':
                    self.data.loc[row.index, 'BBTheta'] = True
                else:
                    self.data.loc[row.index, 'BBTheta'] = False

            self.DC_highest_price = row

        if row['Price'] <= self.DC_lowest_price['Price']:
            self.DC_lowest_price = row

    if self.DC_event == 'uptrend' or self.DC_event == 'init':
        if row['Price'] <= (self.DC_highest_price['Price'] * (1 - current_offset_value)):
            self.DC_event = 'downtrend'
            self.data.loc[row.index, curent_offset_column] = 'Down'
            check_null_value = self.data.isnull(
            ).loc[self.DC_highest_price.name][curent_offset_column]
            if check_null_value:
                self.data.loc[self.DC_highest_price.name,
                              curent_offset_column] = 'UXP'
            else:
                self.data.loc[self.DC_highest_price.name,
                              curent_offset_column] = 'Up+UXP'

            if last_round:
                # OSV discovery
                osv_value = self.OSV(self,
                    self.DC_highest_price.name, dc_offset[0], 'Up')
                self.data.loc[row.index, 'OSV'] = osv_value
                # BBTheta boolean value discovery
                dc_current_highest_price = self.data.loc[
                    self.DC_highest_price.name][f"Event_{dc_offset[0]}"]
                if dc_current_highest_price == 'UXP' or dc_current_highest_price == 'Up+UXP':
                    self.data.loc[row.index, 'BBTheta'] = True
                else:
                    self.data.loc[row.index, 'BBTheta'] = False

            self.DC_lowest_price = row

            if row['Price'] >= self.DC_highest_price['Price']:
                self.DC_highest_price = row

# Calculating OSV value as an independent variable used for prediction according to the paper
def OSV(self, STheta_extreme_index, BTheta, direction):
    if direction == 'Down':
        alternate_direction_value = 'Down+DXP'
    if direction == 'Up':
        alternate_direction_value = 'Up+UXP'
    STheta_extreme_price = self.data.loc[STheta_extreme_index]['Price']
    BTheta_column = f"Event_{BTheta}"
    BTheta_rows = self.data[self.data.index <= STheta_extreme_index]
    BTheta_rows = BTheta_rows[BTheta_rows[BTheta_column].notnull(
    )][BTheta_column]
    if not BTheta_rows.empty:
        for index, row in BTheta_rows[::-1].iteritems():
            if row == direction or row == alternate_direction_value:
                PDCC_BTheta = self.data.loc[index]['Price']
                OSV = ((STheta_extreme_price - PDCC_BTheta) /
                       PDCC_BTheta) / BTheta
                return OSV
    else:
        return
