import pandas as pd
import numpy as np 
import itertools
import yfinance as yf
import statistics
from tests import ADF
from tests import get_johansen

time_period = '160mo'
formation_period = 120##days

df = pd.read_csv('C:/Git stuff/Other-strategies/Country_ETFs.csv', encoding= 'unicode_escape')

l_ETFs = list(df['ETF or ETN'].apply(lambda x: x.split()[-1]))
d_ETFs = {}

for i in l_ETFs:
    d_ETFs[i] = yf.Ticker(i).history(time_period)['Close']
        

df_ETFs = pd.DataFrame(d_ETFs).dropna()
d_appreciated = {}

for i in l_ETFs:
    d_appreciated[str(i)] = (1 + (df_ETFs[i] / df_ETFs[i].shift(1) - 1))

df_appreciated = pd.DataFrame(d_appreciated).dropna()
d_normalized = {}

for i in l_ETFs:
    for t in range(formation_period):
        d_normalized[str(i)] = df_appreciated[i].iloc[:t].cumprod()
        
df_normalized = pd.DataFrame(d_normalized).dropna()
print(df_normalized)

def distance(index_A, index_B):
    return 1/formation_period  * sum(abs(index_A - index_B))

d_distances = {}
d_ETFs = {}

l_ETFs_pairs = list(itertools.combinations(l_ETFs, 2))

coint_pairs = []

###Check if pairs are cointegrated
for i in l_ETFs_pairs:
    if ADF(df_ETFs[i[0]]) and ADF(df_ETFs[i[1]]):
        joint_pairs_series = pd.merge(df_ETFs[i[0]], df_ETFs[i[1]], left_index=True, right_index=True)
        if get_johansen(joint_pairs_series, 0):
            if get_johansen(joint_pairs_series, 0)[0] != 0:
                coint_pairs.append(i)
    
for i in coint_pairs:
    d_distances[i] = distance(df_normalized[i[0]], df_normalized[i[1]])

final_pairs = sorted(d_distances, key=(lambda key:d_distances[key]))[:5] ##5 pairs with the smallest distances 
