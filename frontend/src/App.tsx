import { useRef, useState } from 'react';
import { TaskForm } from './components/TaskForm';
import { YearView } from './components/YearView';
import GanttView from './components/GanttView';
import { taskApi } from './api/task';
import { transformToTree, type YearNode } from './utils/transformer';
import type { DecomposeRequest, DecomposeResponse, DecomposeTraceEvent, EvaluateOutput } from './types/task';
import { LayoutDashboard, BarChart, CheckCircle2, AlertCircle, Activity, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import type { Task } from 'gantt-task-react';

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<YearNode | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'card' | 'gantt'>('card');
  const [aiTip, setAiTip] = useState<{ message: string; level: string } | null>(null);
  const [traceEvents, setTraceEvents] = useState<DecomposeTraceEvent[]>([]);
  const [traceOpen, setTraceOpen] = useState(true);
  const abortRef = useRef<AbortController | null>(null);

  // Store the raw response for evaluation display
  const [evaluationData, setEvaluationData] = useState<EvaluateOutput | null>(null);

  const handleDecompose = async (data: DecomposeRequest) => {
    setLoading(true);
    setError(null);
    setAiTip(null);
    setEvaluationData(null);
    setTraceEvents([]);
    setTraceOpen(true);
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      const applyResponse = (response: DecomposeResponse) => {
        if (response.status === 'need_clarification') {
          setError('需要更多信息: ' + (response.questions?.map((q) => q.question).join(', ') || ''));
          return;
        }

        if (response.status === 'error') {
          setError(response.error || '任务拆解失败');
          return;
        }

        if (response.status === 'completed' && response.plan) {
          const tree = transformToTree(response);
          setResult(tree);

          if (response.evaluation) {
            setEvaluationData(response.evaluation);

            if (response.evaluation.overall_score < 80) {
              setAiTip({
                message: `计划质量评分: ${response.evaluation.overall_score}/100。${response.evaluation.issues.length > 0 ? response.evaluation.issues[0].suggestion : ''}`,
                level: response.evaluation.overall_score < 60 ? 'critical' : 'medium',
              });
            } else if (response.evaluation.overall_score >= 90) {
              setAiTip({
                message: `计划质量优秀！评分: ${response.evaluation.overall_score}/100`,
                level: 'low',
              });
            }
          }

          if (response.router_result) {
            console.log('Router intent:', response.router_result.intent);
          }
        }
      };

      const res = await fetch('http://localhost:8000/api/v2/decompose/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        signal: abortRef.current.signal,
      });

      if (!res.ok || !res.body) {
        const fallback = await taskApi.decompose({ ...data, include_trace: true });
        if (fallback.trace) setTraceEvents(fallback.trace);
        applyResponse(fallback);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null;
      const isDecomposeResponse = (v: unknown): v is DecomposeResponse => isRecord(v) && typeof v.status === 'string';

      const pushEvent = (evt: DecomposeTraceEvent) => {
        setTraceEvents((prev) => [...prev, evt]);
      };

      const flushBuffer = (force: boolean) => {
        const parts = buffer.split('\n\n');
        if (!force) buffer = parts.pop() ?? '';
        for (const chunk of parts) {
          const lines = chunk.split('\n').filter(Boolean);
          const dataLines: string[] = [];
          for (const line of lines) {
            if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
          }
          const dataStr = dataLines.join('\n').trim();
          if (!dataStr) continue;
          let parsed: unknown;
          try {
            parsed = JSON.parse(dataStr);
          } catch {
            continue;
          }
          if (!isRecord(parsed) || typeof parsed.type !== 'string') continue;
          const evt: DecomposeTraceEvent = {
            type: parsed.type,
            ts: typeof parsed.ts === 'string' ? parsed.ts : new Date().toISOString(),
            data: isRecord(parsed.data) ? parsed.data : undefined,
          };
          pushEvent(evt);

          if (evt.type === 'result' && isDecomposeResponse(parsed.data)) applyResponse(parsed.data);
          if (evt.type === 'error') {
            const errPayload = isRecord(parsed.data) ? parsed.data : undefined;
            const errMsg = typeof errPayload?.error === 'string' ? errPayload.error : '任务拆解失败';
            setError(errMsg);
          }
        }
      };

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        flushBuffer(false);
      }
      flushBuffer(true);
    } catch (err) {
      console.error(err);
      if (err instanceof DOMException && err.name === 'AbortError') return;
      setError(err instanceof Error ? err.message : '任务拆解失败，请检查网络或稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleGanttTaskChange = async (task: Task, _changeType: 'move' | 'resize') => {
    // 1. 查找原始任务和父任务 (这里需要从 Task ID 解析或遍历树)
    // 简化起见，我们假设 year 是 parent，因为 GanttView 里我们把 project 设为了 parent

    // 真实场景：需要从 result 树中找到 task 对应的节点和它的 parent
    // 注意：GanttView 里 ID 格式是 day-mIdx-wIdx-dIdx

    console.log('Task Changed:', task);
    console.log('Change Type:', _changeType);

    // 调用后端评估
    try {
      // Note: This endpoint needs to be implemented in backend
      // For now, we'll skip the actual call
      // const assessment = await assessImpact({
      //   original_task: { ... },
      //   updated_task: { ... },
      //   parent_task: { ... },
      //   change_type: _changeType,
      // });

      // Mock assessment for demo
      const assessment = {
        impact_level: 'low',
        suggestion: '任务调整在合理范围内',
      };

      if (assessment.impact_level !== 'none') {
        setAiTip({
          message: `AI 提示: ${assessment.suggestion}`,
          level: assessment.impact_level,
        });
        // 8秒后自动消失
        setTimeout(() => setAiTip(null), 8000);
      }
    } catch (e) {
      console.error('Failed to assess impact', e);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20 relative">
      {/* AI Tip Toast */}
      {aiTip && (
        <div
          className={`fixed top-20 right-4 z-50 p-4 rounded-lg shadow-xl max-w-sm animate-in fade-in slide-in-from-top-4 ${
            aiTip.level === 'critical' || aiTip.level === 'high'
              ? 'bg-red-100 text-red-800 border-red-300 border'
              : aiTip.level === 'medium'
              ? 'bg-yellow-100 text-yellow-800 border-yellow-300 border'
              : 'bg-blue-100 text-blue-800 border-blue-300 border'
          }`}
        >
          <div className="flex items-start gap-2">
            {aiTip.level === 'low' ? (
              <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <div className="font-bold mb-1">{aiTip.level === 'low' ? '成功' : 'AI 评估'}</div>
              <div>{aiTip.message}</div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-blue-600 p-2 rounded-lg">
              <LayoutDashboard className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900 tracking-tight">AI 任务拆解器</h1>
              <p className="text-xs text-gray-500">V2.0 - LangChain 架构</p>
            </div>
          </div>

          {/* View Switcher */}
          {result && (
            <div className="flex bg-gray-100 p-1 rounded-lg">
              <button
                type="button"
                onClick={() => setViewMode('card')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'card'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                卡片视图
              </button>
              <button
                type="button"
                onClick={() => setViewMode('gantt')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'gantt'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                <BarChart className="w-4 h-4 rotate-90" />
                甘特/排期视图
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
        {/* Input Section */}
        <section className={result ? '' : 'min-h-[80vh] flex flex-col justify-center'}>
          {!result && (
            <div className="text-center mb-10">
              <h2 className="text-3xl font-extrabold text-gray-900 mb-4">
                {result ? '任务拆解结果' : '从年度目标开始'}
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                {result
                  ? 'AI 已为您规划好完整的执行链路，请查看详情'
                  : '输入您的核心目标，AI 将基于 LangChain 架构为您生成结构化任务计划'}
              </p>
            </div>
          )}

          <TaskForm onSubmit={handleDecompose} isLoading={loading} />

          {(loading || traceEvents.length > 0) && (
            <div className="mt-6 max-w-4xl mx-auto bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-5 h-5 text-indigo-600" />
                  <div className="font-semibold text-gray-800">拆解过程</div>
                  <div className="text-xs text-gray-500">{traceEvents.length} 条</div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setTraceOpen((v) => !v)}
                    className="px-2 py-1 text-sm text-gray-600 hover:text-gray-900"
                  >
                    {traceOpen ? (
                      <span className="inline-flex items-center gap-1">
                        <ChevronUp className="w-4 h-4" />收起
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1">
                        <ChevronDown className="w-4 h-4" />展开
                      </span>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => setTraceEvents([])}
                    className="inline-flex items-center gap-1 px-2 py-1 text-sm text-gray-600 hover:text-gray-900"
                  >
                    <Trash2 className="w-4 h-4" />
                    清空
                  </button>
                </div>
              </div>
              {traceOpen && (
                <div className="max-h-[420px] overflow-auto px-6 py-4 space-y-3">
                  {traceEvents.map((evt, idx) => {
                    const labelMap: Record<string, string> = {
                      start: '开始',
                      session: '会话创建',
                      router_start: '路由判断',
                      router_prompt_ready: '路由提示词就绪',
                      router_raw_response: '路由响应',
                      router_output: '路由输出',
                      router_result: '路由结果',
                      clarify_start: '生成澄清问题',
                      clarify_prompt_ready: '澄清提示词就绪',
                      clarify_raw_response: '澄清响应',
                      clarify_output: '澄清输出',
                      clarify_result: '澄清结果',
                      decompose_start: '开始拆解',
                      decompose_prompt_ready: '拆解提示词就绪',
                      decompose_raw_response: '拆解响应',
                      decompose_parsed: '拆解解析',
                      decompose_output: '拆解输出',
                      decompose_result: '拆解完成',
                      evaluate_start: '质量评估',
                      evaluate_prompt_ready: '评估提示词就绪',
                      evaluate_raw_response: '评估响应',
                      evaluate_output: '评估输出',
                      evaluate_result: '评估结果',
                      completed: '完成',
                      result: '返回结果',
                      error: '错误',
                    };

                    const title = labelMap[evt.type] || evt.type;
                    const preview = typeof evt.data?.preview === 'string' ? evt.data.preview : '';
                    const val = (v: unknown) =>
                      typeof v === 'string' || typeof v === 'number' ? String(v) : '-';
                    const hint =
                      evt.type === 'decompose_parsed' || evt.type === 'decompose_output' || evt.type === 'decompose_result'
                        ? `任务数: ${val(evt.data?.tasks)} / 里程碑: ${val(evt.data?.milestones)}`
                        : evt.type === 'evaluate_output' || evt.type === 'evaluate_result'
                        ? `评分: ${val(evt.data?.overall_score)}`
                        : '';

                    return (
                      <div key={`${evt.ts}-${idx}`} className="border border-gray-100 rounded-lg p-3 bg-gray-50">
                        <div className="flex items-start justify-between gap-3">
                          <div className="font-medium text-gray-800">{title}</div>
                          <div className="text-xs text-gray-500 shrink-0">{evt.ts}</div>
                        </div>
                        {(hint || preview) && (
                          <div className="mt-2 text-sm text-gray-700 space-y-2">
                            {hint && <div className="text-gray-600">{hint}</div>}
                            {preview && (
                              <pre className="text-xs bg-white border border-gray-200 rounded p-2 overflow-auto whitespace-pre-wrap">
                                {preview}
                              </pre>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {loading && (
                    <div className="text-sm text-gray-500">
                      正在生成中…过程会实时更新。
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="mt-6 p-4 bg-red-50 text-red-700 rounded-lg text-center max-w-2xl mx-auto border border-red-100">
              {error}
            </div>
          )}
        </section>

        {/* Evaluation Score Display */}
        {evaluationData && result && (
          <section className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
              计划质量评估
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500 mb-1">总体评分</div>
                <div className="text-2xl font-bold text-gray-900">
                  {evaluationData.overall_score}/100
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500 mb-1">问题数量</div>
                <div className="text-2xl font-bold text-gray-900">
                  {evaluationData.issues?.length || 0}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500 mb-1">状态</div>
                <div className="text-2xl font-bold text-gray-900">
                  {evaluationData.passed ? '✓ 通过' : '✗ 需改进'}
                </div>
              </div>
            </div>
            {evaluationData.issues && evaluationData.issues.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">改进建议：</h4>
                <ul className="space-y-2">
                  {evaluationData.issues.slice(0, 3).map((issue, idx: number) => (
                    <li key={idx} className="text-sm text-gray-600 bg-yellow-50 p-2 rounded">
                      <span className="font-medium">{issue.category}:</span> {issue.suggestion}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}

        {/* Result Section */}
        {result && (
          <section className="scroll-mt-24" id="result-view">
            {viewMode === 'card' ? <YearView data={result} /> : <GanttView data={result} onTaskChange={handleGanttTaskChange} />}

            <div className="mt-12 text-center">
              <button
                type="button"
                onClick={() => {
                  setResult(null);
                  setEvaluationData(null);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
                className="text-gray-500 hover:text-gray-900 underline underline-offset-4"
              >
                创建新任务
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
