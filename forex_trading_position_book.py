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

position_book = dq.request_position_book(client,instrument)
print(position_book)