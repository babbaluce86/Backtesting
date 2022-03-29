from abc import ABCMeta, abstractmethod
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from binance.client import Client
plt.style.use("seaborn")


api_key = "your_api_key"
secret_key = "your_secret_key"

client = Client(api_key = api_key, 
                api_secret = secret_key, 
                tld = "com", 
                testnet = True) # Testnet!!!



class IterateBacktest():
    
    '''Computes event drivent backtesting. 
       
       Code implemented by Salvatore Tambasco.
    
       ------------------------------------------------------------------------
       +++++++++++++++++++++++++STATIC METHODS+++++++++++++++++++++++++++++++++
       ------------------------------------------------------------------------
       get_data()
       ========================================================================
       plot_data()
       
       attribute: cols
       
       ========================================================================
       get_values()
       
       attribute: bar as integer.
       
       ========================================================================
       print_current_balance()
       
       attribute: bar as integer.
       
       ========================================================================
       buy()
       
       attributes: bar, qty if given quantity is a float, amount is a float.
       
       ========================================================================
       sell()
       
       attributes: bar, qty if given quantity is a float, amount is a float.
       
       ========================================================================
       go_long()
       
       attributes: bar, qty if given quantity is a float, amount is a float.
       
       ========================================================================
       go_short()
       
       attributes: bar, qty if given quantity is a float, amount is a float.
       
       ========================================================================
       print_current_position_value()
       
       attribute: bar as integer.
       
       ========================================================================
       print_current_nav()
       
       attribute: bar as integer.
       
       ========================================================================
       close_position()
       
       attribute: bar as integer.
       
       ========================================================================
       print_performance()
       
       ========================================================================
       pnl_dataframe()
       
       ========================================================================
       plot_performance()
       
       ------------------------------------------------------------------------
       +++++++++++++++++++++++++ABSTRACT METHODS+++++++++++++++++++++++++++++++
       ------------------------------------------------------------------------
       test_strategy()
       
       to be implemented with the strategy rationale.
       
       ========================================================================
       on_data()
       
       to be implemented with the data manipulation rationale.
       
       ------------------------------------------------------------------------
       ++++++++++++++++++++++++++++++PARAMETERS++++++++++++++++++++++++++++++++
       ------------------------------------------------------------------------
       
       symbol
       
       this is the thicker of the futures cryptocurrency for which we backtest
       
       ========================================================================
       
       start
       
       give a datetime into string format YYYY-MM-dd
       
       =========================================================================
       
       interval
       
       give the resolution of the bars that needs to be considered in the backtest
       
       ==========================================================================
       
       amount
       
       give the amount of cash the trader want to invest
       
       
       ==========================================================================
       
       commissions
       
       trading costs, mostly for binance bitcoin futures assume 0.001 commission
       the iceberg costs can be implemented with order book data availability.
       
       ===========================================================================
       
       filepath
       
       if given then input a .csv file.
       
       ============================================================================
       
       binance
       
       if set to True pulls the data from the Binance API 
       with my testnet credentials.
       
       ''' 
    

    def __init__(self, symbol, start, interval, amount, commissions = None, filepath = None, binance = True):
        
        self.symbol = symbol
        self.start = start
        self.interval = interval
        self.commissions = commissions
        self.filepath = filepath
        self.binance = binance
        self.initial_balance = amount
        self.current_balance = amount
        self.units = 0
        self.trades = 0
        self.position = 0
        self.pnl = []
        
        self.get_data()
        

    def get_data(self):
        
        if self.filepath:
            
            raw = pd.read_csv(self.filepath, parse_dates = ['Date'], index_col = 'Date')[['Close', 'Volume']]
            raw.index = pd.to_datetime(raw.index, utc = True)
            
        elif self.binance:
            
            bars = client.futures_historical_klines(symbol = self.symbol, interval = self.interval,
                                        start_str = self.start, end_str = None, limit = 1000)
            raw = pd.DataFrame(bars)
            raw["Date"] = pd.to_datetime(raw.iloc[:,0], unit = "ms")
            raw.columns = ["Open Time", "Open", "High", "Low", "Close", "Volume",
                          "Clos Time", "Quote Asset Volume", "Number of Trades",
                          "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore", "Date"]
            raw = raw[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
            raw.set_index("Date", inplace = True)
            for column in raw.columns:
                raw[column] = pd.to_numeric(raw[column], errors = "coerce")
                
        raw['returns'] = np.log(raw.Close/raw.Close.shift(1))
    
            
        self.data = raw[['Close', 'Volume', 'returns']]

    def plot_data(self, cols = None):  
        if cols is None:
            cols = "Close"
        self.data[cols].plot(figsize = (12, 8), title = self.symbol)
    
    def get_values(self, bar):
        date = str(self.data.index[bar])
        price = round(self.data.Close.iloc[bar], 5)
        return date, price
    
    def print_current_balance(self, bar):
        date, price = self.get_values(bar)
        print("{} | Current Balance: {}".format(date, round(self.current_balance, 2)))
        
    def buy(self, bar, qty = None, amount = None):
        date, price = self.get_values(bar)
        if self.commissions:
            price += self.commissions
        if amount is not None: # use units if units are passed, otherwise calculate units
            qty = round(amount / price / 10, 4)
        self.current_balance -= qty * price # reduce cash balance by "purchase price"
        self.units += qty
        self.trades += 1
        
        self.pnl.append((date, price, self.current_balance, 1.0))
        
        print("{} |  Buying {} for {}".format(date, qty, round(price, 5)))
    
    def sell(self, bar, qty = None, amount = None):
        date, price = self.get_values(bar)
        if self.commissions:
            price -= self.commissions 
        if amount is not None: # use units if units are passed, otherwise calculate units
            qty = round(amount / price / 10, 4)
        self.current_balance += qty * price # increases cash balance by "purchase price"
        self.units -= qty
        self.trades += 1
        
        self.pnl.append((date, price, self.current_balance, -1.0))
        
        
        print("{} |  Selling {} for {}".format(date, qty, round(price, 5)))
        
    
    def go_long(self, bar, qty = None, amount = None):
        if self.position == -1:
            self.buy(bar, qty = -self.units) # if short position, go neutral first
        if qty:
            self.buy(bar, qty = qty)
        elif amount:
            if amount == "all":
                amount = self.current_balance
            self.buy(bar, amount = amount) # go long

    # helper method
    def go_short(self, bar, qty = None, amount = None):
        if self.position == 1:
            self.sell(bar, qty = self.units) # if long position, go neutral first
        if qty:
            self.sell(bar, qty = units)
        elif amount:
            if amount == "all":
                amount = self.current_balance
            self.sell(bar, amount = amount) # go short
            
            
    @abstractmethod
    def test_strategy(self):
        raise NotImplementedError("Should implement test_strategy()")
    
    @abstractmethod
    def on_data(self):
        raise NotImplementedError("Should implement on_data()")        
    
    
    def print_current_position_value(self, bar):
        date, price = self.get_values(bar)
        cpv = self.units * price
        print("{} |  Current Position Value = {}".format(date, round(cpv, 2)))
    
    def print_current_nav(self, bar):
        date, price = self.get_values(bar)
        nav = self.current_balance + self.units * price
        print("{} |  Net Asset Value = {}".format(date, round(nav, 2)))
        
    def close_position(self, bar):
        date, price = self.get_values(bar)
        print(75 * "-")
        print("{} | +++ CLOSING FINAL POSITION +++".format(date))
        self.current_balance += self.units * price # closing final position (works with short and long!)
        self.current_balance -= (abs(self.units) * self.commissions) # substract half-spread costs
        print("{} | closing position of {} for {}".format(date, self.units, price))
        self.units = 0 # setting position to neutral
        self.trades += 1
        perf = (self.current_balance - self.initial_balance) / self.initial_balance * 100
        self.print_current_balance(bar)
        print("{} | net performance (%) = {}".format(date, round(perf, 2) ))
        print("{} | number of trades executed = {}".format(date, self.trades))
        print(75 * "-")
        
    def pnl_dataframe(self):
        
        self.results = pd.DataFrame(self.pnl)
        
        self.results.columns = ['date', 'price', 'balance', 'positions']
        
        self.results.set_index('date', inplace = True)
        
        self.results['returns'] = np.log(self.results.price / self.results.price.shift(1))
        self.results['strategy'] =  self.results.positions.shift(1)*self.results.returns
        self.results['trades'] = self.results.positions.diff().fillna(0).abs()
        self.results.strategy = self.results.strategy + self.results.trades * self.commissions
        self.results['total_sreturn'] = self.results['returns'].cumsum()
        self.results['drawdown'] = self.results['total_sreturn'] - self.results['total_sreturn'].cummax()
        
    
    def print_performance(self):
        
        self.pnl_dataframe()
        
        data = self.results.copy()
        
        n_trades = data.trades.sum()
        sharpe = round(data.strategy.mean() / data.strategy.std(),4)
        account_balance = round(data.balance[-1])
        winners = data.query('positions == 1 & strategy > 0').shape[0] + data.query('positions == -1 & strategy > 0').shape[0]
        loosers = n_trades - winners
        win_ratio = round(winners / n_trades, 2)
        loose_ratio = round(loosers / n_trades, 2)
        max_drawdown = round(self.results.drawdown.min(),4)
        
        print('+++++++++++ PERFORMANCE +++++++++++++')
        print('-'*100)
        print('Number of trades {}'.format(n_trades))
        print('Final account balance {}'.format(data.balance[-1]))
        print('Number of winning trades {}'.format(winners))
        print('Number of loosing trades {}'.format(loosers))
        print('='*100)
        print('Win Ratio {}'.format(win_ratio))
        print('Loose Ratio {}'.format(loose_ratio))
        print('Maximum Drawdown {}'.format(max_drawdown))
        print('='*100)
        print('Sharpe Ratio {}'.format(sharpe))
        
    def plot_performance(self, amount):
        
        self.pnl_dataframe()
        
        data = self.results.copy()
        
        multiple_cash = np.exp(data.total_sreturn)
        cash_evolution = multiple_cash * amount
        
        plt.figure(figsize = (20,20))
        
        plt.plot(cash_evolution, label = 'acount evolution')
        
        plt.legend(loc = 'upper left')
        
        plt.show()
        
        
        
