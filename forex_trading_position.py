import pandas as pd

class position:
    def __init__(self, cash=10000, position={}):
        self.cash = cash
        self.position = position
        trade_log = {"timestamp": [], "product": [], "size": [], "cash_used": [], "order_type": [], "comment": []}
        self.trade_log = pd.DataFrame.from_dict(trade_log)
        self.value = self.cash

    def order(self, size, product, price, order_type='open', timestamp=None, comment=None):
        if order_type == 'open':
            if abs(size) * price > self.cash:
                print('Trying to order ' + str(size) + ' of ' + str(product) + ' at price ' + str(
                    price) + ', but insufficient fund available!')
            else:
                if str(product) not in self.position.keys():
                    self.position[str(product)] = size
                    self.cash = self.cash - size * price
                    self.trade_log = self.trade_log.append(
                        pd.DataFrame([[price, abs(size) * price, order_type, str(product), size, timestamp, comment]],
                                     columns=['price', 'cash_used', 'order_type', 'product', 'size', 'timestamp',
                                              'comment']))
                else:
                    self.position[str(product)] = self.position[str(product)] + size
                    self.cash = self.cash - size * price
                    self.trade_log = self.trade_log.append(
                        pd.DataFrame([[price, abs(size) * price, order_type, str(product), size, timestamp, comment]],
                                     columns=['price', 'cash_used', 'order_type', 'product', 'size', 'timestamp',
                                              'comment']))
        elif order_type == 'close':
            self.position[str(product)] = self.position[str(product)] + size
            self.value = self.cash
            self.cash = self.cash - size * price
            if size > 0:
                self.value = self.value - self.cash
            else:
                self.value = self.cash - self.value
            self.trade_log = self.trade_log.append(
                pd.DataFrame([[price, abs(size) * price, order_type, str(product), size, timestamp, comment]],
                             columns=['price', 'cash_used', 'order_type', 'product', 'size', 'timestamp', 'comment']))
        else:
            print('order type not recognized')

    def get_position(self):
        return self.position

    def get_cash(self):
        return self.cash

    def get_value(self):
        return self.value




