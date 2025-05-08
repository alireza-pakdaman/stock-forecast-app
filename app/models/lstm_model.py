import pandas as pd, numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
from sklearn.preprocessing import MinMaxScaler
class LSTMForecaster:
    def __init__(self, seq_len=60, epochs=10, batch_size=32):
        self.seq_len = seq_len; self.epochs = epochs; self.batch_size = batch_size
        self.scaler = MinMaxScaler()
        self.model = None; self.last_sequence = None
    def _prep(self, series):
        scaled = self.scaler.fit_transform(series.values.reshape(-1,1))
        X, y = [], []
        for i in range(self.seq_len, len(scaled)):
            X.append(scaled[i-self.seq_len:i,0]); y.append(scaled[i,0])
        return np.array(X), np.array(y)
    def fit(self, df: pd.DataFrame):
        series = df['close']; X, y = self._prep(series)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        self.model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(X.shape[1],1)),
            LSTM(50),
            Dense(1)
        ])
        self.model.compile(optimizer='adam', loss='mse')
        self.model.fit(X, y, epochs=self.epochs, batch_size=self.batch_size, verbose=0)
        self.last_sequence = series.values[-self.seq_len:]
    def predict(self, steps=30):
        if self.model is None: raise RuntimeError("Call fit() first.")
        seq = self.last_sequence.copy(); preds=[]
        import pandas as pd, numpy as np
        for _ in range(steps):
            inp = self.scaler.transform(seq.reshape(-1,1))[-self.seq_len:]
            pred = self.model.predict(inp.reshape((1,self.seq_len,1)), verbose=0)[0][0]
            val = self.scaler.inverse_transform([[pred]])[0][0]; preds.append(val)
            seq = np.append(seq[1:], val)
        idx = pd.date_range(start=pd.Timestamp.today().normalize()+pd.Timedelta(days=1), periods=steps, freq='B')
        return pd.Series(preds, index=idx)
