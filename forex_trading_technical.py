import numpy as np
import pandas as pd

def movingAverage(data, window):
    mvg = pd.ewma(data, span= window)
    return mvg


def RSIfun(data, n=14):
    delta = data.diff()
    # -----------
    dUp = delta.copy()
    dDown = delta.copy()
    dUp[dUp < 0] = 0
    dDown[dDown > 0] = 0

    RolUp = pd.rolling_mean(dUp, n)
    RolDown = pd.rolling_mean(dDown, n).abs()

    RS = RolUp / RolDown
    rsi = 100.0 - (100.0 / (1.0 + RS))
    return rsi


def moving_std(data, window=10):
    std = pd.rolling_std(data, window=window)
    return std


def bollinger_band(data, window=12):
    ma = movingAverage(data=data, window=window)
    std = moving_std(data=data, window=window)
    upper_band = ma + 2 * std
    lower_band = ma - 2 * std
    return upper_band, lower_band


def MACD(data, fast=12, slow=26, signal=9):
    fast_ma = movingAverage(data, window=fast)
    slow_ma = movingAverage(data, window=slow)
    difference = fast_ma - slow_ma
    signal = movingAverage(difference, window=signal)
    output = difference - signal
    return output


def parabolic_sar(data):
    PSAR = []
    n = len(data)
    previous_high = None
    pp_high = 0
    previous_low = None
    pp_low = 999999999
    for i in range(n):
        if i == 0:
            first_trend = 'D'
            Initial_Acc = 0.02
            first_ep = data.iloc[i, data.columns.get_loc('low')]
            first_PSAR = data.iloc[i, data.columns.get_loc('high')]
            first_diff = (first_PSAR - first_ep) * Initial_Acc
            PSAR.append([first_PSAR, first_trend])
            previous_high = data.iloc[i, data.columns.get_loc('high')]
            previous_low = data.iloc[i, data.columns.get_loc('low')]
            previous_trend = first_trend
            previous_PSAR = first_PSAR
            previous_diff = first_diff
            previous_ep = first_ep
            previous_acc = Initial_Acc
        else:
            if previous_trend == 'D':
                initial_PSAR = max(previous_PSAR - previous_diff, previous_high, pp_high)
            else:
                initial_PSAR = min(previous_PSAR - previous_diff, previous_low, pp_low);

            current_high = data.iloc[i, data.columns.get_loc('high')];
            current_low = data.iloc[i, data.columns.get_loc('low')]
            if (previous_trend == 'D' and initial_PSAR > current_high) or (
                    previous_trend == 'U' and initial_PSAR < current_low):
                current_PSAR = initial_PSAR
            elif (previous_trend == 'D' and initial_PSAR <= current_high) or (
                    previous_trend == 'U' and initial_PSAR >= current_low):
                current_PSAR = previous_ep

            if current_PSAR > data.iloc[i, data.columns.get_loc('close')]:
                current_trend = 'D'
                current_ep = min(current_low, previous_ep)
            else:
                current_trend = 'U'
                current_ep = max(current_high, previous_ep)

            PSAR.append([current_PSAR, current_trend])
            if current_trend == previous_trend and current_ep != previous_ep:
                current_acc = min(0.2, previous_acc + 0.02)
            elif current_trend == previous_trend and current_ep == previous_ep:
                current_acc = previous_acc
            else:
                current_acc = 0.02
            previous_diff = current_acc * (current_PSAR - current_ep)
            previous_acc = current_acc
            previous_trend = current_trend
            previous_PSAR = current_PSAR
            previous_high = current_high
            previous_low = current_low
            previous_ep = current_ep
            if i >= 1:
                pp_high = data.iloc[i - 1, data.columns.get_loc('high')]
                pp_low = data.iloc[i - 1, data.columns.get_loc('low')]
    PSAR = pd.DataFrame(PSAR, columns=['PSAR', 'Trend'], index=data.index)
    return PSAR

def calculate_MACD_reversal(MACD):
    MACD = pd.DataFrame(MACD)
    MACD['reversal'] = 0
    MACD['reversal_signal'] = 0
    for i in range(len(MACD)):
        if i == 0 :
            MACD.loc[i,'reversal'] =0
        else:
            if MACD.loc[i-1,'MACD'] < MACD.loc[i,'MACD']:
                MACD.loc[i, 'reversal'] = 1
            elif MACD.loc[i-1,'MACD'] > MACD.loc[i,'MACD']:
                MACD.loc[i, 'reversal'] = -1
    MACD['reversal_shift'] = MACD['reversal'].shift(1)
    MACD.loc[(MACD['reversal_shift'] == 1) & (MACD['reversal'] == -1),'reversal_signal'] = -1
    MACD.loc[(MACD['reversal_shift'] == -1) & (MACD['reversal'] == 1), 'reversal_signal'] = 1
    reverse_index = MACD[MACD['reversal_signal'] != 0].index
    for i in range(len(reverse_index)):
        if i > 0:
            if reverse_index[i] - reverse_index[i-1] < 4:
                MACD.loc[reverse_index[i],'reversal_signal'] = 0
                MACD.loc[reverse_index[i-1], 'reversal_signal'] = 0
    return MACD[['reversal_signal','reversal']]






