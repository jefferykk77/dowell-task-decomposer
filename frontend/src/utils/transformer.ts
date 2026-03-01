/**
 * Transformer utility to convert backend responses to frontend display format
 * Supports both v1 (legacy) and v2 (task_decomposer) backend responses
 */

import type {
  LegacyDecomposeResponse,
  PlanSchema,
  TaskSchema,
  TaskItem,
  TimeHierarchy,
  TimeHierarchyFlat,
  TimeHierarchyNode,
} from '../types/task';
import { parseISO, isWithinInterval, startOfDay, endOfDay } from 'date-fns';

// ==========================================
// Legacy Types (for backward compatibility)
// ==========================================

export interface DayNode extends TaskItem {
  type: 'day';
}

export interface WeekNode extends TaskItem {
  type: 'week';
  children: DayNode[];
}

export interface MonthNode extends TaskItem {
  type: 'month';
  children: WeekNode[];
}

export interface YearNode extends TaskItem {
  type: 'year';
  children: (MonthNode | WeekNode | DayNode)[];
}

// ==========================================
// V2 Backend Types
// ==========================================

export interface PlanNode {
  id: string;
  title: string;
  description?: string;
  type: 'goal' | 'milestone' | 'task' | 'subtask';
  children: PlanNode[];
  metadata: {
    start_date?: string;
    end_date?: string;
    priority?: string;
    risk?: string;
    estimate_hours?: number;
    definition_of_done?: string;
    assignee?: string;
    tags?: string[];
  };
}

// ==========================================
// Legacy Transform Function (V1 Backend)
// ==========================================

export function transformLegacyToTree(data: LegacyDecomposeResponse): YearNode {
  const { year, months, weeks, days } = data;

  const monthNodes: MonthNode[] = months.map((m: TaskItem) => ({
    ...m,
    type: 'month',
    children: [],
  }));

  const weekNodes: WeekNode[] = weeks.map((w: TaskItem) => ({
    ...w,
    type: 'week',
    children: [],
  }));

  const dayNodes: DayNode[] = days.map((d: TaskItem) => ({
    ...d,
    type: 'day',
  }));

  // 1. 如果有 Month，尝试 Year -> Month -> Week -> Day
  if (monthNodes.length > 0) {
    // 组装 Weeks 到 Months
    weekNodes.forEach((week) => {
      if (!week.start_date || !week.end_date) return;
      const weekStart = parseISO(week.start_date);
      const targetMonth = monthNodes.find((m) => {
        if (!m.start_date || !m.end_date) return false;
        const mStart = parseISO(m.start_date);
        const mEnd = parseISO(m.end_date);
        return isWithinInterval(weekStart, { start: mStart, end: mEnd });
      });
      if (targetMonth) {
        targetMonth.children.push(week);
      }
    });

    // 组装 Days 到 Weeks (优先) 或 Months (兜底)
    dayNodes.forEach((day) => {
      if (!day.task_date) return;
      const taskDate = parseISO(day.task_date);

      // 尝试找到 Week
      const targetWeek = weekNodes.find((w) => {
        if (!w.start_date || !w.end_date) return false;
        const wStart = startOfDay(parseISO(w.start_date));
        const wEnd = endOfDay(parseISO(w.end_date));
        return isWithinInterval(taskDate, { start: wStart, end: wEnd });
      });

      if (targetWeek) {
        targetWeek.children.push(day);
      }
    });

    return {
      ...year,
      type: 'year',
      children: monthNodes,
    };
  }

  // 2. 如果没有 Month 但有 Week，尝试 Year -> Week -> Day
  if (weekNodes.length > 0) {
    dayNodes.forEach((day) => {
      if (!day.task_date) return;
      const taskDate = parseISO(day.task_date);

      const targetWeek = weekNodes.find((w) => {
        if (!w.start_date || !w.end_date) return false;
        const wStart = startOfDay(parseISO(w.start_date));
        const wEnd = endOfDay(parseISO(w.end_date));
        return isWithinInterval(taskDate, { start: wStart, end: wEnd });
      });

      if (targetWeek) {
        targetWeek.children.push(day);
      }
    });

    return {
      ...year,
      type: 'year',
      children: weekNodes,
    };
  }

  // 3. 如果没有 Month 和 Week，只有 Day，尝试 Year -> Day
  return {
    ...year,
    type: 'year',
    children: dayNodes,
  };
}

// ==========================================
// V2 Transform Functions (New Backend)
// ==========================================

/**
 * Convert backend PlanSchema to hierarchical tree structure
 */
export function transformPlanToTree(plan: PlanSchema): PlanNode {
  const rootNode: PlanNode = {
    id: 'root',
    title: plan.goal,
    description: plan.context,
    type: 'goal',
    children: [],
    metadata: {
      start_date: plan.tasks[0]?.start_date,
      end_date: plan.tasks[plan.tasks.length - 1]?.end_date,
    },
  };

  // Add milestones as children
  plan.milestones.forEach((milestone) => {
    const milestoneNode: PlanNode = {
      id: milestone.id,
      title: milestone.title,
      description: milestone.description,
      type: 'milestone',
      children: [],
      metadata: {
        end_date: milestone.due,
        definition_of_done: milestone.definition_of_done,
      },
    };

    // Find tasks related to this milestone
    const relatedTasks = plan.tasks.filter((task) =>
      task.tags.includes(milestone.id.toLowerCase())
    );

    relatedTasks.forEach((task) => {
      const taskNode = transformTaskToNode(task);
      milestoneNode.children.push(taskNode);
    });

    rootNode.children.push(milestoneNode);
  });

  // Add tasks without milestones directly to root
  const tasksWithoutMilestones = plan.tasks.filter(
    (task) => !task.tags.some((tag) =>
      plan.milestones.some((m) => m.id.toLowerCase() === tag.toLowerCase())
    )
  );

  tasksWithoutMilestones.forEach((task) => {
    rootNode.children.push(transformTaskToNode(task));
  });

  return rootNode;
}

/**
 * Convert TaskSchema to PlanNode
 */
function transformTaskToNode(task: TaskSchema): PlanNode {
  return {
    id: task.id,
    title: task.title,
    description: task.description,
    type: task.depends_on?.length > 0 ? 'subtask' : 'task',
    children: [],
    metadata: {
      start_date: task.start_date,
      end_date: task.end_date,
      priority: task.priority,
      risk: task.risk,
      estimate_hours: task.estimate_hours,
      definition_of_done: task.definition_of_done,
      assignee: task.assignee,
      tags: task.tags,
    },
  };
}

/**
 * Convert flat time hierarchy to YearNode format
 * This is the PREFERRED method when time_hierarchy_flat is available
 * 后端已提供扁平的 months, weeks, days 结构，直接组装成树状结构
 */
export function transformTimeHierarchyFlatToYearNode(flat: TimeHierarchyFlat): YearNode {
  // 转换 months
  const monthNodes: MonthNode[] = flat.months.map(m => ({
    ...m,
    type: 'month' as const,
    children: [] as WeekNode[],
  }));

  // 转换 weeks
  const weekNodes: WeekNode[] = flat.weeks.map(w => ({
    ...w,
    type: 'week' as const,
    children: [] as DayNode[],
  }));

  // 转换 days
  const dayNodes: DayNode[] = flat.days.map(d => ({
    ...d,
    type: 'day' as const,
  }));

  // 将 weeks 组装到对应的 months
  weekNodes.forEach((week) => {
    if (!week.start_date || !week.end_date) return;

    const targetMonth = monthNodes.find((m) => {
      if (!m.start_date || !m.end_date) return false;
      const mStart = parseISO(m.start_date);
      const mEnd = parseISO(m.end_date);
      const wStart = parseISO(week.start_date!);
      return isWithinInterval(wStart, { start: mStart, end: mEnd });
    });

    if (targetMonth) {
      targetMonth.children.push(week);
    }
  });

  // 将 days 组装到对应的 weeks
  dayNodes.forEach((day) => {
    if (!day.task_date) return;

    const targetWeek = weekNodes.find((w) => {
      if (!w.start_date || !w.end_date) return false;
      const wStart = startOfDay(parseISO(w.start_date));
      const wEnd = endOfDay(parseISO(w.end_date));
      const taskDate = parseISO(day.task_date!);
      return isWithinInterval(taskDate, { start: wStart, end: wEnd });
    });

    if (targetWeek) {
      targetWeek.children.push(day);
    }
  });

  // 计算总工时
  const totalHours = dayNodes.reduce((sum, day) => sum + (day.estimated_hours || 0), 0);

  return {
    title: flat.year.title,
    description: flat.year.description,
    type: 'year' as const,
    start_date: flat.year.start_date,
    end_date: flat.year.end_date,
    milestones: flat.year.milestones,
    estimated_hours: totalHours,
    children: monthNodes.length > 0 ? monthNodes : weekNodes,
  };
}

/**
 * Convert time hierarchy to YearNode format
 * This is the fallback method when time_hierarchy is available but not flat
 */
export function transformTimeHierarchyToYearNode(timeHierarchy: TimeHierarchy): YearNode {
  // 递归转换时间层级节点
  function convertNode(node: TimeHierarchyNode): any {
    const baseNode = {
      title: node.title,
      description: `${node.level.toUpperCase()} - ${node.title}`,
      start_date: node.start_date,
      end_date: node.end_date,
      task_date: node.task_date,
      estimated_hours: node.estimated_hours,
      priority: 1,
      children: [],
    };

    // 根据层级设置类型
    if (node.level === 'day') {
      return { ...baseNode, type: 'day' as const };
    } else if (node.level === 'week') {
      return { ...baseNode, type: 'week' as const };
    } else if (node.level === 'month') {
      return { ...baseNode, type: 'month' as const };
    } else if (node.level === 'quarter') {
      // 季度作为特殊的月份节点处理
      return { ...baseNode, type: 'month' as const };
    } else {
      return { ...baseNode, type: 'year' as const };
    }
  }

  // 递归构建层级结构
  function buildHierarchy(nodes: TimeHierarchyNode[]): any[] {
    return nodes.map(node => {
      const converted = convertNode(node);
      if (node.children && node.children.length > 0) {
        converted.children = buildHierarchy(node.children);
      }
      return converted;
    });
  }

  // 构建顶层节点
  const topLevelNodes = buildHierarchy(timeHierarchy.hierarchy);

  return {
    title: timeHierarchy.goal,
    description: `时间粒度: ${timeHierarchy.granularity.toUpperCase()}\n总天数: ${timeHierarchy.total_days}天`,
    type: 'year' as const,
    start_date: timeHierarchy.start_date,
    end_date: timeHierarchy.end_date,
    estimated_hours: topLevelNodes.reduce((sum, node) => sum + (node.estimated_hours || 0), 0),
    children: topLevelNodes,
  };
}

/**
 * Check if tasks have hierarchical structure (with level field)
 */
function hasHierarchicalTasks(plan: PlanSchema): boolean {
  return plan.tasks.length > 0 && plan.tasks.some(t => t.level);
}

/**
 * Convert hierarchical tasks (with level and parent_task_id) to YearNode
 */
function transformHierarchicalTasksToYearNode(plan: PlanSchema): YearNode {
  // Create a map of tasks by ID for quick lookup
  const taskMap = new Map<string, TaskSchema>();
  plan.tasks.forEach(task => taskMap.set(task.id, task));

  // Helper function to convert TaskSchema to appropriate node type
  const taskToNode = (task: TaskSchema): MonthNode | WeekNode | DayNode => {
    const baseNode = {
      title: task.title,
      description: task.description,
      start_date: task.start_date,
      end_date: task.end_date,
      task_date: task.start_date,
      estimated_hours: task.estimate_hours,
      priority: ['P0', 'P1', 'P2', 'P3'].indexOf(task.priority) + 1,
      children: [] as any[],
    };

    if (task.level === 'day') {
      return { ...baseNode, type: 'day' as const };
    } else if (task.level === 'week') {
      return { ...baseNode, type: 'week' as const, children: [] as DayNode[] };
    } else {
      return { ...baseNode, type: 'month' as const, children: [] as WeekNode[] };
    }
  };

  // Build the hierarchy
  const monthNodes: MonthNode[] = [];
  const weekNodes: WeekNode[] = [];
  const dayNodes: DayNode[] = [];

  // First pass: convert all tasks to nodes
  const nodeMap = new Map<string, MonthNode | WeekNode | DayNode>();
  plan.tasks.forEach(task => {
    const node = taskToNode(task);
    nodeMap.set(task.id, node);

    if (task.level === 'month') {
      monthNodes.push(node as MonthNode);
    } else if (task.level === 'week') {
      weekNodes.push(node as WeekNode);
    } else if (task.level === 'day') {
      dayNodes.push(node as DayNode);
    }
  });

  // Second pass: build parent-child relationships
  plan.tasks.forEach(task => {
    const node = nodeMap.get(task.id);
    if (!node || !task.parent_task_id) return;

    const parentNode = nodeMap.get(task.parent_task_id);
    if (!parentNode) return;

    // Add child to parent
    if (parentNode.type === 'month' && node.type === 'week') {
      (parentNode as MonthNode).children.push(node as WeekNode);
    } else if (parentNode.type === 'week' && node.type === 'day') {
      (parentNode as WeekNode).children.push(node as DayNode);
    }
  });

  // Calculate total hours
  const totalHours = plan.tasks.reduce(
    (sum, task) => sum + (task.estimate_hours || 0),
    0
  );

  return {
    title: plan.goal,
    description: plan.context,
    type: 'year',
    start_date: plan.tasks[0]?.start_date,
    end_date: plan.tasks[plan.tasks.length - 1]?.end_date,
    estimated_hours: totalHours,
    children: monthNodes.length > 0 ? monthNodes : weekNodes,
  };
}

/**
 * Convert V2 PlanSchema to legacy YearNode format
 * This allows using existing UI components with new backend
 */
export function transformPlanSchemaToYearNode(plan: PlanSchema): YearNode {
  // 1. 优先使用 time_hierarchy_flat (后端已转换为扁平格式)
  if (plan.time_hierarchy_flat) {
    return transformTimeHierarchyFlatToYearNode(plan.time_hierarchy_flat);
  }

  // 2. 备用：使用嵌套的 time_hierarchy
  if (plan.time_hierarchy) {
    return transformTimeHierarchyToYearNode(plan.time_hierarchy);
  }

  // 3. 使用层级任务结构（如果有 level 字段）
  if (hasHierarchicalTasks(plan)) {
    return transformHierarchicalTasksToYearNode(plan);
  }

  // 3. Fallback: Calculate total hours
  const totalHours = plan.tasks.reduce(
    (sum, task) => sum + (task.estimate_hours || 0),
    0
  );

  // Convert milestones to months
  const monthNodes: MonthNode[] = plan.milestones.map((milestone) => {
    const relatedTasks = plan.tasks.filter((task) =>
      task.tags.includes(milestone.id.toLowerCase())
    );

    return {
      title: milestone.title,
      description: milestone.description,
      start_date: milestone.due,
      end_date: undefined,
      type: 'month',
      milestones: [milestone.title],
      estimated_hours: relatedTasks.reduce((sum, t) => sum + (t.estimate_hours || 0), 0),
      priority: 1,
      children: [],
    };
  });

  // Convert high-priority tasks to weeks
  const weekNodes: WeekNode[] = plan.tasks
    .filter((task) => task.priority === 'P0' || task.priority === 'P1')
    .slice(0, 20)
    .map((task) => ({
      title: task.title,
      description: task.description,
      start_date: task.start_date,
      end_date: task.end_date,
      type: 'week',
      priority: ['P0', 'P1', 'P2', 'P3'].indexOf(task.priority) + 1,
      estimated_hours: task.estimate_hours,
      children: [],
    }));

  // Convert all tasks to days
  const dayNodes: DayNode[] = plan.tasks.map((task) => ({
    title: task.title,
    description: task.description,
    start_date: task.start_date,
    end_date: task.end_date,
    task_date: task.start_date,
    type: 'day',
    priority: ['P0', 'P1', 'P2', 'P3'].indexOf(task.priority) + 1,
    estimated_hours: task.estimate_hours,
  }));

  // Build hierarchy
  dayNodes.forEach((day) => {
    if (!day.task_date) return;

    // Try to find matching week
    const targetWeek = weekNodes.find((w) => {
      if (!w.start_date || !w.end_date) return false;
      const wStart = startOfDay(parseISO(w.start_date));
      const wEnd = endOfDay(parseISO(w.end_date));
      const taskDate = parseISO(day.task_date!);
      return isWithinInterval(taskDate, { start: wStart, end: wEnd });
    });

    if (targetWeek) {
      targetWeek.children.push(day);
    }
  });

  return {
    title: plan.goal,
    description: plan.context,
    type: 'year',
    start_date: plan.tasks[0]?.start_date,
    end_date: plan.tasks[plan.tasks.length - 1]?.end_date,
    estimated_hours: totalHours,
    children: monthNodes.length > 0 ? monthNodes : weekNodes,
  };
}

// ==========================================
// Unified Transform Function
// ==========================================

/**
 * Type guard to check if response is V2 format
 */
const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null;

export function isV2Response(response: unknown): response is { plan: PlanSchema } {
  if (!isRecord(response) || !('plan' in response)) return false;
  const plan = response.plan;
  if (!isRecord(plan) || !('goal' in plan)) return false;
  return typeof plan.goal === 'string';
}

/**
 * Type guard to check if response is legacy format
 */
export function isLegacyResponse(response: unknown): response is LegacyDecomposeResponse {
  if (!isRecord(response)) return false;
  return 'year' in response && 'months' in response;
}

/**
 * Unified transform function that handles both V1 and V2 responses
 * This is the main export used by components
 */
export function transformToTree(data: unknown): YearNode {
  if (isV2Response(data) && data.plan) {
    return transformPlanSchemaToYearNode(data.plan);
  }

  if (isLegacyResponse(data)) {
    return transformLegacyToTree(data);
  }

  // Fallback: try to create a basic structure
  console.warn('Unknown response format, creating fallback structure');
  return {
    title: 'Unknown Task',
    type: 'year',
    children: [],
  };
}
