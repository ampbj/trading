import numpy as np
import pandas as pd
import datetime
from hmmlearn import hmm
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import dates
import statsmodels.api as sm
import re
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
        # check if index is datetime index
        if self.data.index.dtype == '<M8[ns]':
            self.data.index = pd.DatetimeIndex(
                self.data.index).to_period(self.data_freq)
        self.data['pct_change'] = self.data['Price'].pct_change(n_pct_change)

    def directional_change_fit(self, dc_offset=[0.1, 0.2]):
        dc_offset.sort()
        dc_offset.reverse()
        self.data['BBTheta'] = pd.Series('bool')
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
                        self.data.loc[index + 1,
                                      curent_offset_column] = 'Start upward OS'
                        if self.data.isnull().loc[self.DC_lowest_price.name][curent_offset_column]:
                            self.data.loc[self.DC_lowest_price.name,
                                          curent_offset_column] = 'DXP'
                        else:
                            self.data.loc[self.DC_lowest_price.name,
                                          curent_offset_column] = 'Down+DXP'
                        self.DC_highest_price = values
                        dc_current_lowest_price = self.data.loc[
                            self.DC_lowest_price.name][f"Event_{dc_offset[0]}"]
                        if item_number == 1 and (dc_current_lowest_price == 'DXP' or dc_current_lowest_price == 'Down+DXP'):
                            self.data.loc[index, 'BBTheta'] = True
                    if values['Price'] <= self.DC_lowest_price['Price']:
                        self.DC_lowest_price = values

                if self.DC_event == 'uptrend' or self.DC_event == 'init':
                    if values['Price'] <= (self.DC_highest_price['Price'] * (1 - current_offset_value)):
                        self.DC_event = 'downtrend'
                        self.data.loc[index, curent_offset_column] = 'Down'
                        self.data.loc[index + 1,
                                      curent_offset_column] = 'Start downward OS'
                        if self.data.isnull().loc[self.DC_highest_price.name][curent_offset_column]:
                            self.data.loc[self.DC_highest_price.name,
                                          curent_offset_column] = 'UXP'
                        else:
                            self.data.loc[self.DC_lowest_price.name,
                                          curent_offset_column] = 'Up+UXP'
                        self.DC_lowest_price = values
                        dc_current_highest_price = self.data.loc[
                            self.DC_highest_price.name][f"Event_{dc_offset[0]}"]
                        if item_number == 1 and (dc_current_highest_price == 'UXP' or dc_current_highest_price == 'Up+UXP'):
                            self.data.loc[index, 'BBTheta'] = True
                    if values['Price'] >= self.DC_highest_price['Price']:
                        self.DC_highest_price = values
        return self

    def markov_switching_regression_fit(self, k_regimes=3, summary=False, expected_duration=False):
        self.Markov_switching_model = sm.tsa.MarkovRegression(self.data['pct_change'].dropna(), k_regimes=k_regimes,
                                                              trend='nc', switching_variance=True).fit()
        if expected_duration:
            print('expected durations:',
                  self.Markov_switching_model.expected_durations)
        if summary:
            print(self.Markov_switching_model.summary())
        return self

    def hidden_markov_model_fit(self, n_components=3, n_iter=100):
        hmm_data = self.data['pct_change'].dropna().values.reshape(-1, 1)
        self.hmm_model_fit = hmm.GaussianHMM(
            n_components=n_components, covariance_type="full", n_iter=n_iter).fit(hmm_data)
        self.hmm_model_predict = self.hmm_model_fit.predict(hmm_data)
        return self

    def plot_market_regime(self, figsize=(20, 12), day_interval=10, plot_hmm=False):
        data_to_draw = self.data
        data_to_draw.index = data_to_draw.index.to_timestamp()
        if plot_hmm:
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
        ax[0].plot(data_to_draw['Price'], label='Price', color='w')
        data_event_columns = self.data.filter(regex=("Event.*"))
        first_round = True
        fontsize = 7
        for column in data_event_columns:
            annotate_result = data_to_draw[self.data[column].notnull()]
            match = re.search(r'(Event_)([\w\.-]+)', column)
            superscript = match.group(2)
            if first_round:
                color = 'red'
                offset_value = 2
            else:
                color = '#42AFD8'
                offset_value = 10
            for index, row in annotate_result.iterrows():
                text = "%s^%s" % (row[column], superscript)
                if row[column] == 'Down':
                    ax[0].annotate(text, xy=(index, row['Price']), xytext=(index - datetime.timedelta(days=40), (row['Price'] + 20)), color=color,
                                   arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=80", color=color), fontsize=fontsize)
                    if not first_round and data_to_draw.loc[index]['BBTheta'] is True:
                        ax[0].annotate(data_to_draw.loc[index]['BBTheta'], xy=(index, row['Price']), xytext=(index + datetime.timedelta(days=30), (row['Price'] + 20)), color='#EA62EC',
                                       arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=70", color='#EA62EC'), fontsize=fontsize)
                elif row[column] == 'Up':
                    ax[0].annotate(text, xy=(index, row['Price']), xytext=(index, (row['Price'] - 20)), color=color,
                                   arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=-60", color=color), fontsize=fontsize)
                    if not first_round and data_to_draw.loc[index]['BBTheta'] is True:
                        ax[0].annotate(data_to_draw.loc[index]['BBTheta'], xy=(index, row['Price']), xytext=(index - datetime.timedelta(days=50), (row['Price'] - 25)), color='#EA62EC',
                                       arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=40", color='#EA62EC'), fontsize=fontsize)
                elif row[column] == 'DXP' or row[column] == 'Down+DXP':
                    ax[0].annotate(text, xy=(index, row['Price']), xytext=(index - datetime.timedelta(days=10), (row['Price'] - 20 + offset_value)), color=color,
                                   arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=90", color=color), fontsize=fontsize)
                elif row[column] == 'UXP' or row[column] == 'Up+UXP':
                    ax[0].annotate(text, xy=(index, row['Price']), xytext=(index - datetime.timedelta(days=10), (row['Price'] + 20 - offset_value)), color=color,
                                   arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=90", color=color), fontsize=fontsize)
                first_round = False
        ax[1].plot(data_to_draw['pct_change'], color='y',
                   linewidth=1.5, label='Price return')
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
