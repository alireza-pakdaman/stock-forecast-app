# 📈 Stock Forecast Web App
Minimal Flask app that fetches Yahoo Finance data, builds Prophet forecasts, renders interactive Plotly charts, and exports PDF / CSV reports.
## Quick start (local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app:create_app
flask run
```
### Docker
```bash
docker build -t stockapp .
docker run -p 8000:8000 stockapp
```
*Legal note*: This project is for **educational purposes only** and should not be taken as financial advice.
