import oandapyV20 as oda20
import oandapyV20.endpoints.instruments as ins
import pandas as pd
import forex_trading_data_request as oanda_request
from datetime import datetime
import time


token = '28ad8531340cc620497c245acdc354c8-8093db0a8f9b94116571467f3324bf33'
client = oda20.API(access_token=token)

while(True):
    now = datetime.now()
    time_str = '-'.join([str(now.year),str(now.month).rjust(2,'0'),str(now.day).rjust(2,'0')])+'T' + ':'.join([str(now.hour).rjust(2,'0'),str(now.minute).rjust(2,'0'),str(now.second).rjust(2,'0')])
    print('time: {a}'.format(a = time_str))
    if now.minute % 5 == 0:
        print('time: {a}, writing data'.format(a = time_str))
        price = oanda_request.request_data(client=client,instrument='EUR_USD',frequency='M5',count = 1)
        current_price = float(price['close'])
        
        position_bk = oanda_request.request_position_book(client=client,instrument='EUR_USD')
        
        position_bk[['price','longCountPercent','shortCountPercent']] = position_bk[['price','longCountPercent','shortCountPercent']].astype(float)
        
        order_bk = oanda_request.request_order_book(client=client,instrument='EUR_USD')
        
        order_bk[['price','longCountPercent','shortCountPercent']] = order_bk[['price','longCountPercent','shortCountPercent']].astype(float)
        
        order_bk=order_bk[(order_bk['price'] >current_price*0.995)&(order_bk['price'] <current_price*1.005)]
        
        order_bk['desc'] = 'order'
        
        position_bk = position_bk[(position_bk['price'] >current_price*0.995)&(position_bk['price'] <current_price*1.005)]
        
        position_bk['desc'] = 'position'
        
        df = pd.concat([order_bk,position_bk])
        
        df['time'] = now
        
        df.to_csv('../data/or_pos_{a}.csv'.format(a=time_str),index=None)
        
    time.sleep(60)
        