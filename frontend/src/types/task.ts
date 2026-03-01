// ==========================================
// Task Decomposer V2.0 Frontend Types
// Aligned with backend task_decomposer
// ==========================================

/**
 * Priority Levels (from backend)
 */
export const PriorityLevel = {
  P0: "P0", // 最高优先级
  P1: "P1", // 高优先级
  P2: "P2", // 中等优先级
  P3: "P3", // 低优先级
} as const;
export type PriorityLevel = (typeof PriorityLevel)[keyof typeof PriorityLevel];

/**
 * Risk Levels (from backend)
 */
export const RiskLevel = {
  LOW: "低",
  MEDIUM: "中",
  HIGH: "高",
} as const;
export type RiskLevel = (typeof RiskLevel)[keyof typeof RiskLevel];

/**
 * Constraint Schema
 */
export interface ConstraintSchema {
  type: string; // time, budget, tech_stack, forbidden
  description: string;
  value?: string;
}

/**
 * Open Question Schema
 */
export interface OpenQuestionSchema {
  id: string; // Q1, Q2, etc.
  question: string;
  critical: boolean;
  reason?: string;
}

/**
 * Milestone Schema
 */
export interface MilestoneSchema {
  id: string; // M1, M2, etc.
  title: string;
  description?: string;
  due?: string; // YYYY-MM-DD
  definition_of_done: string;
}

/**
 * Task Schema
 */
export interface TaskSchema {
  id: string; // T1, T2, etc.
  title: string;
  description: string;
  inputs: string[];
  outputs: string[];
  depends_on: string[];
  parent_task_id?: string | null; // 父任务ID，用于构建层级结构
  estimate_hours?: number;
  priority: PriorityLevel;
  risk: RiskLevel;
  definition_of_done: string;
  start_date?: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
  assignee?: string;
  tags: string[];
  level?: string; // 任务层级：month, week, day
}

/**
 * Plan Metadata
 */
export interface PlanMetadata {
  version: string;
  created_at: string; // ISO format
  updated_at: string; // ISO format
  model_used?: string;
  rag_enabled: boolean;
}

/**
 * Plan Schema (from backend)
 */
export interface PlanSchema {
  goal: string;
  context?: string;
  constraints: ConstraintSchema[];
  assumptions: string[];
  open_questions: OpenQuestionSchema[];
  milestones: MilestoneSchema[];
  tasks: TaskSchema[];
  time_hierarchy?: TimeHierarchy; // 嵌套的时间层级结构
  time_hierarchy_flat?: TimeHierarchyFlat; // 扁平的时间层级结构（新增）
  metadata?: PlanMetadata;
}

/**
 * 时间层级结构（嵌套格式）
 */
export interface TimeHierarchy {
  goal: string;
  start_date: string;
  end_date: string;
  granularity: TimeGranularity;
  total_days: number;
  hierarchy: TimeHierarchyNode[];
}

export interface TimeHierarchyNode {
  level: 'year' | 'quarter' | 'month' | 'week' | 'day';
  title: string;
  start_date?: string;
  end_date?: string;
  task_date?: string;
  estimated_hours?: number;
  work_day?: boolean;
  children?: TimeHierarchyNode[];
}

/**
 * 扁平时间层级结构（后端转换后）
 * 这是前端期望的格式，包含扁平的 months、weeks、days 数组
 */
export interface TimeHierarchyFlat {
  year: {
    title: string;
    description: string;
    milestones: string[];
    start_date: string;
    end_date: string;
  };
  months: Array<{
    title: string;
    description: string;
    start_date: string;
    end_date: string;
    priority: number;
  }>;
  weeks: Array<{
    title: string;
    description: string;
    start_date: string;
    end_date: string;
    priority: number;
  }>;
  days: Array<{
    title: string;
    description: string;
    task_date: string;
    estimated_hours: number;
    completed: boolean;
  }>;
}

/**
 * Evaluation Issue
 */
export interface EvaluationIssue {
  severity: string; // critical, high, medium, low
  category: string; // completeness, feasibility, consistency
  description: string;
  suggestion: string;
  affected_tasks: string[];
}

/**
 * Evaluate Output
 */
export interface EvaluateOutput {
  overall_score: number; // 0-100
  issues: EvaluationIssue[];
  passed: boolean;
  rewrite_needed: boolean;
  rewrite_reason?: string;
}

/**
 * Router Output
 */
export interface RouterOutput {
  intent: string; // clarify, decompose, rag_decompose, empathize, unknown
  confidence: number; // 0-1
  reasoning: string;
  suggested_action: string;
}

/**
 * Time Granularity Enum
 */
export type TimeGranularity = 'year' | 'quarter' | 'month' | 'week' | 'day';

/**
 * Decompose Request (to backend)
 */
export interface DecomposeRequest {
  goal: string;
  context?: string;
  constraints?: string[];
  user_id?: string;
  enable_evaluation?: boolean;
  include_trace?: boolean;

  // 新增：时间相关参数
  start_date?: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
  work_hours_per_day?: number;
  work_days_per_week?: number[]; // 0=周一, 6=周日
}

export interface DecomposeTraceEvent {
  type: string;
  ts: string;
  data?: Record<string, unknown>;
}

/**
 * Decompose Response (from backend)
 */
export interface DecomposeResponse {
  status: "need_clarification" | "completed" | "error";
  plan?: PlanSchema;
  questions?: OpenQuestionSchema[];
  session_id?: string;
  evaluation?: EvaluateOutput;
  router_result?: RouterOutput;
  error?: string;
  trace?: DecomposeTraceEvent[];
}

/**
 * Clarify Request (to backend)
 */
export interface ClarifyRequest {
  goal: string;
  context?: string;
}

/**
 * Clarify Response (from backend)
 */
export interface ClarifyResponse {
  questions: OpenQuestionSchema[];
  reasoning: string;
  priority: string[];
}

// ==========================================
// Legacy Types (for backward compatibility)
// ==========================================

export interface GoalContext {
  long_term_goal?: string;
  completion_criteria?: string;
  deadline_type?: string;
  scope_boundaries?: string;
}

export interface CurrentContext {
  current_progress?: string;
  existing_resources?: string;
}

export interface TimeContext {
  weekly_hours?: number;
  available_slots?: string;
  min_viable_effort?: string;
}

export interface PriorityContext {
  trade_off?: string;
  task_density?: string;
}

export interface EnvironmentContext {
  environment?: string;
  aversion?: string;
}

export interface DependencyContext {
  coordination?: string;
  resources?: string;
  risks?: string;
}

/**
 * Legacy TaskItem (for UI display)
 */
export interface TaskItem {
  title: string;
  description?: string;
  start_date?: string;
  end_date?: string;
  task_date?: string;
  priority?: number;
  milestones?: string[];
  estimated_hours?: number;
  completed?: boolean;
}

/**
 * Legacy Decompose Response format (for backward compatibility)
 */
export interface LegacyDecomposeResponse {
  year: TaskItem;
  months: TaskItem[];
  weeks: TaskItem[];
  days: TaskItem[];
}
