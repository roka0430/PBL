import json

settings = """
sys,sensing_interval_sec,センシング間隔,秒,10,1,None
sys,startup_waiting_sec,起動待機時間,秒,10,0,None
sys,soil_moisture_dry,乾燥時の土壌水分センサ値,,800,0,1023
sys,soil_moisture_wet,湿潤時の土壌水分センサ値,,300,0,1023
sys,pump_flow_rate_ml_sec,ポンプ流量,mL/s,10,1,None
thr,determination_interval_sec,給水判定間隔,秒,60,1,None
thr,start_soil_moisture_percent,給水開始しきい値,%,30,0,100
thr,stop_soil_moisture_percent,給水終了しきい値,%,50,0,100
fix,determination_interval_sec,給水判定間隔,秒,60,1,None
fix,start_soil_moisture_percent,給水開始しきい値,%,30,0,100
fix,amount_ml,給水量,mL,50,10,None
sch,interval_sec,給水間隔,秒,21600,60,None
sch,amount_ml,給水量,mL,50,10,None
"""

result = {}

for setting in settings.split("\n"):
    if setting.strip() == "":
        continue

    tpy, key, label, unit, default, minv, maxv = setting.split(",")

    if tpy not in result:
        result[tpy] = {}

    result[tpy][key] = {
        "label": label,
        "unit": unit,
        "default": float(default),
        "min": None if minv == "None" else float(minv),
        "max": None if maxv == "None" else float(maxv),
    }


with open(
    r"C:\workspace\nitic\2026\pbl\watering\config\setting_definitions.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
