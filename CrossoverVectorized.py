from CoreModules.VectorizedBacktester import VectorBacktest
from CoreModules.Indicator import Indicator
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from itertools import product
import warnings
warnings.filterwarnings("ignore")
plt.style.use("seaborn")



       


class DoubleCrossover(VectorBacktest):
    
    '''Double Crossover Backtest Child class (based on the VectorBacktest parent class).
       This Class provides a backtest for the exponential moving average trading strategy.
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
       
       Parameters: smas, list or array of length two, emas[0] = EMA_S, emas[1] = EMA_L
       
       ==================================================================================
       
       on_data()
       
       Parameters: smas, list or array of length two, emas[0] = EMA_S, emas[1] = EMA_L
       
       ==================================================================================
       
       optimize_strategy()
       
       ==================================================================================
       
       find_best_strategy()
       
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
        return "DoubleCrossover(symbol = {}, start = {}, end = {}, interval = {}, amount = {}, tc = {}, filepath = {}, binance = {}))".format(self.symbol, self.start, self.end, self.interval, self.amount, self.tc, self.filepath, self.binance)
    
    
    
    def test_strategy(self, emas):
        
        self.EMA_S = emas[0]
        self.EMA_L = emas[1]
        
        self.on_data(emas = emas)
        self.run_backtest()
        
        data = self.results.copy()
        
        data['creturns'] = data.returns.cumsum().apply(np.exp) 
        data['cstrategy'] = data.strategy.cumsum().apply(np.exp)
        
        self.results = data
        self.print_performance()
    
    def on_data(self, emas):
        
        data = self.data[['Close', 'returns']].copy()
        data['EMA_S'] = Indicator(data.Close).EMA(emas[0])
        data['EMA_L'] = Indicator(data.Close).EMA(emas[1])
        
        data.dropna(inplace = True)
        
        data['positions'] = 0
        
        cond1 = data.EMA_S > data.EMA_L 
        cond2 = data.EMA_S < data.EMA_L
        
        data.loc[cond1, 'positions'] = 1
        data.loc[cond2, 'positions'] = -1
        
        self.results = data
    
    def optimize_strategy(self, EMA_S_range, EMA_L_range):
        
        'performs a grid search on optimal SMA_S and SMA_L based on maximizing returns'
        
        performance_metric = self.calculate_multiple
            
        s_range = range(*EMA_S_range)
        l_range = range(*EMA_L_range)
        
        combinations = list(product(s_range, l_range))
        
        performance = []
        
        for comb in combinations:
            self.on_data(emas = comb)
            self.run_backtest()
            performance.append(performance_metric(self.results.strategy))
            
        self.performance_overview = pd.DataFrame(data = np.array(combinations), columns = ['EMA_S', 'EMA_L'])
        self.performance_overview['performance'] = performance
        
        self.find_best_strategy()
            
        
    def find_best_strategy(self):
        
        '''Related method to optimize_strategy. Returns best parameters and best performance.'''
        
        best = self.performance_overview.nlargest(1, 'performance')
        best_short = best.EMA_S.iloc[0]
        best_large = best.EMA_L.iloc[0]
        best_performance = best.performance.iloc[0]
        
        print('Return perc. {} | EMA_S = {} | EMA_L = {}'.format(best_performance, 
                                                                  best_short, 
                                                                  best_large))
        
        self.test_strategy(emas = (best_short, best_large))
        
        
    