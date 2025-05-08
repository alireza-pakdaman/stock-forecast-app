from app.data.loader import fetch_price_history
from app.models.prophet_model import ProphetForecaster
def test_pipeline():
    df = fetch_price_history('AAPL', start='2024-01-01')
    assert not df.empty
    fore = ProphetForecaster(); fore.fit(df)
    yhat = fore.predict(7)
    assert len(yhat)==7
