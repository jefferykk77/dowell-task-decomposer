import React, { useState } from 'react';
import type { DecomposeRequest } from '../types/task';
import { BrainCircuit, ListTree, Target, Hourglass, Battery, Zap, ShieldCheck, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '../utils/cn';

interface TaskFormProps {
  onSubmit: (data: DecomposeRequest) => void;
  isLoading: boolean;
}

export const TaskForm: React.FC<TaskFormProps> = ({ onSubmit, isLoading }) => {
  // Core fields (aligned with backend)
  const [goal, setGoal] = useState('');

  // Context fields
  const [context, setContext] = useState('');
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    return d.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => {
    const d = new Date();
    d.setMonth(d.getMonth() + 3);
    return d.toISOString().split('T')[0];
  });

  // Constraints
  const [budgetConstraint, setBudgetConstraint] = useState('');
  const [techStackConstraint, setTechStackConstraint] = useState('');
  const [timeConstraint, setTimeConstraint] = useState('');

  // Optional advanced fields
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [weeklyHours, setWeeklyHours] = useState(10);
  const [priority, setPriority] = useState<'quality' | 'speed' | 'balanced'>('balanced');
  const [riskTolerance, setRiskTolerance] = useState<'low' | 'medium' | 'high'>('medium');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Build constraints array
    const constraints: string[] = [];

    if (endDate) {
      constraints.push(`时间约束: 必须在 ${endDate} 前完成`);
    }

    if (startDate && endDate) {
      const totalDays = Math.ceil((new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24));
      constraints.push(`项目周期: ${startDate} 至 ${endDate}，共 ${totalDays} 天`);
    }

    if (budgetConstraint) {
      constraints.push(`预算约束: ${budgetConstraint}`);
    }

    if (techStackConstraint) {
      constraints.push(`技术栈: ${techStackConstraint}`);
    }

    if (timeConstraint) {
      constraints.push(`时间投入: ${timeConstraint}`);
    }

    if (weeklyHours) {
      constraints.push(`每周可投入: ${weeklyHours} 小时`);
    }

    if (priority === 'speed') {
      constraints.push('优先级: 速度优先');
    } else if (priority === 'quality') {
      constraints.push('优先级: 质量优先');
    }

    if (riskTolerance === 'low') {
      constraints.push('风险容忍度: 低风险偏好');
    } else if (riskTolerance === 'high') {
      constraints.push('风险容忍度: 高风险偏好');
    }

    // Build context string
    let fullContext = context;

    if (weeklyHours && !fullContext.includes('每周')) {
      fullContext += fullContext ? `\n每周可投入 ${weeklyHours} 小时` : `每周可投入 ${weeklyHours} 小时`;
    }

    onSubmit({
      goal,
      context: fullContext || undefined,
      constraints: constraints.length > 0 ? constraints : undefined,
      enable_evaluation: true,
      start_date: startDate,
      end_date: endDate,
      work_hours_per_day: Math.round((weeklyHours / 5) * 10) / 10, // 假设每周5天工作日
      work_days_per_week: [0, 1, 2, 3, 4], // 周一到周五
    });
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-8 py-6 border-b border-gray-100">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <ListTree className="w-6 h-6 text-indigo-600" />
          AI 智能任务拆解 V2.0
        </h2>
        <p className="text-gray-500 mt-2 text-sm">
          基于新的 LangChain 架构，提供更强大的任务规划和质量评估
        </p>
      </div>

      <form onSubmit={handleSubmit} className="p-8 space-y-10">
        {/* Section 1: Goal */}
        <section className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 border-b pb-2">
            <Target className="w-5 h-5 text-blue-500" />
            核心目标
          </h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              您的目标 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              required
              placeholder="例如：开发一个待办事项小程序、通过CPA考试、体重减到60kg"
              className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-blue-100 outline-none transition-all"
              rows={3}
            />
          </div>
        </section>

        {/* Section 2: Context */}
        <section className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 border-b pb-2">
            <Battery className="w-5 h-5 text-green-500" />
            背景信息
          </h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              详细描述（可选）
            </label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="提供更多背景信息，如：当前进度、已有资源、使用场景等..."
              className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-green-100 outline-none transition-all"
              rows={4}
            />
          </div>
        </section>

        {/* Section 3: Basic Constraints */}
        <section className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 border-b pb-2">
            <Hourglass className="w-5 h-5 text-orange-500" />
            基本约束
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                开始日期 <span className="text-red-500">*</span>
              </label>
              <input
                aria-label="开始日期"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-orange-100 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                结束日期 <span className="text-red-500">*</span>
              </label>
              <input
                aria-label="结束日期"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
                min={startDate || new Date().toISOString().split('T')[0]}
                className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-orange-100 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                预算约束（可选）
              </label>
              <input
                type="text"
                value={budgetConstraint}
                onChange={(e) => setBudgetConstraint(e.target.value)}
                placeholder="例如：预算有限、使用开源方案"
                className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-orange-100 outline-none transition-all"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                技术栈/工具（可选）
              </label>
              <input
                type="text"
                value={techStackConstraint}
                onChange={(e) => setTechStackConstraint(e.target.value)}
                placeholder="例如：React + TypeScript、Python Flask、微信小程序"
                className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-orange-100 outline-none transition-all"
              />
            </div>
          </div>
        </section>

        {/* Advanced Options Toggle */}
        <div className="pt-2">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-gray-700 transition-colors"
          >
            {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            {showAdvanced ? '收起高级选项' : '展开高级选项'}
          </button>
        </div>

        {/* Collapsible Advanced Section */}
        {showAdvanced && (
          <div className="space-y-10 animate-in slide-in-from-top-4 fade-in duration-300">
            {/* Section 4: Priority & Risk */}
            <section className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 border-b pb-2">
                <Zap className="w-5 h-5 text-purple-500" />
                优先级与风险
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    更看重什么
                  </label>
                  <div className="flex bg-gray-50 p-1 rounded-lg border border-gray-200">
                    {[
                      { value: 'speed', label: '速度' },
                      { value: 'balanced', label: '平衡' },
                      { value: 'quality', label: '质量' },
                    ].map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => setPriority(opt.value as typeof priority)}
                        className={cn(
                          'flex-1 py-2 rounded-md text-sm font-medium transition-all capitalize',
                          priority === opt.value
                            ? 'bg-white text-purple-600 shadow-sm border border-gray-100'
                            : 'text-gray-500 hover:text-gray-700'
                        )}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    风险容忍度
                  </label>
                  <div className="flex bg-gray-50 p-1 rounded-lg border border-gray-200">
                    {[
                      { value: 'low', label: '低' },
                      { value: 'medium', label: '中' },
                      { value: 'high', label: '高' },
                    ].map((opt) => (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => setRiskTolerance(opt.value as typeof riskTolerance)}
                        className={cn(
                          'flex-1 py-2 rounded-md text-sm font-medium transition-all capitalize',
                          riskTolerance === opt.value
                            ? 'bg-white text-purple-600 shadow-sm border border-gray-100'
                            : 'text-gray-500 hover:text-gray-700'
                        )}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            {/* Section 5: Time & Environment */}
            <section className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 border-b pb-2">
                <ShieldCheck className="w-5 h-5 text-teal-500" />
                时间与环境
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    每周可投入（小时）
                  </label>
                  <input
                    aria-label="每周可投入总时长"
                    type="number"
                    value={weeklyHours}
                    onChange={(e) => setWeeklyHours(Number(e.target.value))}
                    min={1}
                    className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-teal-100 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    时间投入描述
                  </label>
                  <input
                    type="text"
                    value={timeConstraint}
                    onChange={(e) => setTimeConstraint(e.target.value)}
                    placeholder="例如：工作日晚上、周末整块时间"
                    className="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-teal-100 outline-none transition-all"
                  />
                </div>
              </div>
            </section>
          </div>
        )}

        <div className="pt-6">
          <button
            type="submit"
            disabled={isLoading}
            className={cn(
              'w-full py-4 rounded-xl font-bold text-white text-lg shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 transform active:scale-[0.99]',
              'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700',
              isLoading && 'opacity-70 cursor-not-allowed'
            )}
          >
            {isLoading ? (
              <>
                <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
                正在智能生成计划...
              </>
            ) : (
              <>
                <BrainCircuit className="w-6 h-6" />
                开始 AI 拆解
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
