import yfinance as yf
from functools import lru_cache
import pandas as pd

@lru_cache(maxsize=128)
def fetch_price_history(ticker: str, start: str = "2000-01-01", interval: str = "1d") -> pd.DataFrame:
    df = yf.download(ticker, start=start, interval=interval, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data for {ticker!r}")
    
    # Handle multi-level column format if present
    if isinstance(df.columns, pd.MultiIndex):
        # Get the Close price column - in the new format it's ('Price', 'Close', 'AAPL')
        close_col = [col for col in df.columns if 'Close' in col]
        if close_col:
            # Create a new DataFrame with just the close price
            result_df = pd.DataFrame({'close': df[close_col[0]]})
            result_df.index.name = "date"
            return result_df
    
    # If not a multi-level column format, proceed with the old approach
    df.dropna(inplace=True)
    df.rename(columns=str.lower, inplace=True)
    df.index.name = "date"
    return df
