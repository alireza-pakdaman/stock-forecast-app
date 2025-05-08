from prophet import Prophet
import pandas as pd

class ProphetForecaster:
    def __init__(self, daily_seasonality=True):
        self.model = Prophet(daily_seasonality=daily_seasonality)
        
    def fit(self, df: pd.DataFrame):
        # Make sure the df has a 'close' column
        if 'close' not in df.columns:
            raise ValueError("DataFrame must have a 'close' column")
            
        # Reset index to convert the date index to a column, and rename for Prophet
        df_ = df[['close']].reset_index().rename(columns={'date':'ds','close':'y'})
        
        # Ensure y is numeric
        df_['y'] = pd.to_numeric(df_['y'])
        
        self.model.fit(df_)
        
    def predict(self, steps: int = 30) -> pd.DataFrame:
        future = self.model.make_future_dataframe(periods=steps)
        forecast = self.model.predict(future)
        # Return the forecast DataFrame with ds as index, keeping all columns
        return forecast.set_index('ds')[-steps:]
