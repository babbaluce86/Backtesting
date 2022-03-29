import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class Indicator(object):
    
    '''Provides a class of most used indicators in trading.
       Code implemented by Salvatore Tambasco.'''
    
    '''
    ----------------------------------------------------
    ++++++++++++++++++METHODS+++++++++++++++++++++++++++
    ----------------------------------------------------
       SMA
       
       Simple Moving Average, if volatility is set to 
       True, then a standard deviation simple moving
       average is performed.
       
    ====================================================
       
       EMA
       
       Exponential Moving Average, if volatility is set to 
       True, then a standard deviation exponential moving
       average is performed.
       
    ======================================================
    
       APO
       
       Absolute Price Oscillator
       
    ======================================================
       
       MACD
       
       Moving Average Convergence Divergence
       
    ======================================================   
    
       BollingerBands
       
       Bollinger Bands indicator
       
    ======================================================
    
       RSI
       
       Relative Strength Index
       
    ======================================================
    
       '''
    
    def __init__(self, data):
        
        if isinstance(data, pd.Series):
            
            self.data = data.to_frame('Close')
            
        else:
            
            self.data = data
        
        
    def SMA(self, sma, volatility = False):
        
        data = self.data.copy()
        
        if volatility:
            return data.Close.rolling(window = sma).std()
            
        else:
            return data.Close.rolling(window = sma).mean()
    
    
    def EMA(self, ema, volatility = False):
        
        data = self.data.copy()
        
        if volatility:
            return data.Close.ewm(span = ema, adjust = True).mean()
        
        else:
            return data.Close.ewm(span = ema, adjust = True).mean()
    
    
    def APO(self, ema_s, ema_l):
        
        data = self.data.copy()
        fast_ema = self.EMA(ema = ema_s)
        slow_ema = self.EMA(ema = ema_l)
        difference = fast_ema.sub(slow_ema)
        data['APO'] = difference
        
        return data
    
    def MACD(self, ema_line_s, ema_line_l, ema_signal):
        
        data = self.data.copy()
        ema_s = self.EMA(ema = ema_line_s)
        ema_l = self.EMA(ema = ema_line_l)
        ema_m = self.EMA(ema = ema_signal)
        
        data['MACD_line'] = ema_s.sub(ema_l)
        data['MACD_signal'] = ema_m
        data['MACD_hist'] = data.MACD_line.sub(data.MACD_signal)
        
        return data
    
    def BollingerBands(self, sma, scaling_factor):
        
        data = self.data.copy()
        
        data['middleBand'] = self.SMA(sma)
        data['upperBand'] = data.middleBand + scaling_factor * self.SMA(sma = sma, volatility = True)
        data['lowerBand'] = data.middleBand - scaling_factor * self.SMA(sma = sma, volatility = True)
        
        return data
    
    def RSI(self, sma = None, ema = None):
        
        data = self.data.copy()
        
        delta = data.Close.diff()[1:]
        
        up, down = delta.clip(lower=0), delta.clip(upper=0)
        
        if sma:
            
            avgGain = up.rolling(window=sma).mean()
            avgLoss = down.rolling(window=sma).mean()
            
        elif ema:
            
            avgGain = up.ewm(span = ema, adjust = True).mean()
            avgLoss = down.ewm(span = ema, adjust = True).mean()
            
        rs = avgGain.div(avgLoss)
        rsi = 100.0 - (100.0 / (1 + rs))
        
        data['RSI'] = rsi
        
        return data