import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import datetime
import time

app = FastAPI()
templates = Jinja2Templates(directory="templates")

_cache = {
    "last_updated": 0,
    "data": [],
    "prediction": None
}

def get_data():
    data_map = {}
    try:
        with open("history.txt", "r") as f:
            for line in f:
                if ":" in line:
                    ts_str, val_str = line.strip().split(":")
                    ts = float(ts_str)
                    val = float(val_str)
                    data_map[ts] = val
    except FileNotFoundError:
        pass
    
    data = [(ts, val) for ts, val in data_map.items()]
    return sorted(data, key=lambda x: x[0])


def predict_completion(data):
    data = data[-60:]
    if len(data) < 2:
        return None
    
    # linear regression!!
    n = len(data)
    sum_x = sum(d[0] for d in data)
    sum_y = sum(d[1] for d in data)
    sum_xy = sum(d[0] * d[1] for d in data)
    sum_xx = sum(d[0] ** 2 for d in data)
    
    denominator = (n * sum_xx - sum_x ** 2)
    if denominator == 0:
        return None
        
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    
    if slope <= 0:
        return None 
        
    target_y = 100
    target_x = (target_y - intercept) / slope
    
    return datetime.datetime.fromtimestamp(target_x)


def get_cached_data_and_prediction():
    now = time.time()
    if now - _cache["last_updated"] < 60:
        return _cache["data"], _cache["prediction"]
    
    data = get_data()
    prediction = predict_completion(data)
    
    _cache["last_updated"] = now
    _cache["data"] = data
    _cache["prediction"] = prediction
    return data, prediction


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    data, prediction = get_cached_data_and_prediction()
    
    # maybe eventually downsample?
    labels = [d[0] * 1000 for d in data]
    values = [d[1] for d in data]
    
    prediction_ts = None
    if prediction:
        prediction_ts = prediction.timestamp()
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "prediction_ts": prediction_ts,
            "labels": labels,
            "values": values,
            "start_ts": data[0][0] if data else None
        }
    )


@app.get("/live", response_class=HTMLResponse)
def read_live(request: Request):
    return templates.TemplateResponse(request=request, name="live.html", context={})


@app.get("/api/data")
def get_api_data():
    data, prediction = get_cached_data_and_prediction()
    
    prediction_ts = None
    if prediction:
        prediction_ts = prediction.timestamp()
        
    current_val = data[-1][1] if data else 0
    last_data_ts = data[-1][0] if data else 0
    
    return {
        "current_percentage": current_val,
        "prediction_ts": prediction_ts,
        "last_updated": _cache["last_updated"],
        "last_data_ts": last_data_ts
    }




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))