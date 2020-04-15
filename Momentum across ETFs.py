###Between 5 different ETFs, representing different asset classes 
###Try to pick 2 ETFs with the highest price momentum 
###Hold them for 20 days and rebalance
###The Holding period associated with the highest SR 
###in the training period is used to test the model in the test period

import pandas as pd
from datetime import datetime
import yfinance as yf
import statistics

time_period = '160mo'
time_now = datetime.now()
momentum_long = 252 #12 month
momentum_short = 20 #1 month
training_period = 1000 #days
holding_period = list(range(10,70,10))
rf = 1

symbols = ["SPY", "EFA", "BND", "VNQ", "GSG"] ##ETFs across different asset classes


dict_ETF_data = {}
for symbol in symbols:
   dict_ETF_data[symbol] = yf.Ticker(symbol).history(time_period)['Close']
   
df = pd.DataFrame(dict_ETF_data).dropna()
print(df)

def moving_average(x, N):
    return pd.Series(x).rolling(window=N).mean().iloc[N-1:].values


def mom_diff(symbols, strategy_period, momentum_long, momentum_short):
    d_momentum_vals = {}
    
    for symbol in symbols:
        d_momentum_vals[symbol] = moving_average(dict_ETF_data[symbol].iloc[0:strategy_period], momentum_short)[-1] - moving_average(dict_ETF_data[symbol].iloc[0:strategy_period], momentum_long)[-1]
    
    return d_momentum_vals


training_period = round(0.8 * df.shape[0])
###choose the holding period that results in the greatest SR
ret = {}
for h_p in holding_period:
    ret_h_p = []
    for i in range(momentum_long, training_period-momentum_long, h_p):
        returns = 0
        d_momentum_vals = mom_diff(symbols, i ,momentum_long, momentum_short)
        req_ETFs = sorted(d_momentum_vals, key=(lambda key:d_momentum_vals[key]), reverse=True)[:2]
        returns = 0.5 * (dict_ETF_data[req_ETFs[0]].iloc[i+1+h_p]/dict_ETF_data[req_ETFs[0]].iloc[i+1] - 1) \
        + 0.5 * (dict_ETF_data[req_ETFs[1]].iloc[i+1+h_p]/dict_ETF_data[req_ETFs[1]].iloc[i+1] - 1)
        ret_h_p.append(returns * 100)
    
    ret[str(h_p)] = ret_h_p


h_p_highest = sorted(ret, key=(lambda key:statistics.mean(ret[key])), reverse=True)[0]

s_r = (statistics.mean(ret[str(h_p_highest)]) - rf)/statistics.stdev(ret[str(h_p_highest)])

##testing performance in testing period
ret_test = []
for i in range(training_period-momentum_long, df.shape[0] - momentum_long, int(h_p_highest)):
    returns = 0
    d_momentum_vals = mom_diff(symbols, i ,momentum_long, momentum_short)
    req_ETFs = sorted(d_momentum_vals, key=(lambda key:d_momentum_vals[key]), reverse=True)[:2]
    returns = 0.5 * (dict_ETF_data[req_ETFs[0]].iloc[i+1+h_p]/dict_ETF_data[req_ETFs[0]].iloc[i+1] - 1) \
    + 0.5 * (dict_ETF_data[req_ETFs[1]].iloc[i+1+h_p]/dict_ETF_data[req_ETFs[1]].iloc[i+1] - 1)
    ret_test.append(returns * 100)

s_r_test = (statistics.mean(ret_test) - rf)/statistics.stdev(ret_test)
##looks good

###What should I get into now:
d_momentum_vals_now = mom_diff(symbols, df.shape[0], momentum_long, momentum_short)
req_ETFs_now = sorted(d_momentum_vals, key=(lambda key:d_momentum_vals_now[key]), reverse=True)[:2]
print(req_ETFs_now)
