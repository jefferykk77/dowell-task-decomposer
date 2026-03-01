"""
测试时间粒度判断和任务拆解功能
演示从年度/季度/月度/周度/日度的自动判断和层级拆解
"""

from datetime import date
from task_decomposer.utils import (
    determine_time_granularity,
    decompose_task_by_time,
    flatten_hierarchy,
    TimeGranularity
)


def print_hierarchy(hierarchy: dict, indent: int = 0):
    """递归打印层级结构"""
    prefix = "  " * indent
    level = hierarchy.get("level", "unknown")
    title = hierarchy.get("title", "无标题")
    start = hierarchy.get("start_date", "")
    end = hierarchy.get("end_date", "")
    task_date = hierarchy.get("task_date", "")

    if level == "day":
        print(f"{prefix}[{level.upper()}] {title} - {task_date}")
    else:
        print(f"{prefix}[{level.upper()}] {title}")
        if start and end:
            print(f"{prefix}   时间: {start} ~ {end}")

    # 递归打印子节点
    children = hierarchy.get("children", [])
    if children and indent < 3:  # 限制打印深度
        print(f"{prefix}   +-- 子节点 ({len(children)}个)")
        for child in children[:3]:  # 只打印前3个
            print_hierarchy(child, indent + 1)
        if len(children) > 3:
            print(f"{prefix}      ... 还有 {len(children) - 3} 个节点")


def test_granularity(name: str, start: date, end: date):
    """测试单个时间粒度"""
    print(f"\n{'='*80}")
    print(f"测试场景: {name}")
    print(f"{'='*80}")

    # 1. 判断时间粒度
    granularity = determine_time_granularity(start, end)
    print(f"\n[时间粒度判断]")
    print(f"   时间范围: {start} ~ {end}")
    print(f"   总天数: {(end - start).days + 1} 天")
    print(f"   判断结果: {granularity.value.upper()}")

    # 2. 执行任务拆解
    print(f"\n[执行任务拆解]")
    result = decompose_task_by_time(
        goal=f"{name}任务目标",
        start_date=start,
        end_date=end,
        work_hours_per_day=8.0,
        work_days_per_week=[0, 1, 2, 3, 4]  # 周一到周五
    )

    print(f"   拆解粒度: {result['granularity'].value.upper()}")
    print(f"   总层级节点: {len(result['hierarchy'])} 个")

    # 3. 显示层级结构示例
    print(f"\n[层级结构示例 (前2个节点)]")
    for i, node in enumerate(result['hierarchy'][:2]):
        print(f"\n节点 {i+1}:")
        print_hierarchy(node, 1)

    # 4. 扁平化统计
    print(f"\n[扁平化统计]")
    flat_tasks = flatten_hierarchy(result)
    level_counts = {}
    for task in flat_tasks:
        level = task['level']
        level_counts[level] = level_counts.get(level, 0) + 1

    for level, count in sorted(level_counts.items()):
        level_name = {
            'year': '年度',
            'quarter': '季度',
            'month': '月度',
            'week': '周度',
            'day': '日度'
        }.get(level, level)
        print(f"   {level_name}: {count} 个")

    print(f"   总计: {len(flat_tasks)} 个任务节点")


def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("时间粒度判断与任务拆解测试")
    print("="*80)

    # 测试不同时间粒度的场景
    test_cases = [
        ("年度任务", date(2024, 1, 1), date(2024, 12, 31)),
        ("季度任务", date(2024, 1, 1), date(2024, 3, 31)),
        ("月度任务", date(2024, 1, 1), date(2024, 1, 31)),
        ("周度任务", date(2024, 1, 15), date(2024, 1, 21)),
        ("单日任务", date(2024, 1, 15), date(2024, 1, 15)),
    ]

    for name, start, end in test_cases:
        test_granularity(name, start, end)

    print(f"\n{'='*80}")
    print("[OK] 所有测试完成")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
