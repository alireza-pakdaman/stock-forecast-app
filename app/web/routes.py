from flask import Blueprint, render_template, request, send_file, flash, redirect
from ..data import fetch_price_history
from ..data.indicators import sma, ema, rsi, macd
from ..models import ProphetForecaster
from ..visualize import price_chart, overlay_forecast
from ..reports import build_pdf
import tempfile, io, pandas as pd
import numpy as np
from datetime import datetime

bp = Blueprint('web', __name__)

def calculate_indicators(df):
    """Calculate all technical indicators and statistics for a price dataframe"""
    # Basic stats
    latest_close = df['close'].iloc[-1]
    prev_close = df['close'].iloc[-2]
    price_change = latest_close - prev_close
    price_change_pct = (price_change / prev_close) * 100
    
    # Moving averages
    df['sma_7'] = sma(df['close'], 7)
    df['sma_20'] = sma(df['close'], 20)
    df['sma_50'] = sma(df['close'], 50)
    df['ema_12'] = ema(df['close'], 12)
    df['ema_26'] = ema(df['close'], 26)
    
    # RSI
    df['rsi_14'] = rsi(df['close'], 14)
    
    # MACD
    macd_df = macd(df['close'])
    df['macd'] = macd_df['macd']
    df['macd_signal'] = macd_df['signal']
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # Bollinger Bands
    df['bb_middle'] = df['sma_20']
    df['bb_std'] = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
    df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    
    # Check if we have high/low data for Stochastic Oscillator
    n = 14
    if 'high' in df.columns and 'low' in df.columns:
        # Calculate Stochastic Oscillator with high/low data
        df['stoch_k'] = 100 * ((df['close'] - df['low'].rolling(n).min()) / 
                            (df['high'].rolling(n).max() - df['low'].rolling(n).min()))
        df['stoch_d'] = df['stoch_k'].rolling(3).mean()
        stoch_value = df['stoch_k'].iloc[-1]
        
        # Calculate ATR with high/low data
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift())
        tr3 = abs(df['low'] - df['close'].shift())
        df['tr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr_14'] = df['tr'].rolling(14).mean()
        atr_value = df['atr_14'].iloc[-1]
    else:
        # Alternative calculation for Stochastic using only close prices
        # This is less accurate but still provides a momentum indicator
        df['close_min'] = df['close'].rolling(n).min()
        df['close_max'] = df['close'].rolling(n).max()
        df['stoch_k'] = 100 * ((df['close'] - df['close_min']) / 
                            (df['close_max'] - df['close_min']).replace(0, 1))  # Avoid division by zero
        df['stoch_d'] = df['stoch_k'].rolling(3).mean()
        stoch_value = df['stoch_k'].iloc[-1]
        
        # Simple volatility measure as ATR alternative
        df['daily_change'] = df['close'].diff().abs()
        df['atr_14'] = df['daily_change'].rolling(14).mean()
        atr_value = df['atr_14'].iloc[-1]
    
    # Volume analysis - check if volume data is available
    if 'volume' in df.columns:
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        volume_value = df['volume'].iloc[-1]
        volume_change_pct = ((volume_value / df['volume_sma_20'].iloc[-1]) - 1) * 100
    else:
        # No volume data available
        volume_value = 0
        volume_change_pct = 0
    
    # Volatility
    df['returns'] = df['close'].pct_change()
    volatility_30d = df['returns'].rolling(30).std() * np.sqrt(252) * 100
    
    # Technical signals
    sma_7_signal = "Buy" if df['close'].iloc[-1] > df['sma_7'].iloc[-1] else "Sell"
    sma_20_signal = "Buy" if df['close'].iloc[-1] > df['sma_20'].iloc[-1] else "Sell"
    sma_50_signal = "Buy" if df['close'].iloc[-1] > df['sma_50'].iloc[-1] else "Sell"
    ema_12_signal = "Buy" if df['close'].iloc[-1] > df['ema_12'].iloc[-1] else "Sell"
    ema_26_signal = "Buy" if df['close'].iloc[-1] > df['ema_26'].iloc[-1] else "Sell"
    
    macd_signal = "Buy" if df['macd_hist'].iloc[-1] > 0 else "Sell"
    rsi_val = df['rsi_14'].iloc[-1]
    rsi_signal = "Buy" if rsi_val < 30 else "Sell" if rsi_val > 70 else "Neutral"
    stoch_signal = "Buy" if (df['stoch_k'].iloc[-1] < 20 and df['stoch_d'].iloc[-1] < 20) else \
                   "Sell" if (df['stoch_k'].iloc[-1] > 80 and df['stoch_d'].iloc[-1] > 80) else "Neutral"
    
    # Bollinger Bands signal
    bb_signal = "Buy" if df['close'].iloc[-1] < df['bb_lower'].iloc[-1] else \
                "Sell" if df['close'].iloc[-1] > df['bb_upper'].iloc[-1] else "Neutral"
    
    # Count signals for summary
    signals = [sma_7_signal, sma_20_signal, sma_50_signal, ema_12_signal, ema_26_signal, 
               macd_signal, rsi_signal, stoch_signal, bb_signal]
    buy_count = signals.count("Buy")
    sell_count = signals.count("Sell")
    neutral_count = signals.count("Neutral")
    total_signals = len(signals)
    
    buy_percent = round((buy_count / total_signals) * 100)
    sell_percent = round((sell_count / total_signals) * 100)
    neutral_percent = round((neutral_count / total_signals) * 100)
    
    # Overall rating
    if buy_percent > 60:
        rating = "Strong Buy"
    elif buy_percent > 40:
        rating = "Buy"
    elif sell_percent > 60:
        rating = "Strong Sell"
    elif sell_percent > 40:
        rating = "Sell"
    else:
        rating = "Neutral"
    
    # Format for display
    formatted_stats = {
        'latest_close': f"{latest_close:.2f}",
        'price_change_1d': f"{price_change_pct:.2f}",
        'latest_close_class': 'success' if price_change_pct > 0 else 'danger',
        'latest_close_icon': 'arrow-up' if price_change_pct > 0 else 'arrow-down',
        'volume': f"{int(volume_value):,}" if volume_value > 0 else "N/A",
        'volume_change_pct': f"{volume_change_pct:.2f}",
        'volume_class': 'success' if volume_change_pct > 0 else 'danger',
        'volume_icon': 'arrow-up' if volume_change_pct > 0 else 'arrow-down',
        'volatility_30d': f"{volatility_30d.iloc[-1]:.2f}%",
        'volatility_high': volatility_30d.iloc[-1] > volatility_30d.mean(),
        'rsi': f"{rsi_val:.2f}",
        'rsi_val': rsi_val,
        'sma_7': f"{df['sma_7'].iloc[-1]:.2f}",
        'sma_20': f"{df['sma_20'].iloc[-1]:.2f}",
        'sma_50': f"{df['sma_50'].iloc[-1]:.2f}",
        'ema_12': f"{df['ema_12'].iloc[-1]:.2f}",
        'ema_26': f"{df['ema_26'].iloc[-1]:.2f}",
        'sma_7_indicator': sma_7_signal,
        'sma_20_indicator': sma_20_signal,
        'sma_50_indicator': sma_50_signal,
        'ema_12_indicator': ema_12_signal,
        'ema_26_indicator': ema_26_signal,
        'macd': f"{df['macd'].iloc[-1]:.4f}",
        'macd_indicator': macd_signal,
        'stoch': f"{stoch_value:.2f}",
        'stoch_indicator': stoch_signal,
        'bb_width': f"{df['bb_width'].iloc[-1]:.4f}",
        'bb_indicator': bb_signal,
        'atr': f"{atr_value:.4f}",
        'rating': rating,
        'buy_signals': buy_percent,
        'sell_signals': sell_percent,
        'neutral_signals': neutral_percent
    }
    
    return formatted_stats, price_change_pct

@bp.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        ticker = request.form['ticker'].upper().strip()
        horizon = int(request.form.get('horizon',30))
        try:
            df = fetch_price_history(ticker)
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect('/')
        
        # Calculate all indicators
        stats, price_change_pct = calculate_indicators(df)
        
        # Forecast
        forecaster = ProphetForecaster()
        forecaster.fit(df)
        forecast_df = forecaster.predict(horizon)
        
        # Get forecast metrics
        current_close = df['close'].iloc[-1]
        forecast_close = forecast_df['yhat'].iloc[-1]
        forecast_change = forecast_close - current_close
        forecast_change_pct = (forecast_change / current_close) * 100
        forecast_end_date = forecast_df.index[-1].strftime('%Y-%m-%d')
        
        # Add forecast stats
        stats.update({
            'forecast_close': f"{forecast_close:.2f}",
            'forecast_change_pct': f"{forecast_change_pct:.2f}",
            'forecast_end_date': forecast_end_date
        })
        
        # Create charts
        price_fig = price_chart(df)
        fc_fig = overlay_forecast(df, forecast_df)
        
        # Current date for display
        current_date = datetime.now().strftime('%B %d, %Y')
        
        return render_template('dashboard.html', 
                              ticker=ticker, 
                              horizon=horizon,
                              stats=stats,
                              price_change_pct=price_change_pct,  # Pass the numeric value
                              price_change_pct_formatted=f"{price_change_pct:.2f}",  # Pass the formatted string as well
                              current_date=current_date,
                              price_chart=price_fig.to_html(full_html=False, include_plotlyjs='cdn'),
    
                                forecast_chart=fc_fig.to_html(full_html=False, include_plotlyjs=False)) 
    return render_template('index.html')

@bp.post('/download/pdf')
def download_pdf():
    ticker = request.form['ticker']
    horizon = int(request.form['horizon'])
    
    # Get data and calculate indicators
    df = fetch_price_history(ticker)
    stats, _ = calculate_indicators(df)
    
    # Forecast
    forecaster = ProphetForecaster()
    forecaster.fit(df)
    forecast_df = forecaster.predict(horizon)
    
    # Get forecast metrics for the report
    current_close = df['close'].iloc[-1]
    forecast_close = forecast_df['yhat'].iloc[-1]
    forecast_change = forecast_close - current_close
    forecast_change_pct = (forecast_change / current_close) * 100
    forecast_end_date = forecast_df.index[-1].strftime('%Y-%m-%d')
    
    # Add forecast stats
    stats.update({
        'forecast_close': f"{forecast_close:.2f}",
        'forecast_change_pct': f"{forecast_change_pct:.2f}",
        'forecast_end_date': forecast_end_date
    })
    
    # Create charts
    price_fig = price_chart(df)
    fc_fig = overlay_forecast(df, forecast_df)
    
    # Current date for the report
    current_date = datetime.now().strftime('%B %d, %Y')
    
    # Create PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
        build_pdf({
            'ticker': ticker,
            'horizon': horizon,
            'stats': stats,
            'current_date': current_date,
            'fig_price': price_fig.to_html(full_html=False, include_plotlyjs='cdn'),
            'fig_forecast': fc_fig.to_html(full_html=False, include_plotlyjs=False)
        }, f.name)
        
        return send_file(f.name, as_attachment=True, download_name=f"{ticker}_report.pdf")

@bp.post('/download/csv')
def download_csv():
    ticker = request.form['ticker']
    horizon = int(request.form['horizon'])
    
    df = fetch_price_history(ticker)
    forecaster = ProphetForecaster()
    forecaster.fit(df)
    forecast_df = forecaster.predict(horizon)
    
    return send_file(
        io.BytesIO(forecast_df.to_csv().encode()), 
        mimetype='text/csv',
        as_attachment=True, 
        download_name=f"{ticker}_forecast.csv"
    )
    