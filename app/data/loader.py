import yfinance as yf
from functools import lru_cache
import pandas as pd
import logging
import time
import json
import requests
from urllib.error import URLError, HTTPError
import os
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fallback data cache directory
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_fallback_data(ticker):
    """
    Get fallback data from cache or create sample data if no cache exists
    """
    cache_file = os.path.join(CACHE_DIR, f"{ticker.lower()}_fallback.csv")
    
    if os.path.exists(cache_file):
        logger.info(f"Loading fallback data for {ticker} from cache")
        return pd.read_csv(cache_file, index_col='date', parse_dates=['date'])
    
    # Create synthetic data if no cache exists
    logger.info(f"Creating synthetic fallback data for {ticker}")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*3)  # 3 years of data
    
    # Create date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
    
    # Create synthetic price data (random walk with upward trend)
    import numpy as np
    np.random.seed(42)  # For reproducibility
    
    initial_price = 100.0
    returns = np.random.normal(0.0005, 0.015, size=len(date_range))  # Mean positive return
    prices = initial_price * (1 + returns).cumprod()
    
    # Create a DataFrame
    df = pd.DataFrame({
        'close': prices,
        'open': prices * np.random.uniform(0.98, 1.02, size=len(date_range)),
        'high': prices * np.random.uniform(1.01, 1.05, size=len(date_range)),
        'low': prices * np.random.uniform(0.95, 0.99, size=len(date_range)),
        'volume': np.random.randint(100000, 10000000, size=len(date_range))
    }, index=date_range)
    
    df.index.name = 'date'
    
    # Save to cache
    df.to_csv(cache_file)
    
    return df

def try_alternative_sources(ticker, start):
    """
    Try alternative data sources when Yahoo Finance fails
    """
    logger.info(f"Trying alternative data source for {ticker}")
    
    # Try Alpha Vantage API if key is available
    alpha_vantage_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if alpha_vantage_key:
        try:
            logger.info(f"Trying Alpha Vantage API for {ticker}")
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={alpha_vantage_key}"
            r = requests.get(url)
            data = r.json()
            
            if "Time Series (Daily)" in data:
                logger.info(f"Successfully fetched {ticker} data from Alpha Vantage")
                time_series = data["Time Series (Daily)"]
                df = pd.DataFrame.from_dict(time_series, orient='index')
                df.index = pd.DatetimeIndex(df.index)
                df.columns = [col.split('. ')[1].lower() for col in df.columns]
                df.rename(columns={
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume'
                }, inplace=True)
                df = df.astype(float)
                df = df[df.index >= start]
                df.index.name = "date"
                return df
        except Exception as e:
            logger.warning(f"Alpha Vantage API failed for {ticker}: {str(e)}")
    
    # Return fallback data
    return get_fallback_data(ticker)

def process_yfinance_data(df, ticker):
    """
    Process the data from yfinance into a consistent format
    """
    logger.info(f"Processing yfinance data for {ticker}")
    
    # Check if the DataFrame is empty
    if df.empty:
        logger.error(f"Empty DataFrame for {ticker}")
        return df
    
    # Log column structure to help debug
    logger.info(f"Original columns for {ticker}: {df.columns}")
    
    # Handle multi-level column format 
    if isinstance(df.columns, pd.MultiIndex):
        logger.info(f"Multi-level columns detected for {ticker}")
        
        # Look for specific column names regardless of level
        result_df = pd.DataFrame(index=df.index)
        
        # Find all the columns we need
        for col_name in ['Close', 'Open', 'High', 'Low', 'Volume']:
            # Find any column containing this name
            matching_cols = [col for col in df.columns if col_name in str(col)]
            
            if matching_cols:
                # Use the first matching column
                result_df[col_name.lower()] = df[matching_cols[0]]
                logger.info(f"Found and mapped {col_name} column for {ticker}")
            else:
                logger.warning(f"Could not find {col_name} column for {ticker}")
        
        # Ensure we have at least close prices
        if 'close' not in result_df.columns and len(matching_cols) > 0:
            # If we don't have a 'Close' column but have matched others, 
            # use the first numeric column as close
            numeric_cols = [col for col in result_df.columns 
                           if pd.api.types.is_numeric_dtype(result_df[col])]
            
            if numeric_cols:
                result_df['close'] = result_df[numeric_cols[0]]
                logger.info(f"Using {numeric_cols[0]} as close price for {ticker}")
    else:
        # Handle regular column format
        result_df = df.copy()
        # Rename columns to lowercase
        result_df.columns = [col.lower() for col in result_df.columns]
        logger.info(f"Standard columns processed for {ticker}: {result_df.columns}")
    
    # Make sure index name is 'date'
    result_df.index.name = 'date'
    
    # Drop any NaN values
    result_df.dropna(inplace=True)
    
    logger.info(f"Final columns for {ticker}: {result_df.columns}")
    return result_df

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
            
            # Try to use Ticker object first which might handle API changes better
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=start, interval=interval, auto_adjust=True)
            
            if df.empty:
                # Fallback to download method if Ticker.history() returns empty
                logger.warning(f"Empty result from Ticker.history() for {ticker}, trying download method")
                df = yf.download(ticker, start=start, interval=interval, auto_adjust=True, progress=False)
            
            if df.empty:
                logger.error(f"No data returned for {ticker}")
                raise ValueError(f"No data for {ticker!r}")
            
            # Process the data into a consistent format
            processed_df = process_yfinance_data(df, ticker)
            
            if processed_df.empty:
                logger.error(f"Processing resulted in empty DataFrame for {ticker}")
                raise ValueError(f"Failed to process data for {ticker}")
                
            # Make sure we have the minimum required columns
            if 'close' not in processed_df.columns:
                logger.error(f"No 'close' column after processing for {ticker}")
                raise ValueError(f"Missing required 'close' column for {ticker}")
            
            logger.info(f"Successfully fetched and processed {len(processed_df)} records for {ticker}")
            return processed_df
            
        except (URLError, HTTPError) as e:
            logger.warning(f"Network error fetching {ticker}: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Failed to fetch data from Yahoo Finance after {max_retries} attempts")
                return try_alternative_sources(ticker, start)
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {ticker}: {str(e)}")
            return try_alternative_sources(ticker, start)
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            if "No timezone found" in str(e) or "delisted" in str(e):
                logger.warning(f"Symbol {ticker} may be delisted or invalid, using fallback data")
                return try_alternative_sources(ticker, start)
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"All attempts failed, using fallback data")
                return try_alternative_sources(ticker, start)
