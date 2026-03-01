"""
测试后端输出格式
验证 time_hierarchy 的结构，并转换为前端期望的扁平格式
"""
import json
from datetime import date

from task_decomposer.utils import decompose_task_by_time


def test_time_hierarchy_output():
    """测试时间层级输出"""
    print("=" * 60)
    print("测试时间层级输出格式")
    print("=" * 60)

    # 测试一个月的时间范围（应该有月、周、日）
    start = date(2025, 1, 1)
    end = date(2025, 1, 31)

    result = decompose_task_by_time(
        goal="测试任务",
        start_date=start,
        end_date=end,
        work_hours_per_day=8.0,
        work_days_per_week=[0, 1, 2, 3, 4]  # 周一到周五
    )

    print(f"\n1. 原始 time_hierarchy 结构:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"\n2. 分析层级结构:")
    print(f"   - 最大粒度: {result['granularity']}")
    print(f"   - 总天数: {result['total_days']}")
    print(f"   - 顶层节点数: {len(result['hierarchy'])}")

    # 检查第一层是什么
    if result['hierarchy']:
        first_node = result['hierarchy'][0]
        print(f"   - 第一层类型: {first_node.get('level')}")
        print(f"   - 第一层标题: {first_node.get('title')}")
        print(f"   - 第一层子节点数: {len(first_node.get('children', []))}")

        # 检查第二层
        if first_node.get('children'):
            second_node = first_node['children'][0]
            print(f"   - 第二层类型: {second_node.get('level')}")
            print(f"   - 第二层子节点数: {len(second_node.get('children', []))}")

            # 检查第三层
            if second_node.get('children'):
                third_node = second_node['children'][0]
                print(f"   - 第三层类型: {third_node.get('level')}")
                print(f"   - 第三层子节点数: {len(third_node.get('children', []))}")

    print("\n" + "=" * 60)
    print("3. 转换为前端期望的扁平格式")
    print("=" * 60)


def convert_to_frontend_format(time_hierarchy: dict) -> dict:
    """
    将后端的嵌套 time_hierarchy 转换为前端期望的扁平格式

    前端期望:
    {
        "year": {...},
        "months": [...],
        "weeks": [...],
        "days": [...]
    }
    """
    months = []
    weeks = []
    days = []

    def extract_nodes(node, level_filter=None):
        """递归提取指定层级的节点"""
        node_level = node.get('level')
        children = node.get('children', [])

        # 如果节点符合筛选条件，添加到对应列表
        if level_filter is None or node_level == level_filter:
            item = {
                "title": node.get('title'),
                "description": node.get('title', ''),
                "start_date": node.get('start_date'),
                "end_date": node.get('end_date'),
                "priority": 1
            }

            # 对于 day 级别，使用 task_date
            if node_level == 'day':
                item['task_date'] = node.get('task_date')
                item['estimated_hours'] = node.get('estimated_hours', 2)
                item['completed'] = False
                days.append(item)
            elif node_level == 'week':
                weeks.append(item)
            elif node_level == 'month':
                months.append(item)

        # 递归处理子节点
        for child in children:
            extract_nodes(child, level_filter)

    # 递归提取所有层级的节点
    for top_node in time_hierarchy.get('hierarchy', []):
        extract_nodes(top_node)

    # 构建 year 对象
    year = {
        "title": time_hierarchy.get('goal', '年度目标'),
        "description": f"完成{time_hierarchy.get('goal', '')}",
        "milestones": ["计划制定", "阶段执行", "评估总结"],
        "start_date": time_hierarchy.get('start_date'),
        "end_date": time_hierarchy.get('end_date')
    }

    return {
        "year": year,
        "months": months,
        "weeks": weeks,
        "days": days
    }


def test_conversion():
    """测试格式转换"""
    # 重新获取测试数据
    start = date(2025, 1, 1)
    end = date(2025, 1, 31)

    result = decompose_task_by_time(
        goal="完成Python学习",
        start_date=start,
        end_date=end,
        work_hours_per_day=8.0,
        work_days_per_week=[0, 1, 2, 3, 4]
    )

    # 转换为前端格式
    frontend_data = convert_to_frontend_format(result)

    print("\n前端期望的格式:")
    print(json.dumps(frontend_data, indent=2, ensure_ascii=False))

    print(f"\n统计:")
    print(f"  - months 数量: {len(frontend_data['months'])}")
    print(f"  - weeks 数量: {len(frontend_data['weeks'])}")
    print(f"  - days 数量: {len(frontend_data['days'])}")

    # 验证数据
    if not frontend_data['months']:
        print("\n[警告] months 为空！")
    if not frontend_data['weeks']:
        print("[警告] weeks 为空！")
    if not frontend_data['days']:
        print("[警告] days 为空！")

    if frontend_data['months'] and frontend_data['weeks'] and frontend_data['days']:
        print("\n[成功] 所有层级都有数据！")


if __name__ == "__main__":
    test_time_hierarchy_output()
    test_conversion()
