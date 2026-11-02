import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
"""Demand-planning forecast accuracy study on public store-item sales (913,000 daily rows, 10 stores x 50 items, 2013-2017).
Run: python analysis.py   (needs pandas, numpy, statsmodels)"""
import json, numpy as np, pandas as pd
from forecast_lib import *

d = pd.read_csv('data/train.csv', parse_dates=['date'])
d['m'] = d.date.dt.to_period('M')
piv = d.groupby(['store', 'item', 'm']).sales.sum().unstack('m')
keys = list(piv.index); M = piv.values.astype(float); months = list(piv.columns)
assert M.shape == (500, 60) and not np.isnan(M).any()
T = 12                                    # test year = 2017
train, test = M[:, :-T], M[:, -T:]
out = {'rows': int(len(d)), 'series': int(M.shape[0]), 'months': len(months), 'train_months': M.shape[1] - T, 'test_months': T}

# 1) fixed origin: forecast all 12 months of 2017 from data up to Dec 2016 (an annual planning cycle)
methods = {'Naive (last month)': naive, 'Moving average (3 months)': moving_avg, 'Seasonal naive (same month last year)': seasonal_naive,
           'Seasonal naive x growth': seasonal_naive_growth, 'Holt-Winters (damped trend, seasonal)': holt_winters}
fc = {k: f(train, T) for k, f in methods.items()}
def levels(F, A):
    sku_m = (wape(A, F), bias(A, F))
    item = lambda X: X.reshape(10, 50, -1).sum(axis=0)          # sum over stores: item level (sorted store, item keys)
    store = lambda X: X.reshape(10, 50, -1).sum(axis=1)         # sum over items: store level
    return dict(sku_market=sku_m[0], item=wape(item(A), item(F)), store=wape(store(A), store(F)), total=wape(A.sum(0), F.sum(0)), bias=sku_m[1])
assert all(k[0] <= k[1] for k in zip(keys[:-1], keys[1:])) and keys[0] == (1, 1) and keys[49] == (1, 50) and keys[50] == (2, 1)
out['fixed_origin'] = {k: {kk: round(v, 4) for kk, v in levels(F, test).items()} for k, F in fc.items()}

# 2) one-month-ahead rolling forecasts for 2017 (a monthly forecasting cycle) for the four simple methods
simple = {k: v for k, v in methods.items() if 'Holt' not in k}
roll = {k: np.zeros_like(test) for k in simple}
for t in range(T):
    hist = M[:, :M.shape[1] - T + t]
    for k, f in simple.items(): roll[k][:, t] = f(hist, 1)[:, 0]
out['rolling_1m'] = {k: {kk: round(v, 4) for kk, v in levels(F, test).items()} for k, F in roll.items()}

# 3) monthly KPI review for the best fixed-origin method: where does the error come from?
best = min(out['fixed_origin'], key=lambda k: out['fixed_origin'][k]['sku_market']); out['best_fixed_origin'] = best
F = fc[best]
mon = [dict(month=str(months[-T + t]), actual=int(test[:, t].sum()), forecast=int(round(F[:, t].sum())),
            wape=round(wape(test[:, t], F[:, t]), 4), bias=round(bias(test[:, t], F[:, t]), 4)) for t in range(T)]
out['monthly_kpi'] = mon
err = np.abs(test - F).sum(axis=1)                                   # absolute error per series
share = np.sort(err)[::-1].cumsum() / err.sum()
out['error_concentration'] = {'top_10pct_series_share_of_error': round(float(share[49]), 3), 'top_20pct': round(float(share[99]), 3)}
vol_share = np.sort(test.sum(axis=1))[::-1].cumsum() / test.sum()
out['volume_concentration'] = {'top_10pct_series_share_of_volume': round(float(vol_share[49]), 3)}
by_store = {int(s): round(wape(test[(np.array([k[0] for k in keys]) == s)], F[(np.array([k[0] for k in keys]) == s)]), 4) for s in range(1, 11)}
by_item_wape = np.array([wape(test[[i for i, k in enumerate(keys) if k[1] == it]], F[[i for i, k in enumerate(keys) if k[1] == it]]) for it in range(1, 51)])
out['wape_by_store'] = by_store
out['worst_items'] = [dict(item=int(i + 1), wape=round(float(by_item_wape[i]), 4)) for i in np.argsort(-by_item_wape)[:5]]
out['best_items'] = [dict(item=int(i + 1), wape=round(float(by_item_wape[i]), 4)) for i in np.argsort(by_item_wape)[:3]]
# forecast value added vs the naive baseline, one-month rolling
b = out['rolling_1m']; nv = b['Naive (last month)']['sku_market']
out['fva_vs_naive_rolling'] = {k: round(nv - v['sku_market'], 4) for k, v in b.items()}
# is the miss in a particular direction? average bias by quarter for the best method
out['bias_by_quarter'] = {f'Q{q+1}': round(bias(test[:, 3*q:3*q+3], F[:, 3*q:3*q+3]), 4) for q in range(4)}
yr = {int(y): int(M[:, 12*i:12*i+12].sum()) for i, y in enumerate(range(2013, 2018))}
out['yearly_units'] = yr
out['yoy_growth'] = {f'{y}': round(yr[y] / yr[y-1] - 1, 4) for y in range(2014, 2018)}
out['forecast_2017_growth_implied'] = {k: round(float(F_.sum()) / yr[2016] - 1, 4) for k, F_ in fc.items()}
json.dump(out, open('outputs/results.json', 'w'), indent=1)
np.save('outputs/test_actual.npy', test); np.save('outputs/best_forecast.npy', F)
print(json.dumps({k: out[k] for k in ['fixed_origin', 'rolling_1m', 'best_fixed_origin', 'error_concentration', 'volume_concentration', 'wape_by_store', 'worst_items', 'best_items', 'fva_vs_naive_rolling', 'bias_by_quarter']}, indent=1))
print(json.dumps(out['monthly_kpi'], indent=0))
