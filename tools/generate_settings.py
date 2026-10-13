import json

settings = """
システム起動待機時間,秒,10,0,null,sys_startup_delay_sec
センシング間隔,秒,5,1,null,sys_sensor_check_interval_sec
乾燥時の土壌水分センサ値,null,1000,0,1023,sys_soil_moisture_dry
湿潤時の土壌水分センサ値,null,100,0,1023,sys_soil_moisture_wet
ポンプ流量,mL/s,20,0,null,sys_pump_flow_ml_per_sec
"""

result = {}

for setting in settings.split("\n"):
    if setting.strip() == "":
        continue

    label, unit, default, min_value, max_value, key = setting.split(",")

    result[key] = {
        "label": label,
        "unit": "" if unit == "null" else unit,
        "default": float(default),
        "min": None if min_value == "null" else float(min_value),
        "max": None if max_value == "null" else float(max_value),
    }


with open(
    r"C:\workspace\nitic\2026\pbl\watering\config\setting_definitions.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
