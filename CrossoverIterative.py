from CoreModules.EventDrivenBacktester import IterateBacktest
from CoreModules.Indicator import Indicator
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from itertools import product
import warnings
warnings.filterwarnings("ignore")
plt.style.use("seaborn")


class Crossover2(IterateBacktest):
    
    
    '''Double Crossover Backtest Child class (based on the IterateBacktest parent class).
       This Class provides a backtest for the exponential moving average crossover
       trading strategy.
       
       The signal is displayed as follows:
       if EMA_S > EMA_L => buy, if EMA_L > EMA_S => sell, else do nothing.
       
       Code implemented by Salvatore Tambasco. 
       
       ---------------------------------------------------------------------------------
       ++++++++++++++++++++++++++++++++++METHODS++++++++++++++++++++++++++++++++++++++++
       ---------------------------------------------------------------------------------
       
       __repr__()
       
       Prints the inerited parameters of the strategy
       
       ==================================================================================
       
       test_strategy()
       
       Parameters: emas, list or array of length two, emas[0] = EMA_S, emas[1] = EMA_L
       
       ==================================================================================
       
       on_data()
       
       Parameters: emas, list or array of length two, emas[0] = EMA_S, emas[1] = EMA_L
       
       ==================================================================================
       
       
       ----------------------------------------------------------------------------------
       +++++++++++++++++++++++++++++++PARAMETERS+++++++++++++++++++++++++++++++++++++++++
       ----------------------------------------------------------------------------------
       ****All parameters are inherited from the parent class****
       
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
    
    
    
    def __repr__(self):
        return "Crossover2(symbol = {}, start = {}, interval = {}, amount = {}, commissions = {}, filepath = {}, binance = {}))".format(self.symbol, self.start, self.interval, self.amount, self.commissions, self.filepath, self.binance)
    
            
    def test_strategy(self, emas):
        
        
        print('.'*100)
        
        print('Testing Crossover Strategy | {} | EMA_S = {} & EMA_L = {}'.format(self.symbol,emas[0], emas[1]))
        
        print('.'*100)
        
        self.positions = 0
        self.trades = 0
        self.current_balance = self.initial_balance
        self.on_data(emas)
        
        
        
        for bar in range(len(self.data)-1): # all bars (except the last bar)
            
            if self.data["EMA_S"].iloc[bar] > self.data["EMA_L"].iloc[bar]: # signal to go long
                if self.position in [0, -1]:
                    self.go_long(bar, amount = "all") # go long with full amount
                    self.position = 1  # long position
                    
            elif self.data["EMA_S"].iloc[bar] < self.data["EMA_L"].iloc[bar]: # signal to go short
                if self.position in [0, 1]:
                    self.go_short(bar, amount = "all") # go short with full amount
                    self.position = -1 # short position
        self.close_position(bar+1) # close position at the last bar
        
        
    def on_data(self, emas):
        
        data = self.data.copy()
        
        data['EMA_S'] = Indicator(data.Close).EMA(emas[0])
        data['EMA_L'] = Indicator(data.Close).EMA(emas[1])
        data.dropna(inplace = True)
        
        cond1 = data.EMA_S > data.EMA_L
        cond2 = data.EMA_L > data.EMA_S
        
        data.loc[cond1, 'positions'] = 1
        data.loc[cond2, 'positions'] = -1
        
        
        self.data = data
    
        