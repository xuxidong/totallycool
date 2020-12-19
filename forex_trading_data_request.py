import oandapyV20 as oda20
import oandapyV20.endpoints.instruments as ins
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.accounts as accunts
import oandapyV20.endpoints.trades as trades
import oandapyV20.endpoints.pricing as pricing
import pandas as pd

## convert candle data from JSON to pandas dataframe
def dict_to_df(diction):
    data_dic = []
    for i in diction:
        price = i['mid']
        time_stamp = i['time']
        volume = i['volume']
        complete = i['complete']
        price['time'] = time_stamp
        price['volume'] = volume
        price['complete'] = complete
        data_dic.append(price)
    data_dic = pd.DataFrame(data_dic)
    data_dic = data_dic.rename({'o':'open',
        'h':'high',
        'l':'low',
        'c':'close'},axis = 'columns')
    #data_dic.columns = ['close','complete','high','low','open','time','volume']
    data_dic[['close','high','low','open']] = data_dic[['close','high','low','open']].astype(dtype=float)
    return data_dic

##request candle data
def request_data(client,instrument,frequency='M30',count = 60):
    param = {
            'count': count,
            'granularity': frequency
        }
    candle_data = ins.InstrumentsCandles(instrument=instrument, params=param)
    client.request(candle_data)
    candle_data = candle_data.response['candles']
    candle_data = dict_to_df(candle_data)
    return candle_data

##request position book, percentage of long and short position at each price
def request_position_book(client,instrument):
    position_book = ins.InstrumentsPositionBook(instrument= instrument)
    try:
        client.request(position_book)
        position_book = position_book.response['positionBook']['buckets']
    except Exception:
        print('no position book returned because of exception')
        return None
    return pd.DataFrame(position_book)

##request current order book
def request_order_book(client,instrument):
    order_book = ins.InstrumentsOrderBook(instrument=instrument)
    try:
        client.request(order_book)
        order_book = order_book.response['orderBook']['buckets']
    except Exception:
        print('Failed to request order book because of exception')
        return None
    return pd.DataFrame(order_book)

#create limit order
def create_limit_order(client,clientID,instrument,unit,price,stop_loss,timeInForce= 'GTC'):
    order_parms = {
        'order':{
            'price':str(price),
            'stopLossOnFill':{
                'timeInForce':timeInForce,
                'price':str(stop_loss),
            },
            'timeInForce': timeInForce,
            'instrument':instrument,
            'units':str(unit),
            'type':'LIMIT',
            'positionFill':'DEFAULT'
        }
    }
    order_request = orders.OrderCreate(accountID=clientID,data=order_parms)
    try:
        client.request(order_request)
        order_request = order_request.response
    except Exception:
        print('Failed to create order because of exception')
        return None
    return pd.DataFrame(order_request['orderCreateTransaction'])

## get the list of all the orders of this account
def get_order_list(client,clientID):
    order_list_request = orders.OrderList(clientID)
    try:
        client.request(order_list_request)
        order_list = order_list_request.response
    except Exception:
        print('Failed to request order list because of exception')
        return None
    return order_list

## get the list of pending orders of this account
def get_pending_order_list(client,clientID):
    order_list_request = orders.OrdersPending(clientID)
    try:
        client.request(order_list_request)
        order_list = order_list_request.response
    except Exception:
        print('Failed to request pending order list because of exception')
        return None
    return order_list

#replace a current order with a new order
def replace_order(client,clientID,orderID,unit,instrument,price,type):
    data  = {
        'order':{
            'units':str(unit),
            'instrument':instrument,
            'price':str(price),
            'type':type
        }
    }
    order_replacement_request = orders.OrderReplace(accountID=clientID,orderID= orderID,data=data)
    try:
        client.request(order_replacement_request)
        order_replacement_request = order_replacement_request.response
    except Exception:
        print('Failed to replace order because of Exception')
        return None
    return pd.DataFrame(order_replacement_request)

#cancel order
def cancel_order(client,clientID,orderID):
    cancel_order_request = orders.OrderCancel(accountID=clientID,orderID=orderID)
    try:
        client.request(cancel_order_request)
        cancel_order_response = cancel_order_request.response
    except Exception:
        print('Failed to cancel order because of Exception')
        return None
    return cancel_order_response

#place a market order
def create_market_order(client,clientID,instrument,unit):
    data = {
        'order':{
            'units':str(unit),
            'instrument':instrument,
            'tumeInForce':'FOK',
            'type':'MARKET',
            'positionFill':'DEFAULT'
        }
    }
    market_order = orders.OrderCreate(accountID=clientID,data=data)
    try:
        client.request(market_order)
        market_order = market_order.response['orderFillTransaction']
    except Exception:
        print('Failed to create market order because of Exception')
        return None
    return market_order



#get the list of all the trades
def get_trade_list(client,clientID,instrument = None):
    if instrument is None:
        trade_list = trades.TradesList(accountID=clientID)
        try:
            client.request(trade_list)
            trade_list = trade_list.response
        except Exception:
            print('Failed to get trade list because of Exception')
            return None
    else:
        parms = {
            'instrument':instrument
        }
        trade_list = trades.TradesList(accountID=clientID,params=parms)
        try:
            client.request(trade_list)
            trade_list = trade_list.response
        except Exception:
            print('Failed to get trade list of ' + str(instrument) + 'because of Exception' )
            return None
    return trade_list

#get the list of all the open trades
def get_opentrade_list(client,clientID):
    trade_list = trades.OpenTrades(accountID=clientID)
    try:
        client.request(trade_list)
        trade_list = trade_list.response
    except Exception:
        print('Failed to get trade list because of Exception')
        return None
    return trade_list

#get the details of a single trade
def get_trade_detail(client,clientID,tradeID):
    trade_details = trades.TradeDetails(accountID=clientID,tradeID=tradeID)
    try:
        client.request(trade_details)
        trade_details = trade_details.response
    except Exception:
        print('Failed to get trade details because of Exception')
        return None
    return trade_details

#Fully or partially close a open trade
def close_trade(client,clientID,tradeID,unit=None):
    if unit is None:
        close_trade = trades.TradeClose(accountID=clientID,tradeID = tradeID)
        try:
            client.request(close_trade)
            close_trade_response = close_trade.response
        except Exception:
            print('Failed to close trade because of Exception')
            return None
    else:
        data = {'unit':unit}
        close_trade = trades.TradeClose(accountID=clientID, tradeID=tradeID,data=data)
        try:
            client.request(close_trade)
            close_trade_response = close_trade.response
        except Exception:
            print('Failed to close trade because of Exception')
            return None
    return close_trade_response

#get information of account
def get_account_info(client,clientID):
    account_info = accunts.AccountSummary(accountID=clientID)
    try:
        client.request(account_info)
        account_info = account_info.response['account']
    except Exception:
        print('Failed to extract account information because of exception')
        return None
    return account_info

def get_ins_open_trades(trades_list,instrument):
    instrumrnt_open_trades = []
    if trades_list is None:
        return instrumrnt_open_trades
    else:
        current_open_trades = trades_list['trades']
        if len(current_open_trades) > 0 :
            for i in current_open_trades:
                if i['instrument'] == instrument:
                    instrumrnt_open_trades.append(i)
    return instrumrnt_open_trades

#get market price
def get_current_pricing(client,clientID,instrument):
    params = {
        'instruments':instrument
    }

    price = pricing.PricingInfo(accountID=clientID,params=params)
    try:
        client.request(price)
        price = price.response['prices'][0]
    except Exception:
        print('Failed to request market price')
        return None
    return price



client = oda20.API(access_token='39b0f06eeedfdb4bfe2b7d60708ad253-648a30baf6d376c2296d8e8fb1d9c2e7')
clientID = '101-001-8411104-001'
instrument = 'AUD_USD'
load_percentage = 0.7
take_profit_points = 5
stop_loss_points = 3
unit = 100
data = {
        'order':{
            'units':str(unit),
            'instrument':instrument,
            'tumeInForce':'FOK',
            'type':'MARKET',
            'positionFill':'DEFAULT'
        }
    }

#create_order = orders.OrderCreate(accountID=clientID,data=data)
#client.request(create_order)
#print(create_order.response)

