import numpy as np
import pandas as pd
import datetime
from hmmlearn import hmm
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import dates
import statsmodels.api as sm
import re
import math
np.random.seed(42)


class Market_regime:
    def __init__(self, data, data_freq='D', n_pct_change=1):
        columns = data.columns
        if len(columns) > 1:
            raise Exception(
                "There are more than one column in the Pandas DataFrame!")
        pd.plotting.register_matplotlib_converters()
        self.data = data.rename(columns={columns[0]: 'Price'}, inplace=False)
        self.data_freq = data_freq
        # check if index is object
        if self.data.index.dtype.name == 'object':
            self.data.index = pd.to_datetime(self.data.index)
        self.data['pct_change'] = self.data['Price'].pct_change(n_pct_change)

    def directional_change_fit(self, dc_offset=[0.1, 0.2]):
        dc_offset.sort()
        dc_offset.reverse()
        self.data['BBTheta'] = pd.Series('bool')
        self.data['OSV'] = pd.Series('float')
        for item_number in range(len(dc_offset)):
            current_offset_value = dc_offset[item_number]
            curent_offset_column = f"Event_{current_offset_value}"
            self.data[curent_offset_column] = pd.Series('string')
            self.DC_event = 'init'
            self.DC_highest_price = self.data.iloc[0]
            self.DC_lowest_price = self.data.iloc[0]
            for index, values in self.data.iterrows():
                if self.DC_event == 'downtrend' or self.DC_event == 'init':
                    if values['Price'] >= (self.DC_lowest_price['Price'] * (1 + current_offset_value)):
                        self.DC_event = 'uptrend'
                        self.data.loc[index, curent_offset_column] = 'Up'
                        check_null_value = self.data.isnull(
                        ).loc[self.DC_lowest_price.name][curent_offset_column]
                        if check_null_value:
                            self.data.loc[self.DC_lowest_price.name,
                                          curent_offset_column] = 'DXP'
                        else:
                            self.data.loc[self.DC_lowest_price.name,
                                          curent_offset_column] = 'Down+DXP'

                        if item_number == 1:
                            # OSV discovery
                            osv_value = self.OSV(
                                self.DC_lowest_price.name, dc_offset[0], 'Down')
                            self.data.loc[index, 'OSV'] = osv_value
                            # BBTheta boolean value discovery
                            dc_current_lowest_price = self.data.loc[
                                self.DC_lowest_price.name][f"Event_{dc_offset[0]}"]
                            if dc_current_lowest_price == 'DXP' or dc_current_lowest_price == 'Down+DXP':
                                self.data.loc[index, 'BBTheta'] = True

                        self.DC_highest_price = values

                    if values['Price'] <= self.DC_lowest_price['Price']:
                        self.DC_lowest_price = values

                if self.DC_event == 'uptrend' or self.DC_event == 'init':
                    if values['Price'] <= (self.DC_highest_price['Price'] * (1 - current_offset_value)):
                        self.DC_event = 'downtrend'
                        self.data.loc[index, curent_offset_column] = 'Down'
                        check_null_value = self.data.isnull(
                        ).loc[self.DC_highest_price.name][curent_offset_column]
                        if check_null_value:
                            self.data.loc[self.DC_highest_price.name,
                                          curent_offset_column] = 'UXP'
                        else:
                            self.data.loc[self.DC_highest_price.name,
                                          curent_offset_column] = 'Up+UXP'

                        if item_number == 1:
                            # OSV discovery
                            osv_value = self.OSV(
                                self.DC_highest_price.name, dc_offset[0], 'Up')
                            self.data.loc[index, 'OSV'] = osv_value
                            # BBTheta boolean value discovery
                            dc_current_highest_price = self.data.loc[
                                self.DC_highest_price.name][f"Event_{dc_offset[0]}"]
                            if dc_current_highest_price == 'UXP' or dc_current_highest_price == 'Up+UXP':
                                self.data.loc[index, 'BBTheta'] = True

                        self.DC_lowest_price = values

                    if values['Price'] >= self.DC_highest_price['Price']:
                        self.DC_highest_price = values

        return self

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

    def markov_switching_regression_fit(self, k_regimes=3, summary=False, expected_duration=False):
        index_changed = False
        if not self.data.index.dtype.name.startswith('period'):
            self.data.index = pd.DatetimeIndex(
                self.data.index).to_period(self.data_freq)
            index_changed = True
        self.Markov_switching_model = sm.tsa.MarkovRegression(self.data['pct_change'].dropna(), k_regimes=k_regimes,
                                                              trend='nc', switching_variance=True).fit()
        if expected_duration:
            print('expected durations:',
                  self.Markov_switching_model.expected_durations)
        if summary:
            print(self.Markov_switching_model.summary())
        if index_changed:
            self.data.index = self.data.index.to_timestamp()
        return self

    def hidden_markov_model_fit(self, n_components=3, n_iter=100):
        hmm_data = self.data['pct_change'].dropna().values.reshape(-1, 1)
        self.hmm_model_fit = hmm.GaussianHMM(
            n_components=n_components, covariance_type="full", n_iter=n_iter).fit(hmm_data)
        self.hmm_model_predict = self.hmm_model_fit.predict(hmm_data)
        return self

    def plot_market_regime(self, figsize=(20, 12), day_interval=10, plot_hmm=False, no_markov=False):
        data_to_draw = self.data
        # drawing boilderplate
        if no_markov:
            nrows = 2
            _, ax = plt.subplots(nrows=nrows, sharex=True, figsize=figsize, gridspec_kw={
                                 'height_ratios': [5, 2]})
        elif plot_hmm:
            try:
                self.hmm_model_predict
            except AttributeError:
                print('Run hidden_markov_model_fit first!')
            nrows = 6
            _, ax = plt.subplots(nrows=nrows, sharex=True, figsize=figsize, gridspec_kw={
                                 'height_ratios': [5, 2, 1, 1, 1, 1]})
        else:
            nrows = 5
            _, ax = plt.subplots(nrows=nrows, sharex=True, figsize=figsize, gridspec_kw={
                                 'height_ratios': [5, 2, 1, 1, 1]})
        [ax[i].cla() for i in range(nrows)]
        [ax[i].set_facecolor('k') for i in range(nrows)]
        [ax[i].xaxis.set_major_locator(dates.DayLocator(
            interval=day_interval)) for i in range(nrows)]
        [ax[i].xaxis.set_major_formatter(
            dates.DateFormatter('%y-%m-%d')) for i in range(nrows)]
        [ax[i].grid(color='r', linestyle='-', linewidth=1, alpha=0.3)
         for i in range(nrows)]
        plt.xticks(rotation=90)

        # drawing price graph
        ax[0].plot(data_to_draw['Price'], label='Price', color='w')

        # annotate plot with DC info
        self.annotate_plot(data_to_draw, ax[0])

        ax[1].plot(data_to_draw['pct_change'], color='y',
                   linewidth=1.5, label='Price return')
        if not no_markov:
            markov_result = self.Markov_switching_model.smoothed_marginal_probabilities
            markov_result.index = markov_result.index.to_timestamp()
            [ax[i].plot(markov_result[i-2], color='y',
                        label=f'volatility {i-2}') for i in range(2, 5)]
        if plot_hmm:
            index_hmmlearn_offset = len(
                self.data.index) - len(self.hmm_model_predict)
            ax[5].plot(data_to_draw.index[index_hmmlearn_offset:],
                       self.hmm_model_predict, color='y', label='Hmm')
        [ax[i].legend(loc="lower right", prop={'size': 6}) for i in range(2)]
        [ax[i].legend(loc="upper left", prop={'size': 5})
         for i in range(2, nrows)]
        plt.show()

    def annotate_plot(self, data_to_draw, plot_to_annotate):
        data_event_columns = self.data.filter(regex=("Event.*"))
        # figuring out how much to space arrows in annotations out:
        first_round = True
        fontsize = 7

        if self.data_freq == 'D':
            freq = 'days'
            duration = min(math.floor(
                (data_to_draw.index[-1].date() - data_to_draw.index[0].date()).days / 90), 6)
        elif self.data_freq == 'H':
            freq = 'hours'
            duration = min(math.floor(
                (data_to_draw.index[-1].date() - data_to_draw.index[0].date()).days / 90), 6)
        elif self.data_freq == 'M':
            freq = 'minutes'
            duration = max(1, min(math.floor(
                (data_to_draw.index[-1].date() - data_to_draw.index[0].date()).days / 7), 6))

        for column in data_event_columns:
            annotate_result = data_to_draw[self.data[column].notnull()]
            match = re.search(r'(Event_)([\w\.-]+)', column)
            superscript = match.group(2)
            if first_round:
                color = '#EA62EC'
                offset_value = 1
            else:
                color = '#42AFD8'
                offset_value = 5
            if self.data_freq == 'M':
                offset_value /= 10
            for index, row in annotate_result.iterrows():
                text = "%s^%s" % (row[column], superscript)
                if row[column] == 'Down':
                    plot_to_annotate.annotate(text, xy=(index, row['Price']), xytext=(index - datetime.timedelta(**{freq: (duration * 2)}), (row['Price'] + (duration * 2))), color=color,
                                              arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=80", color=color), fontsize=fontsize - 1)
                    if not first_round:
                        downText = ''
                        if data_to_draw.loc[index]['BBTheta'] is True:
                            downText = str(data_to_draw.loc[index]['BBTheta'])
                        if not pd.isnull(data_to_draw.loc[index]['OSV']):
                            string = str(
                                data_to_draw.loc[index]['OSV'].round(decimals=2))
                            if downText:
                                string += '--' + downText
                            downText = string
                        if downText:
                            plot_to_annotate.annotate(downText, xy=(index, row['Price']), xytext=(index - datetime.timedelta(**{freq: (duration * 10)}), (row['Price'] - (duration))), color='#00B748',
                                                      arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=40", color='#00B748'), fontsize=fontsize)
                elif row[column] == 'Up':
                    plot_to_annotate.annotate(text, xy=(index, row['Price']), xytext=(index + datetime.timedelta(**{freq: (duration * 1)}), (row['Price'] - (duration * 2))), color=color,
                                              arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=-60", color=color), fontsize=fontsize - 1)
                    if not first_round:
                        upText = ''
                        if data_to_draw.loc[index]['BBTheta'] is True:
                            upText = str(data_to_draw.loc[index]['BBTheta'])
                        if not pd.isnull(data_to_draw.loc[index]['OSV']):
                            string = str(
                                data_to_draw.loc[index]['OSV'].round(decimals=2))
                            if upText:
                                string += '--' + upText
                            upText = string
                        if upText:
                            plot_to_annotate.annotate(upText, xy=(index, row['Price']), xytext=(index - datetime.timedelta(**{freq: (duration * 10)}), (row['Price'] + (duration))), color='#00B748',
                                                      arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=120", color='#00B748'), fontsize=fontsize)
                elif row[column] == 'DXP' or row[column] == 'Down+DXP':
                    plot_to_annotate.annotate(text, xy=(index, row['Price']), xytext=(index - datetime.timedelta(**{freq: (duration * 4)}), (row['Price'] - (duration * 2) - offset_value)), color=color,
                                              arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=90", color=color), fontsize=fontsize)
                elif row[column] == 'UXP' or row[column] == 'Up+UXP':
                    plot_to_annotate.annotate(text, xy=(index, row['Price']), xytext=(index - datetime.timedelta(**{freq: (duration * 4)}), (row['Price'] + (duration * 2) + offset_value)), color=color,
                                              arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=90", color=color), fontsize=fontsize)
            first_round = False
        return None
