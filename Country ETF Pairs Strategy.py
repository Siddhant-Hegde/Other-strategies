##Based on Pairs Trading on International ETFs SSRN Paper
##https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1958546
##Added in cointegration check for pairs 

import pandas as pd
import numpy as np 
import itertools
import yfinance as yf
import statistics
from tests import ADF
from tests import get_johansen
from functools import reduce

time_period = '200mo'
formation_period = 180##days
trading_period = 20 ##days
holding_period = 20
rf = 0.5
c_in = 1.75 ##threshold value
c_out = 1.0
stop_loss = -7

###retrieve ETF data from Yahoo
def yahoo_data():

    df = pd.read_csv('C:/Git stuff/Other-strategies/Other-strategies/Country_ETFs.csv', encoding= 'unicode_escape')

    l_ETFs = list(df['ETF or ETN'].apply(lambda x: x.split()[-1]))
    d_ETFs = {}
    l_ETFs_pairs = list(itertools.combinations(l_ETFs, 2))
    
    for i in l_ETFs:
        d_ETFs[i] = yf.Ticker(i).history(time_period)['Close']
            
    df_ETFs = pd.DataFrame(d_ETFs).dropna()
    
    return l_ETFs, df_ETFs, l_ETFs_pairs

###Normalized prices of the ETF's, as per paper 
def normalized_prices(l_ETFs, df_ETFs):
    
    d_appreciated = {}
    
    for i in l_ETFs:
        d_appreciated[str(i)] = (1 + (df_ETFs[i] / df_ETFs[i].shift(1) - 1))
    
    df_appreciated = pd.DataFrame(d_appreciated).dropna()
    d_normalized = {}
    
    for i in l_ETFs:
        d_normalized[str(i)] = df_appreciated[i].cumprod()
            
    df_normalized = pd.DataFrame(d_normalized).dropna()
    
    return df_normalized

###calculate distances between two ETF's
def distance(index_A, index_B):
    return 1/index_A.shape[0]  * sum(abs(index_A - index_B))

###Obtain cointegrated pairs
def get_coint_pairs(l_ETFs_pairs, df_ETFs, strategy_run_day):
    
    coint_pairs = []    
    
    ###Check if pairs are cointegrated
    for i in l_ETFs_pairs:
        stock_1 = df_ETFs[i[0]].iloc[strategy_run_day:strategy_run_day+formation_period]
        stock_2 = df_ETFs[i[1]].iloc[strategy_run_day:strategy_run_day+formation_period]
        if ADF(stock_1) and ADF(stock_2):
            joint_pairs_series = pd.merge(stock_1, stock_2, left_index=True, right_index=True)
            if get_johansen(joint_pairs_series, 0):
                if get_johansen(joint_pairs_series, 0)[0] != 0:
                    coint_pairs.append(i)
    
    return coint_pairs

###Obtain pairs that are coinegrated and have the biggest distances
def get_final_pairs(coint_pairs, df_normalized, strategy_run_day):
    
    d_distances = {}
    
    for i in coint_pairs:
        d_distances[i] = distance(df_normalized[i[0]], df_normalized[i[1]])
        
    final_pairs = sorted(d_distances, key=(lambda key:d_distances[key]), reverse = True)[:5] ##5 pairs with the biggest distances 
    
    return final_pairs

##calculating the returns from this strategy
def returns_from_strategy(trading_period, formation_period):
    
    l_ETFs, df_ETFs, l_ETFs_pairs = yahoo_data() 
    
    df_normalized = normalized_prices(l_ETFs, df_ETFs)
    training_period = round(0.8 * df_normalized.shape[0])
    ret_formation_period = []
    
    #df_ETFs = yahoo_data()[1]
    df_ETFs = pd.read_csv('C:/Git stuff/Other-strategies/Other-strategies/df_ETFs.csv')
    
    ###Obtain pairs for each formation period up to the training period 
    strategy_run_day = 0
    while strategy_run_day < training_period:
    
        coint_pairs = get_coint_pairs(l_ETFs_pairs, df_ETFs, strategy_run_day)
        final_pairs = get_final_pairs(coint_pairs, df_normalized.iloc[strategy_run_day:strategy_run_day+formation_period], formation_period)
        ret = []
    
        for pair in final_pairs:
            daily_returns = []
            cumulative_returns = 0
            flag = 0
            no_of_days_in_trade = 0
            d_distance = distance(df_normalized[pair[0]].iloc[strategy_run_day:strategy_run_day+formation_period], df_normalized[pair[1]].iloc[strategy_run_day:strategy_run_day+formation_period])
            
            for t in range(trading_period):
                ###check if trade can be entered based on threshold in and if the trade hasnt been entered
                ###into for the current trading period
                if c_in * d_distance < abs(df_normalized[pair[0]].iloc[strategy_run_day+formation_period+t] - df_normalized[pair[1]].iloc[strategy_run_day+formation_period+t]) and flag == 0:
                    
                    for h_p in range(holding_period):   

                        ###should one remain in the trade based on threshold out
                        if c_out * d_distance < abs(df_normalized[pair[0]].iloc[strategy_run_day + formation_period+t+h_p] - df_normalized[pair[1]].iloc[strategy_run_day + formation_period+t+h_p]) and cumulative_returns > stop_loss:
                            
                            flag = 1 ###entered trade
                            
                            no_of_days_in_trade += 1 ###determine how long one should remain in the trade 
                            
                            num = df_ETFs[pair[0]].iloc[strategy_run_day +formation_period+t+h_p]
                            denom = df_ETFs[pair[0]].iloc[strategy_run_day +formation_period+t+h_p-1]
                            num_1 = df_ETFs[pair[1]].iloc[strategy_run_day +formation_period+t+h_p]
                            denom_1 = df_ETFs[pair[1]].iloc[strategy_run_day +formation_period+t+h_p-1]
                            
                            daily_returns.append((-1 * ((num/denom)-1) + 1 * ((num_1/denom_1)-1)) + 1)

                            cumulative_returns = 100*((reduce(lambda x, y: x*y,daily_returns))-1)
                            
                        else:
                            break

            
            if cumulative_returns != 0:
                
                ret.append(cumulative_returns)
        
        strategy_run_day = strategy_run_day + formation_period + trading_period + holding_period
        
        ret_formation_period.append(ret)
        
    return ret_formation_period

ret = returns_from_strategy(trading_period, formation_period)
flat_ret = [item for sublist in ret for item in sublist]

##calculating the sharpe
s_r = (statistics.mean(flat_ret) - rf)/statistics.stdev(flat_ret)

###Now, to choose the pairs to get into going forward
l_ETFs, df_ETFs, l_ETFs_pairs = yahoo_data()
df_normalized = normalized_prices(l_ETFs, df_ETFs)
time_start_pair_formation = df_normalized.shape[0] - formation_period - trading_period - holding_period
coint_pairs_use = get_coint_pairs(l_ETFs_pairs, df_ETFs, time_start_pair_formation)
final_pairs_use = get_final_pairs(coint_pairs_use, df_normalized.iloc[time_start_pair_formation:time_start_pair_formation+formation_period], formation_period)

