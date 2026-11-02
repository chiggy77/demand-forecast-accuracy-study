import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
R = json.load(open('outputs/results.json'))
BLUE, ORANGE, GREY = '#2a78d6', '#eb6834', '#9a998f'
plt.rcParams.update({'font.family': 'DejaVu Sans'})
def clean(ax):
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
# 1) accuracy by method (12-month planning cycle)
fo = R['fixed_origin']; names = list(fo); order = sorted(names, key=lambda k: -fo[k]['sku_market'])
fig, ax = plt.subplots(figsize=(8, 4.4)); y = np.arange(len(order))
ax.barh(y, [fo[k]['sku_market'] * 100 for k in order], color=[BLUE if k == R['best_fixed_origin'] else GREY for k in order], height=.6)
for i, k in enumerate(order): ax.text(fo[k]['sku_market'] * 100 + .5, i, f"{fo[k]['sku_market']:.1%}  (bias {fo[k]['bias']:+.1%})", va='center', fontsize=9)
ax.set_yticks(y); ax.set_yticklabels(order, fontsize=9); ax.set_xlim(0, 38); ax.set_xlabel('WAPE at monthly store x item level (lower is better)')
ax.set_title('Seasonality matters most: 4% vs 19-28% error', loc='left', fontweight='bold', fontsize=11); clean(ax)
fig.tight_layout(); fig.savefig('outputs/chart_method_accuracy.png', dpi=180); plt.close()
# 2) 2017 actual vs forecast (best method)
m = R['monthly_kpi']; x = np.arange(len(m)); fig, ax = plt.subplots(figsize=(8, 4.2))
ax.plot(x, [r['actual'] / 1e3 for r in m], color=BLUE, lw=2.2, marker='o', label='Actual')
ax.plot(x, [r['forecast'] / 1e3 for r in m], color=ORANGE, lw=2, marker='s', ls='--', label=R['best_fixed_origin'].split(' (')[0] + ' forecast')
ax.set_xticks(x); ax.set_xticklabels([r['month'][5:] for r in m]); ax.set_xlabel('2017 month'); ax.set_ylabel('Units (thousands)')
for i, r in enumerate(m):
    if i in (0, 4, 11): ax.annotate(f"bias {r['bias']:+.1%}", (i, r['forecast'] / 1e3), textcoords='offset points', xytext=(0, 9), ha='center', fontsize=8)
ax.legend(frameon=False); ax.set_title('Holt-Winters over-forecast most of 2017 (bias shown for 3 months)', loc='left', fontweight='bold', fontsize=11); clean(ax)
fig.tight_layout(); fig.savefig('outputs/chart_actual_vs_forecast_2017.png', dpi=180); plt.close()
