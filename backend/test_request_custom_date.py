import requests
import json
from datetime import datetime, timedelta

url = "http://127.0.0.1:8000/api/tasks/decompose"
headers = {"Content-Type": "application/json"}

# 截止日期为30天后
end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

payload = {
    "title": "30天Python冲刺",
    "end_date": end_date,
    "strategy": "ai"
}

print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Response Year Node:")
        print(json.dumps(data.get("year", {}), ensure_ascii=False, indent=2))
        # 验证 start_date 是否是今天 (或者接近今天)
        print(f"Plan Start: {data.get('year', {}).get('start_date')}")
        print(f"Plan End: {data.get('year', {}).get('end_date')}")
    else:
        print("Error Response:")
        print(response.text)
except Exception as e:
    print(f"Request failed: {e}")
