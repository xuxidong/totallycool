import technical as technical
from datetime import datetime
import time as time
import data_request as dq
import oandapyV20 as oda20
import pandas as pd

print('starting program')
client = oda20.API(access_token='39b0f06eeedfdb4bfe2b7d60708ad253-648a30baf6d376c2296d8e8fb1d9c2e7')
clientID = '101-001-8411104-001'
instrument = 'AUD_USD'
load_percentage = 0.2
take_profit_points = 2.5
stop_loss_points = 1.5
signal_used = 0

params = {
        'M30': {
            'count': 50,
            'granularity': 'M30'
        },
        'M5': {
            'count': 50,
            'granularity': 'M15'
        },

    }

#define trading period
def is_trading_time():
    day = datetime.now().weekday()
    time = datetime.now().time()
    return day < 4 or (day == 4 and time.hour < 16) or (day == 6 and time.hour > 16)

#calculate technical indicators
def calculate_technicals(df):
    df[['Sar', 'Trend']] = technical.parabolic_sar(df)
    df['MACD'] = technical.MACD(df['close'])
    df['MACD_shift'] = df['MACD'].shift(1)
    df['MACD_signal'] = 0
    df.loc[(df['MACD'] > 0) & (df['MACD_shift'] < 0),'MACD_signal'] = 1
    df.loc[(df['MACD'] < 0) & (df['MACD_shift'] > 0), 'MACD_signal'] = -1
    df['sigma'] = technical.moving_std(df['close'])
    df[['MACD_reversal','MACD_trend']] = technical.calculate_MACD_reversal(df['MACD'])
    return df

def stop_loss_take_profit(position):
    closed_trade_ID = []
    if len(position) > 0:
        for i in range(len(position)):
            print('Checking if take profit or stop loss point is reached for trade ' + str(position.loc[i,'tradeID']))
            price = dq.get_current_pricing(client = client,clientID = clientID,instrument = position.loc[i,'instrument'])
            ask = float(price['asks'][0]['price'])
            bid = float(price['bids'][0]['price'])
            if position.loc[i,'position'] == 'long' and (bid < position.loc[i,'stop_loss'] or bid > position.loc[i,'take_profit']):
                close_response = dq.close_trade(client = client,clientID = clientID,tradeID = int(position.loc[i,'tradeID']))
                if close_response is not None:
                    print('Long trade closed because take profit or stop loss limit reached')
                    closed_trade_ID.append(i)

            elif position.loc[i,'position'] == 'short' and (ask > position.loc[i,'stop_loss'] or ask < position.loc[i,'take_profit']):
                close_response = dq.close_trade(client = client,clientID = clientID,tradeID = int(position.loc[i,'tradeID']))
                if close_response is not None:
                    print('Short trade closed because take profit or stop loss limit reached')
                    closed_trade_ID.append(i)
            else:
                print(str(position.loc[i,'tradeID']) + ' trade has no stop loss or take profit point reached')
    position = position.drop(closed_trade_ID)
    return position




while(True):
    if is_trading_time() is True:
        #current position
        print('it is trading time')
        print('-------current open positions--------')
        trades_stop_loss = pd.read_csv('trades_stop_loss.csv')
        print(trades_stop_loss)
        m30_data = dq.request_data(client,instrument,frequency='M30')
        if m30_data is None:
            time.sleep(60)
            print('Reconnecting in 60 seconds')
            continue

        m30_data = calculate_technicals(m30_data)
        two_before_current_index = len(m30_data) - 3
        before_current_index = two_before_current_index +1
        current_index = two_before_current_index + 2
        current_period_change = m30_data.loc[current_index,'close'] - m30_data.loc[current_index,'open']
        current_period_sigma = m30_data.loc[current_index,'sigma']
        #print(m30_data)
        #if MACD sigal is positive
        if m30_data.loc[two_before_current_index,'MACD_reversal'] == 0:
            print('MACD signal not positive')
            #check if take profit or stop loss prices are reached#
            trades_stop_loss = stop_loss_take_profit(trades_stop_loss)
            signal_used = 0

        elif m30_data.loc[two_before_current_index,'MACD_reversal'] == 1 and m30_data.loc[before_current_index,'MACD_trend'] == 1 and signal_used !=1 and -current_period_change < 0.5* current_period_sigma:
            print('MACD signal is 1, checking trading logic')
            # check if take profit or stop loss prices are reached#
            trades_stop_loss = stop_loss_take_profit(trades_stop_loss)

            #if there is an existing open short position of this instrument, close it first#
            total_unit = 0
            if len(trades_stop_loss) >0:
                for i in range(len(trades_stop_loss)):
                    if ins_open_trades.loc[i,'position'] == 'short':
                        close_response = dq.close_trade(client = client,clientID = clientID,tradeID = int(trades_stop_loss.loc[i,'tradeID']))
                        if close_response is not None:
                            print('Short position closed because of MACD turned to Positive')
                            trades_stop_loss.drop(trades_stop_loss[trades_stop_loss['tradeID'] == int(i['id'])].index)
            #after close short position, the remaining positions will be either empty or long#
            current_opens = dq.get_opentrade_list(client, clientID)
            ins_open_trades = dq.get_ins_open_trades(current_opens, instrument=instrument)
            if len(ins_open_trades) > 0:
                for i in ins_open_trades:
                    total_unit = float(i['currentUnits']) + total_unit
            ##get current account information, check available margin
            account_info = dq.get_account_info(client = client,clientID =clientID)
            if account_info is None:
                print('trying to request account information 5 seconds later ')
                time.sleep(5)
                account_info = dq.get_account_info(client, clientID)
            available_margin = float(account_info['marginAvailable'])
            margin_rate = float(account_info['marginRate'])
            balance = float(account_info['marginAvailable'])
            rem_buying_power = available_margin/margin_rate
            max_buying_power = balance/margin_rate
            current_pricing = dq.get_current_pricing(client,clientID,instrument)
            ask_price = float(current_pricing['asks'][0]['price'])
            #the position of a currency pair cannot exceed 70% of total balance
            order_size = min(rem_buying_power/ask_price,(max_buying_power/ask_price)*load_percentage-total_unit)

            if order_size >10000:
                print('Order size about to submit:' + str(order_size))
            #place market order to fill the trade
                market_order = dq.create_market_order(client=client,clientID= clientID,instrument = instrument ,unit= int(order_size))
                if market_order is not None:
                    filled_price = float(market_order['price'])
                    order_id = int(market_order['orderID']) + 1
                    sigma = m30_data.loc[before_current_index,'sigma']
                    take_profit = filled_price + sigma * take_profit_points
                    stop_loss = filled_price - sigma*stop_loss_points
                    print('Long market order filled at price ' + str(filled_price))
                    trades_stop_loss = trades_stop_loss.append(pd.DataFrame([[order_id,instrument,'long',\
                                                                              stop_loss,take_profit]],\
                                                                            columns=['tradeID','instrument','position', 'stop_loss', 'take_profit']))
                    # avoid submitting order using the same signal
                    signal_used = 1
                else:
                    print('Failed to fill market order')
        ##when MACD signal is -1
        elif m30_data.loc[two_before_current_index,'MACD_reversal'] == -1 and m30_data.loc[before_current_index,'MACD_trend'] == -1 and signal_used != -1 and current_period_change < 0.5* current_period_sigma:
            print('MACD signal is -1, check trading logic')
            # check if take profit or stop loss prices are reached#
            trades_stop_loss = stop_loss_take_profit(trades_stop_loss)

            #if there is an existing open short position of this instrument, close it first#
            total_unit = 0
            if len(trades_stop_loss) >0:
                for i in range(len(trades_stop_loss)):
                    if ins_open_trades.loc[i,'position'] == 'short':
                        close_response = dq.close_trade(client = client,clientID = clientID,tradeID = int(trades_stop_loss.loc[i,'tradeID']))
                        if close_response is not None:
                            print('Short position closed because of MACD turned to Positive')
                            trades_stop_loss.drop(trades_stop_loss[trades_stop_loss['tradeID'] == int(i['id'])].index)
            #after close short position, the remaining positions will be either empty or short#
            current_opens = dq.get_opentrade_list(client, clientID)
            ins_open_trades = dq.get_ins_open_trades(current_opens, instrument=instrument)
            if len(ins_open_trades) > 0:
                for i in ins_open_trades:
                    total_unit = float(i['currentUnits']) + total_unit
            ##get current account information, check available margin
            account_info = dq.get_account_info(client,clientID)
            if account_info is None:
                print('trying to request account information 5 seconds later ')
                time.sleep(5)
                account_info = dq.get_account_info(client, clientID)
            available_margin = float(account_info['marginAvailable'])
            margin_rate = float(account_info['marginRate'])
            balance = float(account_info['marginAvailable'])
            rem_buying_power = available_margin/margin_rate
            max_buying_power = balance/margin_rate
            current_pricing = dq.get_current_pricing(client,clientID,instrument)
            bid_price = float(current_pricing['bids'][0]['price'])
            #the position of a currency pair cannot exceed 70% of total balance
            order_size = -min(rem_buying_power/bid_price,(max_buying_power/bid_price)*load_percentage+total_unit)

            if order_size < -10000:
                print('Order size about to submit:' + str(order_size))
            #place market order to fill the trade
                market_order = dq.create_market_order(client=client,clientID= clientID,instrument = instrument ,unit= int(order_size))
                if market_order is not None:
                    print(market_order)
                    filled_price = float(market_order['price'])
                    order_id = int(market_order['orderID']) +1
                    sigma = m30_data.loc[before_current_index,'sigma']
                    take_profit = filled_price - sigma * take_profit_points
                    stop_loss = filled_price + sigma * stop_loss_points
                    trades_stop_loss = trades_stop_loss.append(pd.DataFrame([[order_id,instrument,'short', \
                                                                              stop_loss, take_profit]], \
                                                                            columns=['tradeID','instrument','position', 'stop_loss',
                                                                                     'take_profit']))
                    #avoid submitting order using the same signal
                    signal_used = -1

                    print('Short market order filled at price ' + str(filled_price))

                else:
                    print('Failed to fill market order')

        trades_stop_loss.to_csv('trades_stop_loss.csv',index=False)
        time.sleep(60)

    else:
        print('Not trading time wait.....')
        time.sleep(60)
        continue


