


========================================= BACKTESTING VECTORIZED AND EVENT DRIVEN ================================================

DISCLAIMER:
------------------------

This project is for illustration purposes. 
The codes and the strategies should not be 
understood as an investment suggestion.

The API key and password are provided in the 
modules and are used in a simulated account.
The reader can replace those keys with his/her
own. The provided API key and password are
used only for illustration purpouse and should
not be shared.

===================================================================================================================================

AUTHOR:
-------------------------

Salvatore Tambasco.

===================================================================================================================================

COMPONENTS:
--------------------------

In the main folder there are three python modules:

- CrossoverIterative.py;
- CrossoverVectorized.py;
- CrossoverTrader.py.

All the above mentioned modules contains Classes. The first two cointain a parent class inherited from some 
modules reposited in the CoreModules folder. The third modules contains a wrapper of the Binance broker API
for simulated trading in the cryptocurrency futures market.

The folder CoreModules cointains the following python modules:

- EventDrivenBacktester.py
- VectorizedBacktester.py
- Indicator.py

The first two modules provide the parent abstract classes employed further in the main folder. The Indicator 
module probides a class of the most popular trading indicators, such as simple and exponential moving average,
absolute price oscillator, moving average convergence divergence, Bollinger bands, and relative strength index.

Finally, the file .ipynb is a Jupyter Notebook with a presentation of the entire work.

===================================================================================================================================

PRESENTATION:
---------------------------

The presentation is provided in the file backtestingTour.py

It is articulated in the following topics:

 > Backtesting in Trading:
 
   - some generalities of backtesting, and structure of the work.
   
 > Vectorized Backtesting:
 
   - Explanation of the vectorized backtesting system.
   - How to use the class provided in the module.
   - What are the main shortfalls in vectorized backtesting.
   - How to overcome some shortfalls
   
 > Event Driven Backtesting:
 
   - Explanation behind the event driven backtesting, and motivations.
   - How to use the class provided in the module.
     
===================================================================================================================================
