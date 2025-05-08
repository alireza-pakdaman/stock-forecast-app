from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
class ARIMAForecaster:
    def __init__(self, order=(5,1,0)):
        self.order = order
        self.model = None
    def fit(self, series: pd.Series):
        self.model = ARIMA(series, order=self.order).fit()
    def predict(self, steps: int = 30) -> pd.Series:
        if self.model is None:
            raise RuntimeError("Call fit() first.")
        return self.model.forecast(steps=steps)
