import os
import sys
from datetime import date
from app.services.decomposer import DecomposerService
from app.core.config import settings

# 确保环境变量已加载
print(f"Using API Key: {settings.SILICONFLOW_API_KEY[:5]}...")

service = DecomposerService()

# 模拟一个短期任务：三天内写完一份报告
print("\n=== Testing Short Term Task (AI) ===")
try:
    result = service.decompose(
        title="完成季度业务分析报告",
        year=None,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 3),
        hours_per_week=40,
        work_days=[0, 1, 2, 3, 4],
        strategy="ai",
        preferences={"style": "detail"}
    )
    print("Success!")
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Failed: {e}")
