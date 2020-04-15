import pandas as pd
import numpy as np 
import itertools
import yfinance as yf
import statistics

time_period = '160mo'
formation_period = 120##days

df = pd.read_csv('C:/Git stuff/Other-strategies/Country_ETFs.csv', encoding= 'unicode_escape')
req_df = pd.DataFrame()    

l_ETFs = list(df['ETF or ETN'].apply(lambda x: x.split()[-1]))
d_ETFs = {}

for i in l_ETFs:
    d_ETFs[i] = yf.Ticker(i).history(time_period)['Close']

df_ETFs = pd.DataFrame(d_ETFs).dropna()

def distance(index_A, index_B):
    return 1/formation_period  * sum(abs(index_A - index_B))

d_distances = {}
d_ETFs = {}

l_ETFs_pairs = list(itertools.combinations(l_ETFs, 2))


for i in l_ETFs_pairs:
    d_distances[i] = distance(df_ETFs[i[0]], df_ETFs[i[1]])

print(d_distances)