from abc import ABCMeta, abstractmethod
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from binance.client import Client
plt.style.use("seaborn")


api_key = "82358fba3ec8bf87816d4f5590460d4001824e7ced03fc54d3ac4628919964be"
secret_key = "40943bfd8deaf625a753cf46a857546cf53c16f58ac1e907a94476a73da0595c"

client = Client(api_key = api_key, 
                api_secret = secret_key, 
                tld = "com", 
                testnet = True) # Testnet!!!

class VectorBacktest(object):
    
    '''Computes Vectorized backtesting. Code implemented by Salvatore Tambasco.
    
       ------------------------------------------------------------------------
       +++++++++++++++++++++++++STATIC METHODS+++++++++++++++++++++++++++++++++
       ------------------------------------------------------------------------
       get_data()
       ========================================================================
       run_backtest()
       ========================================================================
       add_session()
       ========================================================================
       add_leverage()
       ========================================================================
       plot_results()
       ========================================================================
       plot_performance()
       ========================================================================
       print_performance()
       ========================================================================
       calculate_multiple()
       ========================================================================
       
       ------------------------------------------------------------------------
       +++++++++++++++++++++++++ABSTRACT METHODS+++++++++++++++++++++++++++++++
       ------------------------------------------------------------------------
       test_strategy()
       ========================================================================
       on_data()
       ========================================================================
       optimize_strategy()
       ========================================================================
       find_best_strategy()
       ========================================================================
       
       ------------------------------------------------------------------------
       ++++++++++++++++++++++++++++++PARAMETERS++++++++++++++++++++++++++++++++
       ------------------------------------------------------------------------
       
       symbol
       
       this is the thicker of the futures cryptocurrency for which we backtest
       
       ========================================================================
       
       start
       
       give a datetime into string format YYYY-MM-dd
       
       =========================================================================
       
       end
       
       give a datetime into string format YYYY-MM-dd
       
       ==========================================================================
       
       interval
       
       give the resolution of the bars that needs to be considered in the backtest
       
       ==========================================================================
       
       tc
       
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
    
    def __init__(self, symbol, start, 
                 interval, 
                 tc, 
                 amount,
                 end = None, 
                 filepath=None, 
                 binance=False):
        
        
        self.filepath = filepath
        self.binance = binance
        self.symbol = symbol
        self.start = start
        self.end = end
        self.interval = interval
        self.tc = tc
        self.amount = amount
        
        self.total_days = 365.25
            
        self.results = None    
            
        self.get_data()
        
        self.tp_year = (self.data.Close.count() / ((self.data.index[-1] - self.data.index[0]).days / self.total_days))
        
    def get_data(self):
        
        '''This method displays the trading data. If a csv file is given then the method will organise the 
           return the data with the below features. Whereas if a csv file is not given then the method 
           cleans the data pulled from the testnet binance API and returns a dataframe with the below features.'''
        
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
        
        
        
        
    @abstractmethod
    def test_strategy(self):
        '''This method should be implemented in a child class based upon the on_data() method below. Tests the strategy
            with the rationale given in the on_data() method.'''
        raise NotImplementedError("Should implement test_strategy()")
    
    @abstractmethod
    def on_data(self):
        '''This method should be implemented in a child class, 
            it provides the data manuevering of the strategy's rationale'''
        raise NotImplementedError("Should implement on_data()")
        
    def run_backtest(self):
        ''' Runs the strategy backtest.
        '''    
        data = self.results.copy()
        data["strategy"] = data["positions"].shift(1) * data["returns"]
        data["trades"] = data.positions.diff().fillna(0).abs()
        data.strategy = data.strategy + data.trades * self.tc
        data['total_sreturn'] = data['returns'].cumsum()
        data['drawdown'] = data['total_sreturn'] - data['total_sreturn'].cummax()
        
        
        self.results = data
        
        
    def add_sessions(self, visualize = False): 
        ''' 
        Adds/Labels Trading Sessions and their compound returns.
        
        Parameter
        ============
        visualize: bool, default False
            if True, visualize compound session returns over time
        '''
        
        if self.results is None:
            print("Run test_strategy() first.")
            
        data = self.results.copy()
        data["session"] = np.sign(data.trades).cumsum().shift().fillna(0)
        data["session_compound"] = data.groupby("session").strategy.cumsum().apply(np.exp) - 1
        self.results = data
        if visualize:
            data["session_compound"].plot(figsize = (12, 8))
            plt.show()  
        
    def add_leverage(self, leverage, report = True): 
        ''' 
        Adds Leverage to the Strategy.
        
        Parameter
        ============
        leverage: float (positive)
            degree of leverage.
        
        report: bool, default True
            if True, print Performance Report incl. Leverage.
        '''
        self.add_sessions()
        self.leverage = leverage
        
        data = self.results.copy()
        data["simple_ret"] = np.exp(data.strategy) - 1
        data["eff_lev"] = leverage * (1 + data.session_compound) / (1 + data.session_compound * leverage)
        data.eff_lev.fillna(leverage, inplace = True)
        data.loc[data.trades !=0, "eff_lev"] = leverage
        levered_returns = data.eff_lev.shift() * data.simple_ret
        levered_returns = np.where(levered_returns < -1, -1, levered_returns)
        data["strategy_levered"] = levered_returns
        data["cstrategy_levered"] = data.strategy_levered.add(1).cumprod()
        
        self.results = data
            
        if report:
            self.print_performance(leverage = True)
        
    def plot_results(self):
        
        '''Plots the results of the test_strategy method against the naive benchmark buy and hold'''
        
        if self.results is None:
            print('Run test_strategy first')
        
        else:
            title = '{} | TC = {}'.format(self.symbol, self.tc)
            self.results[['creturns','cstrategy']].plot(figsize = (16,9), title = title)
        
    @abstractmethod
    def optimize_strategy(self):
        '''This method should be implemented when the given strategy parameters are tuned to maximize 
           returns or sharpe ratio of the strategy '''
        raise NotImplementedError("Should implement optimize_strategy()")
        
    @abstractmethod
    def find_best_strategy(self):
        '''This method should be implemented as a optimal parameter grid search based on the 
            optimize_strategy() method'''
        raise NotImplementedError("Should implement best_strategy()")
        
    def plot_performance(self):
        
        '''Plots the performance of the given strategy, namely the wealth evolution and the drawdon
           on the given trading window.'''
        
        if self.results is None:
            print('Run test_strategy first')
            
        else:
            
            cash_evolution = np.exp(self.results.total_sreturn)*self.amount
            
            title = '{} | TC = {}'.format(self.symbol, self.tc)
            
            fig = plt.figure(figsize = (20,20))
            fig.suptitle(title, fontsize = 20)
            
            plt.plot(cash_evolution, label = 'Wealth Evolution')
            
            plt.show()
        
        
    def print_performance(self):
        ''' Calculates and prints various Performance Metrics.
        '''
        
        data = self.results.copy()
        
        
        n_trades = data.trades.sum()
        winners = data.query('trades != 0 & strategy > 0').shape[0] 
        loosers = n_trades - winners
        win_ratio = round(winners / n_trades, 4)
        loose_ratio = round(loosers / n_trades, 4)
        maximum_drawdown = round(data.drawdown.min(), 4)
        terminal_wealth = round(np.exp(data.total_sreturn[-1]) * self.amount, 4)
        sharpe = round(data.total_sreturn.mean() / data.total_sreturn.std(), 4)
        
        
        strategy_multiple = round(self.calculate_multiple(data.strategy), 4)
        bh_multiple =       round(self.calculate_multiple(data.returns), 4)
        outperf =           round(strategy_multiple - bh_multiple, 4)
        
        print(100 * "=")
        print("STRATEGY PERFORMANCE | INSTRUMENT = {} |".format(self.symbol))
        print(100 * "-")
        print('TRADING PERFORMANCE MEASURES:')
        print('\n')
        print('Number of Trades: {}'.format(n_trades))
        print('Number of Winners: {}'.format(winners))
        print('Number of Loosers: {}'.format(loosers))
        print('\n')
        print('Win Ratio: {}'.format(win_ratio))
        print('Loose Ratio: {}'.format(loose_ratio))
        print('\n')
        print('Terminal Wealth: {}'.format(terminal_wealth))
        print('Maximum Drawdown: {}'.format(maximum_drawdown))
        print(100 * '-')
        print("PERFORMANCE MEASURES:")
        print("\n")
        print("Multiple (Strategy):         {}".format(strategy_multiple))
        print("Multiple (Buy-and-Hold Benchmark):     {}".format(bh_multiple))
        print(38 * "-")
        print("Out-/Underperformance:       {}".format(outperf))
        print("\n")
        print("Sharpe Ratio:                {}".format(sharpe))
        
        print(100 * "=")
        
    def calculate_multiple(self, series):
        '''This is simply implied when calculating the multiple of the strategy returns, i.e.
            as if the trader would invest the amount of 1 dollar. '''
        return np.exp(series.sum())
    
    