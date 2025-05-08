import plotly.graph_objects as go, pandas as pd
def price_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Close Price'))
    fig.update_layout(title='Historical Close Price', xaxis_title='Date', yaxis_title='Price')
    return fig
def overlay_forecast(hist: pd.DataFrame, forecast) -> go.Figure:
    fig = price_chart(hist)
    
    # Handle both Series and DataFrame for backward compatibility
    if isinstance(forecast, pd.DataFrame):
        fig.add_trace(go.Scatter(x=forecast.index, y=forecast['yhat'], name='Forecast', mode='lines', line=dict(dash='dash')))
    else:
        fig.add_trace(go.Scatter(x=forecast.index, y=forecast, name='Forecast', mode='lines', line=dict(dash='dash')))
    
    return fig
