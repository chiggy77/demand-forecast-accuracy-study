# Demand forecast accuracy study

Monthly forecasts for 500 store-item series, compared with WAPE and bias, with a root-cause review.

## Data
`data/train.csv`: public Store Item Demand Forecasting Challenge data (913,000 daily rows, 10 stores x 50 items, 2013-2017), from the GitHub repository jgonzalezab/Store-Item-Demand-Forecasting (Data/train.csv). Not included in the zip: download it into `data/`. The data is very smooth and may be synthetic.

## Reproduce
```
pip install -r requirements.txt
python analysis.py        # writes outputs/results.json (about 30 seconds)
python charts.py
python make_summary.py    # needs python-docx
python tests/test_forecast.py
```

## Method
- Monthly sums per store x item. Train 2013-2016, forecast all 12 months of 2017 (fixed origin). Also one-month-ahead rolling forecasts for the four simple methods.
- Methods: naive, 3-month moving average, seasonal naive, seasonal naive x growth, Holt-Winters (damped trend, multiplicative seasonality).
- WAPE = sum|A-F| / sum A. Bias = sum(F-A) / sum A (positive = over-forecast). Forecast value added = error of the naive forecast minus error of the method.

## Design choices and limitations

- **Why WAPE and not MAPE?** MAPE explodes on low or zero volumes and gives small items too much weight. WAPE weights errors by volume.
- **Why did seasonal naive x growth over-forecast?** It extrapolated 2016's +8.6% growth, but 2017 grew only +3.6%.
- **Why is the moving average worse than naive in the rolling test?** It lags the seasonal swings.
- **What this study does not test:** promotions, new product launches, product life cycles, inventory and service levels.
