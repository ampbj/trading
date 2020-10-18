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
import pickle
import traceback
from market_regime.directional_change import directional_change
np.random.seed(42)


class Market_regime:
    def __init__(self, data, data_freq='d', n_pct_change=1):
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
        if not pd.infer_freq(self.data):
            if self.data_freq == 'd':
                frequency = 'B'
            elif self.data_freq == 'h':
                frequency = 'BH'
            elif self.data_freq == 'm':
                frequency = 'T'
            self.data = self.data.asfreq(frequency, method='ffill')
        self.data['pct_change'] = self.data['Price'].pct_change(n_pct_change).dropna()

    def directional_change_fit(self, dc_offset=[0.1, 0.2]):
        self.data = directional_change(self.data, dc_offset)
        return self

    def markov_switching_regression_fit(self, k_regimes=3, summary=False, expected_duration=False):
        try:
            self.Markov_switching_model = sm.tsa.MarkovRegression(self.data['pct_change'].dropna(), k_regimes=k_regimes,
                                                                  trend='nc', switching_variance=True).fit()
            if expected_duration:
                print('expected durations:',
                      self.Markov_switching_model.expected_durations)
            if summary:
                print(self.Markov_switching_model.summary())
            return self
        except Exception:
            traceback.print_exc()
            return self

    def hidden_markov_model_fit(self, n_components=3, n_iter=100):
        try:
            hmm_data = self.data['pct_change'].dropna().values.reshape(-1, 1)
            self.hmm_model_fit = hmm.GaussianHMM(
                n_components=n_components, covariance_type="full", n_iter=n_iter).fit(hmm_data)
            self.hmm_model_predict = self.hmm_model_fit.predict(hmm_data)
            return self
        except Exception:
            traceback.print_exc()
            return self

    def plot_market_regime(self, figsize=(20, 12), day_interval=10, plot_hmm=False, no_markov=False, save_pic=''):
        data_to_draw = self.data
        # drawing boilderplate
        if no_markov:
            nrows = 2
            fig, ax = plt.subplots(nrows=nrows, sharex=True, figsize=figsize, gridspec_kw={
                'height_ratios': [5, 2]})
        elif plot_hmm:
            try:
                self.hmm_model_predict
            except AttributeError:
                print('Run hidden_markov_model_fit first!')
            nrows = 6
            fig, ax = plt.subplots(nrows=nrows, sharex=True, figsize=figsize, gridspec_kw={
                'height_ratios': [5, 2, 1, 1, 1, 1]})
        else:
            nrows = 5
            fig, ax = plt.subplots(nrows=nrows, sharex=True, figsize=figsize, gridspec_kw={
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
            try:
                markov_result = self.Markov_switching_model.smoothed_marginal_probabilities
                [ax[i].plot(markov_result[i-2], color='y',
                            label=f'volatility {i-2}') for i in range(2, 5)]
            except Exception:
                traceback.print_exc()
                pass
        if plot_hmm:
            index_hmmlearn_offset = len(
                self.data.index) - len(self.hmm_model_predict)
            ax[5].plot(data_to_draw.index[index_hmmlearn_offset:],
                       self.hmm_model_predict, color='y', label='Hmm')
        [ax[i].legend(loc="lower right", prop={'size': 6}) for i in range(2)]
        [ax[i].legend(loc="upper left", prop={'size': 5})
         for i in range(2, nrows)]
        if save_pic:
            pickle.dump(fig,  open(f'{save_pic}.pickle', 'wb'))
        else:
            plt.show()

    def annotate_plot(self, data_to_draw, plot_to_annotate):
        data_event_columns = self.data.filter(regex=("Event.*"))
        # figuring out how much to space arrows in annotations out:
        first_round = True
        fontsize = 7

        if self.data_freq == 'd':
            freq = 'days'
            duration = min(math.floor(
                (data_to_draw.index[-1].date() - data_to_draw.index[0].date()).days / 90), 6)
        elif self.data_freq == 'h':
            freq = 'hours'
            duration = min(math.floor(
                (data_to_draw.index[-1].date() - data_to_draw.index[0].date()).days / 90), 6)
        elif self.data_freq == 'm':
            one_day = 60 * 24
            freq = 'minutes'
            length = len(data_to_draw)
            duration = min(math.ceil(one_day / length), 0.001)
            offset_value_reduction = max((1/duration), 10)

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
            if self.data_freq == 'm':
                offset_value /= offset_value_reduction
            for index, row in annotate_result.iterrows():
                text = "%s^%s" % (row[column], superscript)
                if row[column] == 'Down' or row[column] == 'Down+DXP' or row[column] == 'DXP':
                    if row[column] == 'Down':
                        plot_to_annotate.annotate(text, xy=(index, row['Price']), xytext=(index - datetime.timedelta(**{freq: (duration * 2)}), (row['Price'] + (duration * 2))), color=color,
                                                  arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=80", color=color), fontsize=fontsize - 1)
                    if row[column] == 'Down+DXP' or row[column] == 'DXP':
                        plot_to_annotate.annotate(text, xy=(index, row['Price']), xytext=(index - datetime.timedelta(**{freq: (duration * 4)}), (row['Price'] - (duration * 2) - offset_value)), color=color,
                                                  arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=90", color=color), fontsize=fontsize)
                    if not first_round:
                        downText = ''
                        if not math.isnan(data_to_draw.loc[index]['BBTheta']):
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
                elif row[column] == 'Up' or row[column] == 'Up+UXP' or row[column] == 'UXP':
                    if row[column] == 'Up':
                        plot_to_annotate.annotate(text, xy=(index, row['Price']), xytext=(index + datetime.timedelta(**{freq: (duration * 1)}), (row['Price'] - (duration * 2))), color=color,
                                                  arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=-60", color=color), fontsize=fontsize - 1)
                    elif row[column] == 'Up+UXP' or row[column] == 'UXP':
                        plot_to_annotate.annotate(text, xy=(index, row['Price']), xytext=(index - datetime.timedelta(**{freq: (duration * 4)}), (row['Price'] + (duration * 2) + offset_value)), color=color,
                                                  arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=0,angleB=90", color=color), fontsize=fontsize)
                    if not first_round:
                        upText = ''
                        if not math.isnan(data_to_draw.loc[index]['BBTheta']):
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
            first_round = False
        return None
