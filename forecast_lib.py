"""Forecast methods and accuracy metrics for monthly demand planning (pure functions, tested)."""
import numpy as np


def wape(actual, fc):
    """Weighted absolute percentage error: sum|A-F| / sum A (lower is better)."""
    a = np.asarray(actual, float); f = np.asarray(fc, float)
    return float(np.abs(a - f).sum() / a.sum())


def bias(actual, fc):
    """Forecast bias: sum(F-A) / sum A. Positive = over-forecast."""
    a = np.asarray(actual, float); f = np.asarray(fc, float)
    return float((f - a).sum() / a.sum())


def naive(hist, h):
    """Repeat the last observed month. hist: (series, months)."""
    return np.repeat(hist[:, -1:], h, axis=1)


def moving_avg(hist, h, k=3):
    return np.repeat(hist[:, -k:].mean(axis=1, keepdims=True), h, axis=1)


def seasonal_naive(hist, h, season=12):
    """Same month last year."""
    reps = int(np.ceil(h / season))
    base = hist[:, -season:]
    return np.tile(base, (1, reps))[:, :h]


def seasonal_naive_growth(hist, h, season=12):
    """Same month last year, scaled by the last-12-month vs previous-12-month growth of each series."""
    last = hist[:, -season:].sum(axis=1, keepdims=True)
    prev = hist[:, -2 * season:-season].sum(axis=1, keepdims=True)
    g = np.where(prev > 0, last / np.maximum(prev, 1e-9), 1.0)
    return seasonal_naive(hist, h, season) * g


def holt_winters(hist, h, season=12):
    """Additive-trend, multiplicative-seasonality exponential smoothing per series (statsmodels)."""
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    import warnings
    out = np.zeros((hist.shape[0], h))
    for i, y in enumerate(hist):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                m = ExponentialSmoothing(y, trend='add', damped_trend=True, seasonal='mul', seasonal_periods=season,
                                         initialization_method='estimated').fit()
                out[i] = m.forecast(h)
        except Exception:
            out[i] = seasonal_naive(y[None, :], h)[0]
    return out
