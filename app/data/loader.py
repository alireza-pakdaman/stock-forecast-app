import yfinance as yf
from functools import lru_cache
import pandas as pd
import logging
import time
from urllib.error import URLError, HTTPError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@lru_cache(maxsize=128)
def fetch_price_history(ticker: str, start: str = "2000-01-01", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch stock price history with retry mechanism and improved error handling
    """
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching data for {ticker} (attempt {attempt+1}/{max_retries})")
            df = yf.download(ticker, start=start, interval=interval, auto_adjust=True, progress=False)
            
            if df.empty:
                logger.error(f"No data returned for {ticker}")
                raise ValueError(f"No data for {ticker!r}")
            
            # Handle multi-level column format if present
            if isinstance(df.columns, pd.MultiIndex):
                # Get the Close price column - in the new format it's ('Price', 'Close', 'AAPL')
                close_col = [col for col in df.columns if 'Close' in col]
                if close_col:
                    # Create a new DataFrame with just the close price
                    result_df = pd.DataFrame({'close': df[close_col[0]]})
                    result_df.index.name = "date"
                    logger.info(f"Successfully fetched {len(result_df)} records for {ticker}")
                    return result_df
            
            # If not a multi-level column format, proceed with the old approach
            df.dropna(inplace=True)
            df.rename(columns=str.lower, inplace=True)
            df.index.name = "date"
            logger.info(f"Successfully fetched {len(df)} records for {ticker}")
            return df
            
        except (URLError, HTTPError) as e:
            logger.warning(f"Network error fetching {ticker}: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Failed to fetch data after {max_retries} attempts")
                raise
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            raise
