"""
测试 API 转换函数
验证 convert_time_hierarchy_to_frontend_format 是否正确生成 months
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from datetime import date
from task_decomposer.utils import decompose_task_by_time

# 导入 app.py 中的转换函数
from task_decomposer.app import convert_time_hierarchy_to_frontend_format


def test_month_generation():
    """测试 months 生成逻辑"""
    print("=" * 60)
    print("测试 API 转换函数 - 验证 months 生成")
    print("=" * 60)

    # 测试一个月的时间范围
    start = date(2025, 1, 1)
    end = date(2025, 1, 31)

    result = decompose_task_by_time(
        goal="完成Python学习",
        start_date=start,
        end_date=end,
        work_hours_per_day=8.0,
        work_days_per_week=[0, 1, 2, 3, 4]
    )

    print(f"\n原始 time_hierarchy:")
    print(f"  - 粒度: {result['granularity']}")
    print(f"  - 总天数: {result['total_days']}")
    print(f"  - 层级节点数: {len(result['hierarchy'])}")
    print(f"  - 第一层类型: {result['hierarchy'][0]['level'] if result['hierarchy'] else 'None'}")

    # 使用 app.py 中的转换函数
    frontend_data = convert_time_hierarchy_to_frontend_format(result, "完成Python学习")

    print(f"\n转换后的前端格式:")
    print(f"  - months 数量: {len(frontend_data['months'])}")
    print(f"  - weeks 数量: {len(frontend_data['weeks'])}")
    print(f"  - days 数量: {len(frontend_data['days'])}")

    # 验证数据
    if not frontend_data['months']:
        print("\n[错误] months 仍然为空！")
        return False

    if not frontend_data['weeks']:
        print("\n[错误] weeks 为空！")
        return False

    if not frontend_data['days']:
        print("\n[错误] days 为空！")
        return False

    print("\n[成功] 所有层级都有数据！")

    # 打印第一个 month
    if frontend_data['months']:
        print(f"\n第一个 month:")
        print(f"  - title: {frontend_data['months'][0]['title']}")
        print(f"  - start_date: {frontend_data['months'][0]['start_date']}")
        print(f"  - end_date: {frontend_data['months'][0]['end_date']}")

    # 打印第一个 week
    if frontend_data['weeks']:
        print(f"\n第一个 week:")
        print(f"  - title: {frontend_data['weeks'][0]['title']}")
        print(f"  - start_date: {frontend_data['weeks'][0]['start_date']}")
        print(f"  - end_date: {frontend_data['weeks'][0]['end_date']}")

    # 打印第一个 day
    if frontend_data['days']:
        print(f"\n第一个 day:")
        print(f"  - title: {frontend_data['days'][0]['title']}")
        print(f"  - task_date: {frontend_data['days'][0]['task_date']}")
        print(f"  - estimated_hours: {frontend_data['days'][0]['estimated_hours']}")

    return True


if __name__ == "__main__":
    success = test_month_generation()
    sys.exit(0 if success else 1)
