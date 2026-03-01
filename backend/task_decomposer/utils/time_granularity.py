"""
时间粒度判断和任务拆解工具
根据时间范围自动判断粒度并按层级拆解任务
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class TimeGranularity(str, Enum):
    """时间粒度枚举"""
    YEAR = "year"       # 年度任务
    QUARTER = "quarter" # 季度任务
    MONTH = "month"     # 月度任务
    WEEK = "week"       # 周度任务
    DAY = "day"         # 日任务


def determine_time_granularity(start_date: date, end_date: date) -> TimeGranularity:
    """
    根据开始和结束日期判断任务的时间粒度

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        TimeGranularity: 时间粒度
    """
    delta_days = (end_date - start_date).days

    # 判断逻辑
    if delta_days >= 365:  # 1年及以上
        return TimeGranularity.YEAR
    elif delta_days >= 90:  # 3个月及以上
        return TimeGranularity.QUARTER
    elif delta_days >= 30:  # 1个月及以上
        return TimeGranularity.MONTH
    elif delta_days >= 7:  # 1周及以上
        return TimeGranularity.WEEK
    else:  # 小于1周
        return TimeGranularity.DAY


def split_time_range(
    start_date: date,
    end_date: date,
    granularity: TimeGranularity
) -> List[Tuple[date, date, str]]:
    """
    将时间范围按指定粒度拆分成多个时间段

    Args:
        start_date: 开始日期
        end_date: 结束日期
        granularity: 时间粒度

    Returns:
        List[Tuple[date, date, str]]: 时间段列表，每个元素为 (开始日期, 结束日期, 粒度标签)
    """
    periods = []
    current_start = start_date

    while current_start <= end_date:
        if granularity == TimeGranularity.YEAR:
            # 按年拆分
            year = current_start.year
            current_end = min(date(year, 12, 31), end_date)
            label = f"{year}年"
            periods.append((current_start, current_end, label))

            # 移动到下一年
            current_start = date(year + 1, 1, 1)

        elif granularity == TimeGranularity.QUARTER:
            # 按季度拆分
            year = current_start.year
            month = current_start.month

            # 计算当前季度
            quarter = (month - 1) // 3 + 1
            quarter_start_month = (quarter - 1) * 3 + 1

            # 计算季度结束
            if quarter == 1:
                current_end = min(date(year, 3, 31), end_date)
            elif quarter == 2:
                current_end = min(date(year, 6, 30), end_date)
            elif quarter == 3:
                current_end = min(date(year, 9, 30), end_date)
            else:  # quarter == 4
                current_end = min(date(year, 12, 31), end_date)

            label = f"{year}年Q{quarter}"
            periods.append((current_start, current_end, label))

            # 移动到下一季度
            if quarter == 4:
                current_start = date(year + 1, 1, 1)
            else:
                current_start = date(year, quarter_start_month + 3, 1)

        elif granularity == TimeGranularity.MONTH:
            # 按月拆分
            year = current_start.year
            month = current_start.month

            # 计算月末
            if month == 12:
                current_end = min(date(year, 12, 31), end_date)
            else:
                current_end = min(date(year, month + 1, 1) - timedelta(days=1), end_date)

            label = f"{year}年{month}月"
            periods.append((current_start, current_end, label))

            # 移动到下个月
            if month == 12:
                current_start = date(year + 1, 1, 1)
            else:
                current_start = date(year, month + 1, 1)

        elif granularity == TimeGranularity.WEEK:
            # 按周拆分（周一到周日）
            # 找到当前周的周一
            weekday = current_start.weekday()
            week_start = current_start - timedelta(days=weekday)

            # 周日
            week_end = week_start + timedelta(days=6)

            # 确保不超过结束日期
            week_end = min(week_end, end_date)

            label = f"{week_start.month}/{week_start.day}-{week_end.month}/{week_end.day}"
            periods.append((week_start, week_end, label))

            # 移动到下周一
            current_start = week_end + timedelta(days=1)

        elif granularity == TimeGranularity.DAY:
            # 按天拆分
            label = f"{current_start.month}/{current_start.day}"
            periods.append((current_start, current_start, label))

            # 移动到下一天
            current_start = current_start + timedelta(days=1)

        else:
            break

    return periods


def decompose_task_by_time(
    goal: str,
    start_date: date,
    end_date: date,
    work_hours_per_day: float = 8.0,
    work_days_per_week: List[int] = None
) -> Dict[str, Any]:
    """
    根据时间范围自动拆解任务到天级别

    Args:
        goal: 任务目标
        start_date: 开始日期
        end_date: 结束日期
        work_hours_per_day: 每天工作小时数
        work_days_per_week: 每周工作日列表（0=周一, 6=周日）

    Returns:
        Dict[str, Any]: 包含时间粒度、层级任务、时间段等信息
    """
    if work_days_per_week is None:
        work_days_per_week = [0, 1, 2, 3, 4]  # 默认周一到周五

    # 1. 判断最大时间粒度
    max_granularity = determine_time_granularity(start_date, end_date)

    # 2. 构建层级结构
    hierarchy = {
        "goal": goal,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "granularity": max_granularity,
        "total_days": (end_date - start_date).days + 1,
        "hierarchy": []
    }

    # 3. 根据最大粒度开始拆解
    if max_granularity == TimeGranularity.YEAR:
        # 年度任务 -> 季度 -> 月度 -> 周 -> 天
        quarters = split_time_range(start_date, end_date, TimeGranularity.QUARTER)
        for q_start, q_end, q_label in quarters:
            quarter_data = {
                "level": "quarter",
                "title": f"{q_label}目标",
                "start_date": q_start.isoformat(),
                "end_date": q_end.isoformat(),
                "children": []
            }

            # 拆解到月
            months = split_time_range(q_start, q_end, TimeGranularity.MONTH)
            for m_start, m_end, m_label in months:
                month_data = {
                    "level": "month",
                    "title": f"{m_label}目标",
                    "start_date": m_start.isoformat(),
                    "end_date": m_end.isoformat(),
                    "children": []
                }

                # 拆解到周
                weeks = split_time_range(m_start, m_end, TimeGranularity.WEEK)
                for w_start, w_end, w_label in weeks:
                    week_data = {
                        "level": "week",
                        "title": f"{w_label}周目标",
                        "start_date": w_start.isoformat(),
                        "end_date": w_end.isoformat(),
                        "children": []
                    }

                    # 拆解到天
                    days = split_time_range(w_start, w_end, TimeGranularity.DAY)
                    for d_start, d_end, d_label in days:
                        # 只包含工作日
                        if d_start.weekday() in work_days_per_week:
                            day_data = {
                                "level": "day",
                                "title": f"{d_label}任务",
                                "task_date": d_start.isoformat(),
                                "estimated_hours": work_hours_per_day,
                                "work_day": True
                            }
                            week_data["children"].append(day_data)

                    month_data["children"].append(week_data)

                quarter_data["children"].append(month_data)

            hierarchy["hierarchy"].append(quarter_data)

    elif max_granularity == TimeGranularity.QUARTER:
        # 季度任务 -> 月度 -> 周 -> 天
        months = split_time_range(start_date, end_date, TimeGranularity.MONTH)
        for m_start, m_end, m_label in months:
            month_data = {
                "level": "month",
                "title": f"{m_label}目标",
                "start_date": m_start.isoformat(),
                "end_date": m_end.isoformat(),
                "children": []
            }

            # 拆解到周
            weeks = split_time_range(m_start, m_end, TimeGranularity.WEEK)
            for w_start, w_end, w_label in weeks:
                week_data = {
                    "level": "week",
                    "title": f"{w_label}周目标",
                    "start_date": w_start.isoformat(),
                    "end_date": w_end.isoformat(),
                    "children": []
                }

                # 拆解到天
                days = split_time_range(w_start, w_end, TimeGranularity.DAY)
                for d_start, d_end, d_label in days:
                    if d_start.weekday() in work_days_per_week:
                        day_data = {
                            "level": "day",
                            "title": f"{d_label}任务",
                            "task_date": d_start.isoformat(),
                            "estimated_hours": work_hours_per_day,
                            "work_day": True
                        }
                        week_data["children"].append(day_data)

                month_data["children"].append(week_data)

            hierarchy["hierarchy"].append(month_data)

    elif max_granularity == TimeGranularity.MONTH:
        # 月度任务 -> 周 -> 天
        weeks = split_time_range(start_date, end_date, TimeGranularity.WEEK)
        for w_start, w_end, w_label in weeks:
            week_data = {
                "level": "week",
                "title": f"{w_label}周目标",
                "start_date": w_start.isoformat(),
                "end_date": w_end.isoformat(),
                "children": []
            }

            # 拆解到天
            days = split_time_range(w_start, w_end, TimeGranularity.DAY)
            for d_start, d_end, d_label in days:
                if d_start.weekday() in work_days_per_week:
                    day_data = {
                        "level": "day",
                        "title": f"{d_label}任务",
                        "task_date": d_start.isoformat(),
                        "estimated_hours": work_hours_per_day,
                        "work_day": True
                    }
                    week_data["children"].append(day_data)

            hierarchy["hierarchy"].append(week_data)

    elif max_granularity == TimeGranularity.WEEK:
        # 周度任务 -> 天
        days = split_time_range(start_date, end_date, TimeGranularity.DAY)
        for d_start, d_end, d_label in days:
            if d_start.weekday() in work_days_per_week:
                day_data = {
                    "level": "day",
                    "title": f"{d_label}任务",
                    "task_date": d_start.isoformat(),
                    "estimated_hours": work_hours_per_day,
                    "work_day": True
                }
                hierarchy["hierarchy"].append(day_data)

    else:  # TimeGranularity.DAY
        # 单日任务
        day_data = {
            "level": "day",
            "title": f"{start_date.month}/{start_date.day}任务",
            "task_date": start_date.isoformat(),
            "estimated_hours": work_hours_per_day,
            "work_day": True
        }
        hierarchy["hierarchy"].append(day_data)

    return hierarchy


def flatten_hierarchy(hierarchy: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    将层级结构扁平化，返回所有层级的任务列表

    Args:
        hierarchy: 层级结构字典

    Returns:
        List[Dict[str, Any]]: 扁平化的任务列表
    """
    result = []

    def flatten_node(node: Dict[str, Any], parent_id: str = None):
        """递归扁平化节点"""
        item = {
            "level": node.get("level"),
            "title": node.get("title"),
            "start_date": node.get("start_date"),
            "end_date": node.get("end_date"),
            "task_date": node.get("task_date"),
            "estimated_hours": node.get("estimated_hours"),
            "parent_id": parent_id
        }
        result.append(item)

        # 递归处理子节点
        children = node.get("children", [])
        for i, child in enumerate(children):
            child_parent_id = f"{parent_id}-{i}" if parent_id else str(i)
            flatten_node(child, child_parent_id)

    # 扁平化顶层
    for i, node in enumerate(hierarchy.get("hierarchy", [])):
        flatten_node(node, str(i))

    return result


if __name__ == "__main__":
    # 测试代码
    test_cases = [
        (date(2024, 1, 1), date(2024, 12, 31)),    # 年度
        (date(2024, 1, 1), date(2024, 3, 31)),     # 季度
        (date(2024, 1, 1), date(2024, 1, 31)),     # 月度
        (date(2024, 1, 1), date(2024, 1, 21)),     # 周度
        (date(2024, 1, 15), date(2024, 1, 15)),    # 单日
    ]

    for start, end in test_cases:
        print(f"\n{'='*60}")
        print(f"测试: {start} ~ {end} ({(end-start).days + 1}天)")
        print(f"{'='*60}")

        granularity = determine_time_granularity(start, end)
        print(f"时间粒度: {granularity}")

        result = decompose_task_by_time("测试目标", start, end)

        print(f"\n层级结构:")
        print(f"  最大粒度: {result['granularity']}")
        print(f"  总天数: {result['total_days']}")
        print(f"  层级节点数: {len(result['hierarchy'])}")

        # 打印第一层
        for item in result['hierarchy'][:3]:
            print(f"  - [{item['level']}] {item['title']}: {item.get('start_date', '')} ~ {item.get('end_date', '')}")
            if item.get('children'):
                print(f"    子节点数: {len(item['children'])}")
