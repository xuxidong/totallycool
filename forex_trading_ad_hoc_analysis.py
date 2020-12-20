import technical as technical
import data_request as dq
import oandapyV20 as oda20
from matplotlib import pyplot as plt
import pandas as pd


client = oda20.API(access_token='39b0f06eeedfdb4bfe2b7d60708ad253-648a30baf6d376c2296d8e8fb1d9c2e7')
clientID = '101-001-8411104-001'
instrument = 'AUD_USD'
load_percentage = 0.2
take_profit_points = 2.5
stop_loss_points = 1.5

def calculate_technicals(df):
    df[['Sar', 'Trend']] = technical.parabolic_sar(df)
    df['MACD'] = technical.MACD(df['close'])
    df['MACD_shift'] = df['MACD'].shift(1)
    df['MACD_signal'] = 0
    df.loc[(df['MACD'] > 0) & (df['MACD_shift'] < 0),'MACD_signal'] = 1
    df.loc[(df['MACD'] < 0) & (df['MACD_shift'] > 0), 'MACD_signal'] = -1
    df['sigma'] = technical.moving_std(df['close'])
    df['MACD_reversal'] = technical.calculate_MACD_reversal(df['MACD'])
    return df

data = dq.request_data(client,instrument,frequency='M30',count = 500)
data = calculate_technicals(data)

print(data.tail(50))

plt.plot(data['close'])
plt.scatter(data[data['MACD_reversal']==-1].index, data[data['MACD_reversal']==-1]['close'],color= 'G',linewidths=0.001)
plt.scatter(data[data['MACD_reversal']==1].index, data[data['MACD_reversal']==1]['close'],color= 'R',linewidths=0.001)
plt.show()

